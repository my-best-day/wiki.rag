import logging
import numpy as np
from typing import Optional
from numpy.typing import NDArray

__import__("gen.encoder_helper")

logger = logging.getLogger(__name__)

encoder_configs = {
    # max-token * raw2cln * tok2char * char2byte -> max-byte
    # 8192 tokens -> 256 * 1.05 * 3.9 * 1.05 ~> 35223
    "big": {"model_id": "nomic-ai/nomic-embed-text-v1.5", "max_len": 8192},

    # max-token * raw2cln * tok2char * char2byte -> max-byte
    # 256 tokens -> 256 * 1.05 * 3.9 * 1.05 -> 1100
    "small": {"model_id": "all-MiniLM-L6-v2", "max_len": 256}
}


class Encoder:
    def __init__(
            self,
            batch_size: int,
            target_dim: Optional[int] = None,
            l2_normalize: bool = True,
            config_id: str = "big"):

        self.config = encoder_configs[config_id]
        self.batch_size = batch_size
        self.target_dim = target_dim
        self.l2_normalize = l2_normalize
        self._model = None

    def encode(self, sentences):
        query_embedding = self.model.encode(sentences, batch_size=self.batch_size)
        query_embedding = self.reduce_dim_and_normalize_embedding(query_embedding)
        return query_embedding

    def reduce_dim_and_normalize_embedding(self, embedding):
        """Reduce dimension and normalize the embedding."""
        reduced_embedding = self.reduce_dim(embedding, self.target_dim)
        normalized_embedding = self.normalize_embedding(reduced_embedding, self.l2_normalize)
        return normalized_embedding

    @staticmethod
    def reduce_dim(embedding: NDArray, target_dim: Optional[int]) -> NDArray:
        """Reduce the embedding dimension if necessary."""
        current_dim = embedding.shape[1]

        if target_dim is not None:
            if current_dim < target_dim:
                raise ValueError(f"Target dim {target_dim} exceeds input dim {current_dim}")

            if current_dim > target_dim:
                # layer normalization
                mean = np.mean(embedding, axis=1, keepdims=True)
                std = np.std(embedding, axis=1, keepdims=True)
                normalized_embedding = (embedding - mean) / (std + 1e-6)  # avoid division by zero
                # reduce dimension
                reduced_embedding = normalized_embedding[:, :target_dim]
            else:
                reduced_embedding = embedding
        else:
            reduced_embedding = embedding

        return reduced_embedding

    @staticmethod
    def normalize_embedding(embedding: NDArray, l2_normalize: bool) -> NDArray:
        """Normalize the embedding using L2 normalization if specified."""
        if l2_normalize:
            normalized_embedding = embedding / \
                np.linalg.norm(embedding, axis=1, keepdims=True)
        else:
            normalized_embedding = embedding

        return normalized_embedding

    @property
    def model(self):
        if self._model is None:
            self._model = self.get_model()
        return self._model

    def get_model(self):
        model_id = self.config["model_id"]
        model = self._get_model(model_id)
        return model

    def _get_model(self, model_id):
        from sentence_transformers import SentenceTransformer
        device = self.get_device()
        model = SentenceTransformer(
            model_name_or_path=model_id,
            device=device,
            trust_remote_code=True,
        )
        return model

    @staticmethod
    def get_device():
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return device

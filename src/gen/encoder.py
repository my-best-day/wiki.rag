"""
Encoder class for encoding sentences.
Abstracts working with SentenceTransformer.
"""
import logging
from typing import List
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
    """
    Encoder class for encoding sentences.
    Abstracts working with SentenceTransformer.
    """
    def __init__(
            self,
            batch_size: int,
            config_id: str = "big"):

        self.encoder_config = encoder_configs[config_id]
        self.batch_size: int = batch_size
        self._model = None

    def encode(self, sentences: List[str]) -> NDArray:
        """Encode sentences into embeddings."""
        query_embedding = self.model.encode(sentences, batch_size=self.batch_size)
        return query_embedding

    @property
    def model(self):
        """Get and memoize the model."""
        if self._model is None:
            self._model = self.get_model()
        return self._model

    def get_model(self):
        """Get the SentenceTransformer model by model_id."""
        model_id = self.encoder_config["model_id"]
        model = self._get_model(model_id)
        return model

    def _get_model(self, model_id: str):
        """Get the SentenceTransformer model by model_id."""
        # delay the import to speed up startup time
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
        """Get the PyTorch device cuda/cpu."""
        # delay the import to speed up startup time
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return device

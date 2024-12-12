import numpy as np
from typing import Optional, Literal
from numpy.typing import NDArray

TargetStype = Optional[Literal["float32", "float16", "int8", "uint8"]]


class EmbeddingUtils:

    @staticmethod
    def reduce_dim_and_normalize_embedding(
            embedding: NDArray,
            target_dim: Optional[int],
            l2_normalize: bool,
            target_stype: TargetStype) -> NDArray:
        """Reduce dimension and normalize the embedding."""

        reduced_embedding = EmbeddingUtils.reduce_dim(embedding, target_dim)

        normalized_embedding = EmbeddingUtils.normalize_embedding(reduced_embedding, l2_normalize)

        quantized_embedding = EmbeddingUtils.quantize_embedding(
            normalized_embedding, target_stype, l2_normalize)

        return quantized_embedding

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
                normalized_embedding = (embedding - mean) / (std + 1e-5)  # avoid division by zero
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

    @staticmethod
    def quantize_embedding(embedding: NDArray, stype: TargetStype,
                           is_embedding_l2_normalize: bool) -> NDArray:
        """Quantize the embedding to the specified type."""
        if stype is None:
            return embedding

        assert stype in ["float32", "float16", "int8", "uint8"]
        assert is_embedding_l2_normalize, "Quantization only supported for L2 normalized embeddings"
        if stype == "float32":
            quantized = embedding.astype(np.float32)
        elif stype == "float16":
            quantized = embedding.astype(np.float16)
        elif stype == "int8":
            quantized = np.round(embedding * 127).astype(np.int8)
        elif stype == "uint8":
            quantized = np.round((embedding + 1) * 127.5).astype(np.uint8)
        else:
            raise ValueError(f"Unknown stype: {stype}")
        return quantized

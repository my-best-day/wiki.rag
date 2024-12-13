import numpy as np
from typing import Optional, Literal
from numpy.typing import NDArray

TargetStype = Optional[Literal["float32", "float16", "int8", "uint8"]]


class EmbeddingUtils:

    @staticmethod
    def morph_embeddings(
            embeddings: NDArray,
            target_dim: Optional[int],
            l2_normalize: bool,
            target_stype: TargetStype) -> NDArray:
        """Reduce dimension, normalize, and quantize the embeddings."""

        reduced_embeddings = EmbeddingUtils.reduce_dim(embeddings, target_dim)

        normalized_embeddings = EmbeddingUtils.normalize_embedding(reduced_embeddings, l2_normalize)

        quantized_embeddings = EmbeddingUtils.quantize_embedding(
            normalized_embeddings, target_stype, l2_normalize)

        return quantized_embeddings

    @staticmethod
    def reduce_dim(embeddings: NDArray, target_dim: Optional[int]) -> NDArray:
        """Reduce the embeddings dimension if necessary."""
        current_dim = embeddings.shape[1]

        if target_dim is not None:
            if current_dim < target_dim:
                raise ValueError(f"Target dim {target_dim} exceeds input dim {current_dim}")

            if current_dim > target_dim:
                # layer normalization
                mean = np.mean(embeddings, axis=1, keepdims=True)
                std = np.std(embeddings, axis=1, keepdims=True)
                normalized_embedding = (embeddings - mean) / (std + 1e-5)  # avoid division by zero
                # reduce dimension
                reduced_embedding = normalized_embedding[:, :target_dim]
            else:
                reduced_embedding = embeddings
        else:
            reduced_embedding = embeddings

        return reduced_embedding

    @staticmethod
    def normalize_embedding(embeddings: NDArray, l2_normalize: bool) -> NDArray:
        """Normalize the embeddings using L2 normalization if specified."""
        if l2_normalize:
            normalized_embedding = embeddings / \
                np.linalg.norm(embeddings, axis=1, keepdims=True)
        else:
            normalized_embedding = embeddings

        return normalized_embedding

    @staticmethod
    def quantize_embedding(embeddings: NDArray, stype: TargetStype,
                           is_embedding_l2_normalize: bool) -> NDArray:
        """Quantize the embeddings to the specified type."""
        if stype is None:
            return embeddings

        assert stype in ["float32", "float16", "int8", "uint8"]
        assert is_embedding_l2_normalize, "Quantization only supported for L2 normalized embeddings"
        if stype == "float32":
            quantized = embeddings.astype(np.float32)
        elif stype == "float16":
            quantized = embeddings.astype(np.float16)
        elif stype == "int8":
            quantized = np.round(embeddings * 127).astype(np.int8)
        elif stype == "uint8":
            quantized = np.round((embeddings + 1) * 127.5).astype(np.uint8)
        else:
            raise ValueError(f"Unknown stype: {stype}")
        return quantized

    @staticmethod
    def are_l2_normalized(embeddings, tolerance=1e-6) -> bool:
        """
        Check if embeddings are L2 normalized.

        Args:
            embeddings (np.ndarray): 2D array of embeddings (batch_size x embedding_dim).
            tolerance (float): Tolerance for the L2 norm deviation from 1.

        Returns:
            bool: True if all embeddings are L2 normalized, False otherwise.
        """
        norms = np.linalg.norm(embeddings, axis=1)
        is_l2_norm = np.all(np.abs(norms - 1) < tolerance)
        return is_l2_norm

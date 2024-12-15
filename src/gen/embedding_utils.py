import logging
import numpy as np
from typing import Optional, Literal
from numpy.typing import NDArray

TargetStype = Optional[Literal["float32", "float16", "int8", "uint8"]]

logger = logging.getLogger(__name__)


class EmbeddingUtils:

    @staticmethod
    def morph_embeddings(
            embeddings: NDArray,
            target_dim: Optional[int],
            l2_normalize: bool,
            norm_type: TargetStype,
            target_stype: TargetStype) -> NDArray:
        """Reduce dimension, normalize, and quantize the embeddings."""

        embeddings1 = EmbeddingUtils.reduce_dim(embeddings, target_dim)

        embeddings2 = \
            EmbeddingUtils.normalize_embeddings(embeddings1, l2_normalize, norm_type)

        embeddings3 = EmbeddingUtils.quantize_embeddings(
            embeddings2, target_stype)

        return embeddings3

    @staticmethod
    def reduce_dim(embeddings: NDArray, target_dim: Optional[int]) -> NDArray:
        """Reduce the embeddings dimension if necessary."""
        current_dim = embeddings.shape[1]

        if target_dim is not None:
            if current_dim < target_dim:
                raise ValueError(f"Dim reduction: target {target_dim} exceeds input {current_dim}")

            if current_dim > target_dim:
                # layer normalization
                mean = np.mean(embeddings, axis=1, keepdims=True)
                std = np.std(embeddings, axis=1, keepdims=True)
                normalized_embeddings = (embeddings - mean) / (std + 1e-5)  # avoid division by zero
                # reduce dimension
                reduced_embeddings = normalized_embeddings[:, :target_dim]
            else:
                reduced_embeddings = embeddings
        else:
            reduced_embeddings = embeddings

        if reduced_embeddings is embeddings:
            logger.info("Dim reduction: NOT applied (dim: %s)", current_dim)
        else:
            logger.info("Dim reduction: applied from %s to %s", current_dim, target_dim)

        return reduced_embeddings

    @staticmethod
    def normalize_embeddings(embeddings: NDArray, l2_normalize: bool,
                             astype: TargetStype = None) -> NDArray:
        """Normalize the embeddings using L2 normalization if specified."""
        if l2_normalize:
            if astype is not None:
                embeddings1 = embeddings.astype(astype) if astype is not None else embeddings
            normalized_embeddings = embeddings1 / \
                np.linalg.norm(embeddings1, axis=1, keepdims=True)
            result = normalized_embeddings
            logger.info("L2 normalization: applied")
        else:
            result = embeddings
            logger.info("L2 normalization: NOT applied")

        return result

    @staticmethod
    def quantize_embeddings(embeddings: NDArray, stype: TargetStype) -> NDArray:
        """Quantize the embeddings to the specified type."""
        if stype is None:
            logger.info("Quantization: non requested")
            return embeddings

        current_stype = EmbeddingUtils.get_stype(embeddings)
        if current_stype == stype:
            logger.info("Quantization: already of type %s", stype)
            return embeddings

        assert stype in ["float32", "float16", "int8", "uint8"]

        if not EmbeddingUtils.are_l2_normalized(embeddings):
            raise ValueError("Quantization only supported for L2 normalized embeddings")

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
        logger.info("Quantization: converted from %s to %s", current_stype, stype)

        return quantized

    @staticmethod
    def get_stype(embeddings: NDArray) -> str:
        """Determine the stype of the current embeddings."""
        dtype = embeddings.dtype
        if dtype == np.float32:
            stype = "float32"
        elif dtype == np.float16:
            stype = "float16"
        elif dtype == np.int8:
            stype = "int8"
        elif dtype == np.uint8:
            stype = "uint8"
        else:
            raise ValueError(f"Unknown dtype: {dtype}")
        return stype

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

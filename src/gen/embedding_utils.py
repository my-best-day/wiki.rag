import logging
import numpy as np
from typing import Optional, Literal
from numpy.typing import NDArray
from xutils.embedding_config import EmbeddingConfig
from xutils.timer import LoggingTimer, log_timeit

TargetStype = Optional[Literal["float32", "float16", "int8", "uint8"]]

logger = logging.getLogger(__name__)


class EmbeddingUtils:

    @log_timeit(logger=logger)
    @staticmethod
    def morph_embeddings(
            embeddings: NDArray,
            embed_config: EmbeddingConfig) -> NDArray:
        """Reduce dimension, normalize, and quantize the embeddings."""

        reduced_embeddings = EmbeddingUtils.reduce_dim(embeddings, embed_config.dim)
        timer = LoggingTimer(logger=logger)
        timer.restart("Reduced dimension")

        normalized_embeddings = EmbeddingUtils.normalize_embeddings(
            reduced_embeddings, embed_config.l2_normalize, embed_config.norm_type)
        timer.restart("Normalized embeddings")

        quantized_embeddings = EmbeddingUtils.quantize_embeddings(
            normalized_embeddings, embed_config.stype)
        timer.restart("Quantized embeddings")

        result = quantized_embeddings
        return result

    @log_timeit(logger=logger)
    @staticmethod
    def reduce_dim(embeddings: NDArray, target_dim: Optional[int]) -> NDArray:
        """Reduce the embeddings dimension if necessary."""
        current_dim = embeddings.shape[1]

        if target_dim is not None:
            if current_dim < target_dim:
                raise ValueError(f"Dim reduction: target {target_dim} exceeds input {current_dim}")

            elif current_dim > target_dim:
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

        result = reduced_embeddings
        return result

    @log_timeit(logger=logger)
    @staticmethod
    def normalize_embeddings(embeddings: NDArray, l2_normalize: bool,
                             astype: TargetStype = None) -> NDArray:
        """Normalize the embeddings using L2 normalization if specified."""

        if l2_normalize:
            embeddings_casted = embeddings.astype(astype) if astype is not None else embeddings
            timer = LoggingTimer(logger=logger)
            timer.restart("Casted embeddings")
            normalized_embeddings = embeddings_casted / np.linalg.norm(
                embeddings_casted, axis=1, keepdims=True)
            timer.restart("Normalized embeddings")
            logger.info("L2 normalization: applied")
            result = normalized_embeddings
        else:
            logger.info("L2 normalization: NOT applied")
            result = embeddings

        return result

    @log_timeit(logger=logger)
    @staticmethod
    def quantize_embeddings(embeddings: NDArray, stype: TargetStype) -> NDArray:
        """Quantize the embeddings to the specified type."""

        if stype is None:
            logger.info("Quantization: not requested")
            result = embeddings
        else:
            current_stype = EmbeddingUtils.get_stype(embeddings)
            if current_stype == stype:
                logger.info("Quantization: already of type %s", stype)
                result = embeddings
            else:
                if not EmbeddingUtils.are_l2_normalized(embeddings):
                    raise ValueError("Quantization only supported for L2 normalized embeddings")

                if stype == "float32":
                    quantized_embeddings = embeddings.astype(np.float32)
                elif stype == "float16":
                    quantized_embeddings = embeddings.astype(np.float16)
                elif stype == "int8":
                    quantized_embeddings = np.round(embeddings * 127).astype(np.int8)
                elif stype == "uint8":
                    quantized_embeddings = np.round((embeddings + 1) * 127.5).astype(np.uint8)
                else:
                    raise ValueError(f"Unknown stype: {stype}")

                logger.info("Quantization: converted from %s to %s", current_stype, stype)
                result = quantized_embeddings

        return result

    @log_timeit(logger=logger)
    @staticmethod
    def get_stype(embeddings: NDArray) -> str:
        """Determine the stype of the current embeddings."""
        dtype = embeddings.dtype
        if dtype == np.float64:
            stype = "float64"
        elif dtype == np.float32:
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

    @log_timeit(logger=logger)
    @staticmethod
    def are_l2_normalized(embeddings, tolerance=1e-6) -> bool:
        """Check if embeddings are L2 normalized."""

        norms = np.linalg.norm(embeddings, axis=1)
        result = np.all(np.abs(norms - 1) < tolerance)
        return result

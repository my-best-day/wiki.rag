import os
import logging
import numpy as np
from uuid import UUID
from pathlib import Path
from filelock import FileLock
from typing import List, Tuple
from numpy.typing import NDArray
from xutils.embedding_config import EmbeddingConfig

logger = logging.getLogger(__name__)


EMPTY_RESULT = (
    np.empty((0,), dtype=str),
    np.empty((0, 0), dtype=float),
)


class CleanFileLock(FileLock):
    """
    A file lock that cleans up the lock file after releasing the lock.
    """
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Call the original __exit__ to release the lock
        super().__exit__(exc_type, exc_val, exc_tb)

        # Clean up the lock file after releasing the lock
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)


class EmbeddingStore:
    """
    Simple incremental store for embeddings.
    """

    # Indirection allows easier substitution for testing purposes
    file_lock_class = CleanFileLock

    def __init__(self, path, allow_empty: bool):
        logger.info(f"EmbeddingStore: {path}")
        self.path = Path(path)
        self.allow_empty = allow_empty
        logger.debug("EmbeddingStore(path=%s, allow_empty=%s)", path, allow_empty)

        if not self.does_store_exist():
            if not allow_empty:
                raise RuntimeError(f"Embedding store {path} does not exist")

    @property
    def lock_path(self):
        return self.path.with_suffix(".lock")

    def extend_embeddings(self, uids: List[UUID], embeddings: np.ndarray) -> None:
        """
        Add embeddings to the store.
        Args:
            uids: List of UUIDs
            embeddings: List of embeddings (the output of a sentence_transformer.encode())
        """
        str_uids = [str(uid) for uid in uids]
        lock_path = self.lock_path
        with self.file_lock_class(lock_path):
            self._add_embeddings(str_uids, embeddings)

    def _add_embeddings(self, add_uids: List[str], add_embeds: np.ndarray):
        """
        Add embeddings to the store.
        :param add_embedding_list: List of tuples (segment_id, embedding)
        """
        if len(add_uids) == 0:
            return
        np_str_uids, np_embeds = self._load_embeddings(allow_empty=True)
        np_str_uids = np.concatenate((np_str_uids, add_uids)) if len(np_str_uids) else add_uids
        np_embeds = np.concatenate((np_embeds, add_embeds)) if len(np_embeds) else add_embeds
        np.savez(self.path, uids=np_str_uids, embeddings=np_embeds)

    def get_count(self, allow_empty: bool = False) -> int:
        """
        Get the number of embeddings in the store.
        :return: Number of embeddings in the store.
        """
        lock_path = self.lock_path
        with self.file_lock_class(lock_path):
            np_str_uids, _ = self._load_embeddings(allow_empty=allow_empty)
            count = len(np_str_uids)
        return count

    def load_embeddings(self, allow_empty: bool = False) -> Tuple[List[UUID], List[np.ndarray]]:
        """
        Load embeddings from the store.
        Do type conversion and handle locks here.
        :return: an array of uids: List[UUID] and an array of embeddings: List[np.ndarray]
        """
        lock_path = self.lock_path
        with self.file_lock_class(lock_path):
            np_str_uids, np_embeddings = self._load_embeddings(allow_empty=allow_empty)
            np_uids = np.vectorize(UUID)(np_str_uids)
            logger.debug("EmbeddingStore: %d embeddings loaded", len(np_uids))
            return np_uids, np_embeddings

    def _load_embeddings(self, allow_empty: bool) -> Tuple[NDArray[str], np.ndarray]:
        """
        Load embeddings from the store.
        - It is the caller responsibility to very the file exists and handle
          locks.
        - this method returns a tuple of ndarrays.
        :return: an ndarray of uids: NDArray[UUID] and an ndarray of embeddings: NDArray[np.ndarray]
        """
        if not self.does_store_exist():
            if allow_empty:
                return np.array([]), np.array([])
            else:
                raise FileNotFoundError(f"Embeddings store {self.path} does not exist")
        else:
            with np.load(self.path) as data:
                np_str_uids = data["uids"]
                np_embeddings = data["embeddings"]

        logger.info(f"EmbeddingStore: {len(np_str_uids)} embeddings loaded")
        return np_str_uids, np_embeddings

    # for testing purposes we move file.path.exists here
    def does_store_exist(self) -> bool:
        """Check if the store exists."""
        return self.path.exists()

    @staticmethod
    def get_store_path(config: EmbeddingConfig) -> str:
        """
        Generate a path based on the embedding configuration
        Args:
            config: EmbeddingConfig instance containing prefix, max_len, dim, stype, and norm_type
        """
        dim_part = f"_{config.dim}" if config.dim is not None else ""
        type_part = f"_{config.stype}" if config.stype != "float32" else ""

        # only load the pre-normalized embeddings if we are not asked to normalize
        should_load_normalized = not config.l2_normalize and config.norm_type
        norm_part = f"_{config.norm_type}" if should_load_normalized else ""

        logger.debug("EmbeddingStore: dim_part: %s, type_part: %s, norm_part: %s",
                     dim_part, type_part, norm_part)

        path = f"{config.prefix}_{config.max_len}{dim_part}{type_part}{norm_part}_embeddings.npz"
        return path

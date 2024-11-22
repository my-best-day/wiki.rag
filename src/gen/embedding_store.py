import os
import numpy as np
from uuid import UUID
from pathlib import Path
from filelock import FileLock
from typing import List, Tuple
from numpy.typing import NDArray


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

    def __init__(self, path):
        self.path = Path(path)

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
        np_str_uids, np_embeds = self._load_embeddings()
        np_str_uids = np.concatenate((np_str_uids, add_uids)) if len(np_str_uids) else add_uids
        np_embeds = np.concatenate((np_embeds, add_embeds)) if len(np_embeds) else add_embeds
        np.savez(self.path, uids=np_str_uids, embeddings=np_embeds)

    def get_count(self) -> int:
        """
        Get the number of embeddings in the store.
        :return: Number of embeddings in the store.
        """
        lock_path = self.lock_path
        with self.file_lock_class(lock_path):
            np_str_uids, _ = self._load_embeddings()
            count = len(np_str_uids)
        return count

    def load_embeddings(self) -> Tuple[List[int], List[np.ndarray]]:
        """
        Load embeddings from the store.
        Do type conversion and handle locks here.
        :return: an array of uids: List[UUID] and an array of embeddings: List[np.ndarray]
        """
        lock_path = self.lock_path
        with self.file_lock_class(lock_path):
            np_str_uids, np_embeddings = self._load_embeddings()
            np_uids = np.vectorize(UUID)(np_str_uids)
            return np_uids, np_embeddings

    def _load_embeddings(self) -> Tuple[NDArray[str], np.ndarray]:  # type: ignore
        """
        Load embeddings from the store.
        - It is the caller responsibility to very the file exists and handle
          locks.
        - this method returns a tuple of ndarrays.
        :return: an ndarray of uids: NDArray[UUID] and an ndarray of embeddings: NDArray[np.ndarray]
        """
        if self.does_store_exist():
            with np.load(self.path) as data:
                np_str_uids = data["uids"]
                np_embeddings = data["embeddings"]
        else:
            np_str_uids, np_embeddings = self.empty_result()

        return np_str_uids, np_embeddings

    # for testing purposes we move file.path.exists here
    def does_store_exist(self) -> bool:
        """Check if the store exists."""
        return self.path.exists()

    @staticmethod
    def empty_result() -> Tuple[List[UUID], np.ndarray]:
        uids = np.empty((0,), dtype=str)
        embeddings = np.empty((0, 0), dtype=float)
        return uids, embeddings

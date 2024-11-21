import os
import numpy as np
from uuid import UUID
from pathlib import Path
from filelock import FileLock
from typing import List, Tuple
from numpy.typing import NDArray


class EmbeddingStore:
    """
    Simple incremental store for embeddings.
    """

    def __init__(self, path):
        self.path = Path(path)

    @property
    def lock_path(self):
        return self.path.with_suffix(".lock")

    def extend_embeddings(self, uids: List[UUID], embeddings: List[np.ndarray]) -> None:
        """
        Add embeddings to the store.
        :param add_embeddings: List of tuples (segment_id, embedding)
        """
        str_uids = [str(uid) for uid in uids]
        lock_path = self.lock_path
        with CleanFileLock(lock_path):
            self._add_embeddings(str_uids, embeddings)

    def _add_embeddings(self, add_uids: List[str], add_embeddings: List[np.ndarray]):
        """
        Add embeddings to the store.
        :param add_embedding_list: List of tuples (segment_id, embedding)
        """
        add_str_uids = [str(uid) for uid in add_uids]
        np_str_uids, np_embeddings = self._load_embeddings()
        str_uids, embeddings = np_str_uids.tolist(), np_embeddings.tolist()
        str_uids.extend(add_str_uids)
        embeddings.extend(add_embeddings)
        np.savez(self.path, uids=str_uids, embeddings=add_embeddings)

    def get_count(self) -> int:
        """
        Get the number of embeddings in the store.
        :return: Number of embeddings in the store.
        """
        lock_path = self.lock_path
        with CleanFileLock(lock_path):
            if not self.path.exists():
                count = 0

            with np.load(self.path) as data:
                count = len(data["indices"])
        return count

    def load_embeddings(self) -> Tuple[List[int], List[np.ndarray]]:
        """
        Load embeddings from the store.
        Do type conversion and handle locks here.
        :return: an array of uids: List[UUID] and an array of embeddings: List[np.ndarray]
        """
        lock_path = self.lock_path
        with CleanFileLock(lock_path):
            np_str_uids, np_embeddings = self._load_embeddings()
            str_uids = np_str_uids.tolist()
            uids = [UUID(uid) for uid in str_uids]
            embeddings = np_embeddings.tolist()
            return uids, embeddings

    def _load_embeddings(self) -> Tuple[NDArray[str], NDArray[np.ndarray]]:  # type: ignore
        """
        Load embeddings from the store.
        - It is the caller responsibility to very the file exists and handle
          locks.
        - this method returns a tuple of ndarrays.
        :return: an ndarray of uids: NDArray[UUID] and an ndarray of embeddings: NDArray[np.ndarray]
        """
        if self.path.exists():
            with np.load(self.path) as data:
                np_str_uids = data["uids"]
                np_embeddings = data["embeddings"]
        else:
            np_str_uids = np.array([], dtype=str)
            np_embeddings = np.array([], dtype=np.ndarray)

        return np_str_uids, np_embeddings


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

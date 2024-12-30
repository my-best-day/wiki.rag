import logging
import numpy as np
from uuid import UUID
from typing import List, Tuple
from gen.embedding_store import EmbeddingStore, CleanFileLock

logger = logging.getLogger(__name__)


class UUIDEmbeddingStore(EmbeddingStore):
    """
    Simple incremental store for embeddings.
    """

    # Indirection allows easier substitution for testing purposes
    file_lock_class = CleanFileLock

    def extend_uuid_embeddings(self, uids: List[UUID], embeddings: np.ndarray) -> None:
        """
        Add embeddings to the store.
        Args:
            uids: List of UUIDs
            embeddings: List of embeddings (the output of a sentence_transformer.encode())
        """
        str_uids = [str(uid) for uid in uids]
        self.extend_embeddings(str_uids, embeddings)

    def load_uuid_embeddings(
        self,
        allow_empty: bool = False
    ) -> Tuple[List[UUID], List[np.ndarray]]:
        """
        Load embeddings from the store.
        Do type conversion and handle locks here.
        :return: an array of uids: List[UUID] and an array of embeddings: List[np.ndarray]
        """
        np_uids, np_embeddings = self.load_embeddings(allow_empty)
        np_uuid_uids = np.vectorize(UUID)(np_uids)
        return np_uuid_uids, np_embeddings

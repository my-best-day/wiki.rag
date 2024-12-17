"""
Sugar for loading and accessing the stores.
Consider refactoring this to make reduce duplication.
"""
import time
import logging
from uuid import UUID
from pathlib import Path
from typing import List, Tuple
from numpy.typing import NDArray
from threading import RLock, Thread
from typing import Optional as Opt
from gen.embedding_store import EmbeddingStore

from gen.element.store import Store
from gen.element.element import Element
from gen.element.article import Article
from gen.element.extended_segment import ExtendedSegment
from xutils.embedding_config import EmbeddingConfig

logger = logging.getLogger(__name__)


class Stores:
    def __init__(self, text_file_path: str, embedding_config: EmbeddingConfig):
        self.text_file_path = text_file_path

        self.embedding_config = embedding_config

        self._segments_loaded = False

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._extended_segments: Opt[List[ExtendedSegment]] = None
        self._articles: Opt[List[Article]] = None
        self._embeddings_article_ids: Opt[List[UUID]] = None

        self._lock = RLock()

    def background_load(self):
        def load():
            logging.basicConfig(level=logging.INFO)
            with self._lock:
                logger.info("Loading segments and embeddings in the background.")
                t0 = time.time()
                self._load_segments()
                t1 = time.time()
                logger.info(f"Segments loaded ({t1 - t0:.3f} secs).")
                t0 = t1
                self._load_embeddings()
                t1 = time.time()
                logger.info(f"Embeddings loaded ({t1 - t0:.3f} secs).")

        thread = Thread(target=load)
        thread.start()

    def _load_segments(self):
        """
        Caller is responsible for locking.s
        """
        if not self._segments_loaded:
            segment_file_path_str = \
                f"{self.embedding_config.prefix}_{self.embedding_config.max_len}_segments.json"
            segment_file_path = Path(segment_file_path_str)
            text_file_path = Path(self.text_file_path)
            segment_store = Store()
            segment_store.load_elements(text_file_path, segment_file_path)
            self._segments_loaded = True

    def _load_embeddings(self):
        """
        Caller is responsible for locking.s
        """
        if self._embeddings is None:
            embedding_store_path_str = EmbeddingStore.get_store_path(self.embedding_config)
            embedding_store_path = Path(embedding_store_path_str)
            embedding_store = EmbeddingStore(embedding_store_path)
            self._uids, self._embeddings = embedding_store.load_embeddings()

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        with self._lock:
            self._load_embeddings()
            return self._uids, self._embeddings

    @property
    def extended_segments(self) -> Store:
        with self._lock:
            if self._extended_segments is None:
                self._load_segments()
                extended_segments = [element for element in Element.instances.values()
                                     if isinstance(element, ExtendedSegment)]
                self._extended_segments = extended_segments
        return self._extended_segments

    @property
    def articles(self) -> List[Article]:
        with self._lock:
            if self._articles is None:
                self._load_segments()
                articles = [element for element in Element.instances.values()
                            if isinstance(element, Article)]
                self._articles = articles
        return self._articles

    def get_article(self, uid: UUID) -> Article:
        article = Element.instances.get(uid)
        return article

    def get_embeddings_article_ids(self) -> List[UUID]:
        if self._embeddings_article_ids is None:
            extended_segments = self.extended_segments
            self._embeddings_article_ids = [seg.article.uid for seg in extended_segments]
        return self._embeddings_article_ids

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
from gen.element.flat.flat_article import FlatArticle
from gen.element.flat.flat_extended_segment import FlatExtendedSegment
from xutils.embedding_config import EmbeddingConfig

logger = logging.getLogger(__name__)


class StoresFlat:
    def __init__(self, text_file_path: str, embedding_config: EmbeddingConfig):
        self.text_file_path = text_file_path

        self.embedding_config = embedding_config

        self._articles_loaded = False
        self._segments_loaded = False

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._segments: Opt[List[FlatExtendedSegment]] = None
        self._articles: Opt[List[FlatArticle]] = None

        self._store = Store(single_store=False)
        self._lock = RLock()

    def background_load(self):
        def load():
            logging.basicConfig(level=logging.INFO)
            with self._lock:
                logger.info("Loading segments and embeddings in the background.")

                t0 = time.time()
                # non-flat articles are loaded along with the segments
                self._load_flat_articles()
                t1 = time.time()
                logger.info(f"Articles loaded ({t1 - t0:.3f} secs).")

                t0 = time.time()
                self._load_flat_segments()
                t1 = time.time()
                logger.info(f"Segments loaded ({t1 - t0:.3f} secs).")

                t0 = time.time()
                self._load_embeddings()
                t1 = time.time()
                logger.info(f"Embeddings loaded ({t1 - t0:.3f} secs).")

        thread = Thread(target=load, daemon=True)
        thread.start()

    def _load_flat_articles(self):
        """
        Caller is responsible for locking.s
        """
        if not self._articles_loaded:
            flat_article_file_path = Path(f"{self.embedding_config.prefix}_flat_articles.json")
            text_file_path = Path(self.text_file_path)
            self._store.load_elements(text_file_path, flat_article_file_path)
            self._articles_loaded = True

    def _load_flat_segments(self):
        """
        Caller is responsible for locking.s
        """
        if not self._segments_loaded:
            flat_segment_file_path_str = \
                f"{self.embedding_config.prefix}_{self.embedding_config.max_len}_flat_segments.json"
            flat_segment_file_path = Path(flat_segment_file_path_str)
            text_file_path = Path(self.text_file_path)
            self._store.load_elements(text_file_path, flat_segment_file_path)
            self._segments_loaded = True

    def _load_embeddings(self):
        """
        Caller is responsible for locking.s
        """
        if self._embeddings is None:
            embedding_store_path_str = EmbeddingStore.get_store_path(self.embedding_config)
            embedding_store_path = Path(embedding_store_path_str)
            embedding_store = EmbeddingStore(embedding_store_path, allow_empty=False)
            self._uids, self._embeddings = embedding_store.load_embeddings()

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        with self._lock:
            self._load_embeddings()
            return self._uids, self._embeddings

    @property
    def extended_segments(self) -> Store:
        with self._lock:
            if self._segments is None:
                self._load_flat_segments()
                segments = [element for element in Element.instances.values()
                            if isinstance(element, FlatExtendedSegment)]
                self._segments = segments
        return self._segments

    @property
    def articles(self) -> List[Article]:
        with self._lock:
            if self._articles is None:
                self._load_flat_articles()
                articles = [element for element in Element.instances.values()
                            if isinstance(element, FlatArticle)]
                self._articles = articles
        return self._articles

    def get_article(self, uid: UUID) -> FlatArticle:
        article = Element.instances.get(uid)
        return article

    def get_embeddings_article_ids(self) -> List[UUID]:
        self._load_flat_articles()
        extended_segments = self.extended_segments
        article_ids = [seg.article.uid for seg in extended_segments]
        return article_ids

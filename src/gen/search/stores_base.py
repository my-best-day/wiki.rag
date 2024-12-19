import logging
from uuid import UUID
from pathlib import Path
from typing import List, Tuple
from numpy.typing import NDArray
from threading import RLock, Thread
from typing import Optional as Opt

from abc import ABC, abstractmethod

from xutils.utils import Utils
from gen.element.store import Store
from xutils.timer import LoggingTimer
from gen.element.element import Element
from gen.element.article import Article
from gen.element.extended_segment import ExtendedSegment
from gen.embedding_store import EmbeddingStore
from xutils.embedding_config import EmbeddingConfig
from gen.element.flat.flat_article import FlatArticle
from gen.element.flat.flat_extended_segment import FlatExtendedSegment

logger = logging.getLogger(__name__)


class StoresBase(ABC):
    def __init__(
        self,
        text_file_path_str: str,
        embed_config: EmbeddingConfig
    ) -> None:

        self.text_file_path = Path(text_file_path_str)
        self.embed_config = embed_config
        self.segment_file_path = self.get_element_file_path(
            embed_config,
            self.is_flat,
            "segments"
        )
        self.extended_segment_class = (
            FlatExtendedSegment if self.is_flat else ExtendedSegment)
        self.article_class = FlatArticle if self.is_flat else Article

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._segments_loaded = False

        self._articles: Opt[List[self.article_class]] = None
        self._extended_segments: Opt[List[FlatExtendedSegment]] = None
        self._embeddings_article_ids: Opt[List[UUID]] = None

        self._store = Store(single_store=False)
        self._lock = RLock()

    def background_load(self):
        if Utils.is_env_var_truthy("UNIT_TESTING"):
            return

        def load():
            logger.info("background_load starts")
            with self._lock:
                timer = LoggingTimer('background_load', logger=logger, level="DEBUG")
                # non-flat articles are loaded along with the segments
                self._load_articles()
                timer.restart("article loaded")

                self._load_segments()
                timer.restart("segments loaded")

                self._load_embeddings()
                timer.restart("embeddings loaded")

            logger.info("background_load done")

        thread = Thread(target=load, daemon=True)
        thread.start()

    @abstractmethod
    def _load_articles(self):
        raise NotImplementedError

    def _load_segments(self):
        """
        Caller is responsible for locking.s
        """
        if not self._segments_loaded:
            text_file_path = Path(self.text_file_path)
            segment_file_path = self.segment_file_path
            self._store.load_elements(text_file_path, segment_file_path)
            self._segments_loaded = True

    def _load_embeddings(self):
        """
        Caller is responsible for locking.s
        """
        if self._embeddings is None:
            embedding_store_path_str = EmbeddingStore.get_store_path(self.embed_config)
            embedding_store_path = Path(embedding_store_path_str)
            embedding_store = EmbeddingStore(embedding_store_path, allow_empty=False)
            self._uids, self._embeddings = embedding_store.load_embeddings()

    @staticmethod
    def get_element_file_path(embed_config: EmbeddingConfig, is_flat: bool, kind: str):
        len_part = f"_{embed_config.max_len}" if kind == "segments" else ""
        flat_part = "_flat" if is_flat else ""
        path_str = f"{embed_config.prefix}{len_part}{flat_part}_{kind}.json"
        path = Path(path_str)
        return path

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        with self._lock:
            self._load_embeddings()
            return self._uids, self._embeddings

    @property
    def extended_segments(self) -> Store:
        if self._extended_segments is None:
            with self._lock:
                if self._extended_segments is None:
                    self._load_articles()
                    self._load_segments()
                    segments = [
                        element
                        for element in Element.instances.values()
                        if isinstance(element, self.extended_segment_class)
                    ]
                    self._extended_segments = segments
        return self._extended_segments

    @property
    def articles(self) -> List[Article]:
        if self._articles is None:
            with self._lock:
                if self._articles is None:
                    self._load_segments()
                    articles = [
                        element
                        for element in Element.instances.values()
                        if isinstance(element, self.article_class)
                    ]
                    self._articles = articles
        return self._articles

    def get_article(self, uid: UUID) -> FlatArticle:
        article = Element.instances.get(uid)
        return article

    def get_embeddings_article_ids(self) -> List[UUID]:
        if self._embeddings_article_ids is None:
            extended_segments = self.extended_segments
            self._embeddings_article_ids = [
                seg.article.uid
                for seg in extended_segments
            ]
        return self._embeddings_article_ids

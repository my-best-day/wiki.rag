"""
Sugar for loading and accessing the stores.
Consider refactoring this to make reduce duplication.
"""
from uuid import UUID
from pathlib import Path
from typing import List, Tuple
from typing import Optional as Opt
from numpy.typing import NDArray

from gen.embedding_store import EmbeddingStore

from gen.element.store import Store
from gen.element.element import Element
from gen.element.article import Article
from gen.element.extended_segment import ExtendedSegment


class Stores:
    def __init__(self, text_file_path: str, path_prefix: str, max_len: int):
        self.text_file_path = text_file_path
        self.path_prefix = path_prefix
        self.max_len = max_len

        self._segments_loaded = False

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._extended_segments: Opt[List[ExtendedSegment]] = None
        self._articles: Opt[List[Article]] = None

    def _load_segments(self):
        if not self._segments_loaded:
            segment_file_path = Path(f"{self.path_prefix}_{self.max_len}_segments.json")
            text_file_path = Path(self.text_file_path)
            segment_store = Store()
            segment_store.load_elements(text_file_path, segment_file_path)
            self._segments_loaded = True

    @property
    def embeddings(self) -> Tuple[List[UUID], NDArray]:
        if self._embeddings is None:
            embedding_store_path = Path(f"{self.path_prefix}_{self.max_len}_embeddings.npz")
            embedding_store = EmbeddingStore(embedding_store_path)
            self._uids, self._embeddings = embedding_store.load_embeddings()
        return self._uids, self._embeddings

    @property
    def extended_segments(self) -> Store:
        if self._extended_segments is None:
            self._load_segments()
            extended_segments = [element for element in Element.instances.values()
                                 if isinstance(element, ExtendedSegment)]
            self._extended_segments = extended_segments
        return self._extended_segments

    @property
    def articles(self) -> List[Article]:
        if self._articles is None:
            self._load_segments()
            articles = [element for element in Element.instances.values()
                        if isinstance(element, Article)]
            self._articles = articles
        return self._articles

    def get_embeddings_article_ids(self) -> List[UUID]:
        extended_segments = self.extended_segments
        article_ids = [seg.article.uid for seg in extended_segments]
        return article_ids

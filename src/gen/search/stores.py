"""
Sugar for loading and accessing the stores.
Consider refactoring this to make reduce duplication.
"""
import logging
from gen.element.article import Article
from gen.element.extended_segment import ExtendedSegment
from xutils.embedding_config import EmbeddingConfig
from gen.search.stores_base import StoresBase

logger = logging.getLogger(__name__)


class Stores(StoresBase):
    is_flat = False

    def __init__(self, text_file_path: str, embedding_config: EmbeddingConfig):
        super().__init__(text_file_path, embedding_config)
        self.segment_file_path = self.get_element_file_path("segment", False)
        self.extended_segment_class = ExtendedSegment
        self.article_class = Article

    def _load_articles(self):
        # articles are loaded together with the segments
        pass

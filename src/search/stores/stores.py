"""
Sugar for loading and accessing the stores.
Consider refactoring this to make reduce duplication.
"""
import logging
from xutils.embedding_config import EmbeddingConfig
from search.stores.stores_base import StoresBase

logger = logging.getLogger(__name__)


class Stores(StoresBase):
    is_flat = False

    def __init__(self, text_file_path: str, embedding_config: EmbeddingConfig):
        super().__init__(text_file_path, embedding_config)

    def _load_articles(self):
        # articles are loaded together with the segments
        pass

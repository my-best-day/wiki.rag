"""
Sugar for loading and accessing the stores.
Consider refactoring this to make reduce duplication.
"""
import logging
from pathlib import Path
from xutils.embedding_config import EmbeddingConfig
from gen.search.stores_base import StoresBase

logger = logging.getLogger(__name__)


class StoresFlat(StoresBase):
    is_flat = True

    def __init__(self, text_file_path: str, embedding_config: EmbeddingConfig):
        super().__init__(text_file_path, embedding_config)
        self._articles_loaded = False

    def _load_articles(self):
        """
        Caller is responsible for locking.s
        """
        if not self._articles_loaded:
            flat_article_file_path = self._element_file_path("article", flat=True)
            text_file_path = Path(self.text_file_path)
            self._store.load_elements(text_file_path, flat_article_file_path)
            self._articles_loaded = True

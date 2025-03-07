"""
A store for flat articles.
"""
from pathlib import Path
from typing import Optional

from typing import List
from gen.element.store import Store
from gen.element.element import Element
from gen.element.flat.flat_article import FlatArticle
from xutils.byte_reader import ByteReader


class FlatArticleStore:
    """
    A store for flat articles.
    """
    def __init__(
        self,
        path_prefix: str,
        text_byte_reader: Optional[ByteReader] = None,
        store: Optional[Store] = None
    ) -> None:
        flat_article_store_path_str = f'{path_prefix}_flat_articles.json'
        flat_article_store_path = Path(flat_article_store_path_str)
        self.flat_article_store_path = flat_article_store_path
        self.text_byte_reader = text_byte_reader
        self.store = store or Store()

    def load_documents(self):
        """
        Load the documents from this document store.
        """
        documents = self.load_flat_articles()
        return documents

    def load_flat_articles(self):
        """Load the flat articles from the flat article store."""
        if self.text_byte_reader is None:
            raise ValueError("text_byte_reader is required to read flat articles")
        text_byte_reader = self.text_byte_reader
        flat_article_store_path = self.flat_article_store_path
        self.store.load_elements_byte_reader(text_byte_reader, flat_article_store_path)
        elements = Element.instances.values()
        flat_articles = [element for element in elements if isinstance(element, FlatArticle)]
        return flat_articles

    def write_flat_articles(self, flat_articles: List[FlatArticle]):
        """Write the flat articles to the flat article store."""
        flat_article_store_path = self.flat_article_store_path
        self.store.store_elements(flat_article_store_path, flat_articles)

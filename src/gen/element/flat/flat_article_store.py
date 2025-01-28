from pathlib import Path
from typing import Optional

from typing import List
from gen.element.store import Store
from gen.element.element import Element
from xutils.byte_reader import ByteReader
from gen.element.flat.flat_article import FlatArticle


class FlatArticleStore:
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

    def load_flat_articles(self):
        if self.text_byte_reader is None:
            raise ValueError("text_byte_reader is required to read flat articles")
        text_byte_reader = self.text_byte_reader
        flat_article_store_path = self.flat_article_store_path
        self.store.load_elements_byte_reader(text_byte_reader, flat_article_store_path)
        elements = Element.instances.values()
        flat_articles = [element for element in elements if isinstance(element, FlatArticle)]
        return flat_articles

    def write_flat_articles(self, flat_articles: List[FlatArticle]):
        flat_article_store_path = self.flat_article_store_path
        self.store.store_elements(flat_article_store_path, flat_articles)

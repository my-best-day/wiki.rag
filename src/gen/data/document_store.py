"""
DocumentStore is a store for documents.
It's a generalization of PlotStore and ArticleStore.
"""
from abc import ABC
from typing import List
from gen.element.flat.flat_article import FlatArticle


class DocumentStore(ABC):
    """
    A store for documents.
    A generalization of PlotStore and ArticleStore.
    """
    def load_documents(self) -> List[FlatArticle]:
        """Load the documents from the store."""
        raise NotImplementedError("Subclasses must implement this method")

from abc import ABC
from typing import List
from gen.element.flat.flat_article import FlatArticle


class DocumentStore(ABC):
    def load_documents(self) -> List[FlatArticle]:
        raise NotImplementedError("Subclasses must implement this method")

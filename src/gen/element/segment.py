from uuid import UUID
from typing import Optional
from gen.element.element import Element
from gen.element.article import Article

from gen.element.list_container import ListContainer


class Segment(ListContainer):
    def __init__(self, article: Article, element: Optional[Element] = None,
                 uid: Optional[UUID] = None):
        assert isinstance(article, Article), f"article must be an Article, not {type(article)}"
        super().__init__(element, uid=uid)
        self.article = article

    def to_xdata(self):
        xdata = super().to_xdata()
        xdata["article"] = str(self.article.uid)
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        uid = UUID(xdata["uid"])
        article_uid = UUID(xdata["article"])
        article = Element.instances[article_uid]
        segment = cls(article, uid=uid)
        return segment

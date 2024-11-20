from uuid import UUID
from typing import TYPE_CHECKING
from gen.element.element import Element
from gen.element.section import Section

if TYPE_CHECKING:
    from gen.element.article import Article


class Paragraph(Section):
    """
    A paragraph is a section with a pointer to the article it belongs to.
    """
    def __init__(self, offset: int, _bytes: bytes, article: 'Article', uid: UUID = None):
        super().__init__(offset, _bytes, uid)
        self.article = article
        article.append_paragraph(self)

    def to_xdata(self) -> dict:
        xdata = super().to_xdata()
        if self.article.uid not in Element.instances:
            self.article.to_xdata()
        xdata['article_uid'] = str(self.article.uid)
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        uid = UUID(xdata['uid'])
        offset = xdata['offset']
        length = xdata['length']
        _bytes = byte_reader.read_bytes(offset, length)
        article_uid = UUID(xdata['article_uid'])
        article = Element.instances[article_uid]
        paragraph = cls(offset, _bytes, article, uid=uid)
        return paragraph

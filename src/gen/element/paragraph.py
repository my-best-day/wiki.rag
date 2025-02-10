"""
A paragraph is a section of an article.
"""

from uuid import UUID
from typing import TYPE_CHECKING
from gen.element.element import Element
from gen.element.section import Section

if TYPE_CHECKING:  # pragma: no cover
    from gen.element.article import Article


class Paragraph(Section):
    """
    A paragraph is a section of an article.
    """
    def __init__(self, offset: int, _bytes: bytes, article: 'Article', uid: UUID = None):
        """
        Initialize the paragraph.
        Args:
            offset: the offset of the paragraph
            _bytes: the bytes of the paragraph
            article: the article the paragraph belongs to
            uid: the uid of the paragraph if loading from xdata
        """
        super().__init__(offset, _bytes, uid)
        self.article = article
        article.append_paragraph(self)

    def to_xdata(self) -> dict:
        """Convert the paragraph to xdata."""
        xdata = super().to_xdata()
        xdata['article_uid'] = str(self.article.uid)
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        """Create a paragraph from xdata."""
        uid = UUID(xdata['uid'])
        offset = xdata['offset']
        length = xdata['length']
        _bytes = byte_reader.read_bytes(offset, length)
        article_uid = UUID(xdata['article_uid'])
        article = Element.instances[article_uid]
        paragraph = cls(offset, _bytes, article, uid=uid)
        return paragraph

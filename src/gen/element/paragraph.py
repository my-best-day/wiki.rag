from typing import TYPE_CHECKING
from gen.element.element import Element
from gen.element.section import Section

if TYPE_CHECKING:
    from gen.element.article import Article


class Paragraph(Section):
    """
    A paragraph is a section with a pointer to the article it belongs to.
    """
    def __init__(self, offset: int, _bytes: bytes, article: 'Article'):
        super().__init__(offset, _bytes)
        self.article = article
        article.append_paragraph(self)

    def to_data(self):
        data = super().to_data()
        data['article'] = self.article.index
        return data

    def to_xdata(self) -> dict:
        xdata = super().to_xdata()
        xdata['article'] = self.article.index
        return xdata

    @classmethod
    def from_data(cls, data):
        article = Element.instances[data['article']]
        offset = data['offset']
        _bytes = data['text'].encode('utf-8')
        paragraph = cls(offset, _bytes, article)
        return paragraph

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        offset = xdata['offset']
        length = xdata['length']
        _bytes = byte_reader.read_bytes(offset, length)
        article_index = xdata['article']
        article = cls.instances[article_index]
        paragraph = cls(offset, _bytes, article)
        return paragraph

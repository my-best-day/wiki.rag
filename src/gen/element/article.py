import logging
from gen.element.header import Header
from gen.element.paragraph import Paragraph
from gen.element.container import Container
from gen.element.element import Element
from typing import List, Iterator


class Article(Container):
    """
    Article is a container of a header and paragraphs.
    """
    def __init__(self, header: Header) -> None:
        """
        Create a new article.
        """
        assert isinstance(header, Header), 'header must be a Header'
        super().__init__()
        self._header: Header = header
        self._paragraphs: List[Paragraph] = []

    def to_data(self):
        data = super().to_data()
        data['header'] = self.header.to_data()
        paragraphs_data = [paragraph.to_data() for paragraph in self.paragraphs]
        data['paragraphs'] = paragraphs_data
        return data

    def to_xdata(self) -> int:
        xdata = super().to_xdata()
        xdata['header'] = self.header.index
        return xdata

    @classmethod
    def from_data(cls, data):
        header = Element.hierarchy_from_data(data['header'])

        article = cls(header)

        paragraphs_data = data['paragraphs']
        for paragraph_data in paragraphs_data:
            Element.hierarchy_from_data(paragraph_data)

        return article

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        header_index = xdata['header']
        header = cls.instances[header_index]
        article = cls(header)
        return article

    @property
    def offset(self) -> int:
        """
        The offset of the article.
        """
        return self.header.offset

    @property
    def header(self) -> Header:
        """
        The header of the article.
        """
        return self._header

    @property
    def paragraphs(self) -> Iterator[Paragraph]:
        """
        Iterate over the paragraphs in the article.
        """
        yield from self._paragraphs

    @property
    def elements(self) -> Iterator[Element]:
        """
        Iterate over the elements in the article.
        Elements are the header and paragraphs.
        """
        yield self._header
        yield from self._paragraphs

    def append_paragraph(self, paragraph: Paragraph) -> None:
        """
        Append a paragraph to the article.
        """
        assert isinstance(paragraph, Paragraph), 'paragraph must be an Paragraph '
        f'(got {type(paragraph)})'

        self._paragraphs.append(paragraph)

    def append_element(self, element: Element) -> None:
        """
        Append an element to the article.
        """
        self.append_paragraph(element)

    @property
    def element_count(self) -> int:
        """
        The number of elements in the article.
        """
        return len(self._paragraphs) + 1

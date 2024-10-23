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

from uuid import UUID
from typing import Iterator, Optional
from gen.element.header import Header
from gen.element.list_container import ListContainer
from gen.element.paragraph import Paragraph
from gen.element.container import Container
from gen.element.element import Element


class Article(Container):
    """
    Article is a container of a header and paragraphs.
    """
    def __init__(self, header: Header, uid: Optional[UUID] = None) -> None:
        """
        Create a new article.
        """
        assert isinstance(header, Header), 'header must be a Header'
        super().__init__(uid=uid)
        self._header: Header = header
        self.body = ListContainer()

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
        yield from self.body.elements

    @property
    def elements(self) -> Iterator[Element]:
        """
        Iterate over the elements in the article.
        Elements are the header and paragraphs.
        """
        yield self._header
        yield from self.body.elements

    def append_paragraph(self, paragraph: Paragraph) -> None:
        """
        Append a paragraph to the article.
        """
        assert isinstance(paragraph, Paragraph), 'paragraph must be an Paragraph '
        f'(got {type(paragraph)})'

        self.body.append_element(paragraph)

    def append_element(self, element: Element) -> None:
        """
        Append an element to the article.
        """
        self.append_paragraph(element)

    @property
    def paragraph_count(self) -> int:
        """
        The number of paragraphs in the article.
        """
        return self.body.element_count

    @property
    def element_count(self) -> int:
        """
        The number of elements in the article.
        """
        return self.body.element_count + 1

    def to_xdata(self) -> int:
        xdata = super().to_xdata()
        xdata['header_uid'] = str(self.header.uid)
        xdata['body_uid'] = str(self.body.uid)
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        uid = UUID(xdata['uid'])
        header_uid = UUID(xdata['header_uid'])
        header = cls.instances[header_uid]
        article = cls(header, uid=uid)
        return article

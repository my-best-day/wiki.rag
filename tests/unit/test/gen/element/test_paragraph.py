
from .test_section import TestSection
from gen.element.header import Header
from gen.element.article import Article
from gen.element.section import Section
from gen.element.paragraph import Paragraph


class TestParagraph(TestSection):
    def create_section(self, offset: int, _bytes: bytes) -> Section:
        article = Article(Header(0, b'a'))
        return Paragraph(offset, _bytes, article)

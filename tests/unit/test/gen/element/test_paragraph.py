
from .test_section import TestSection
from gen.element.section import Section
from gen.element.paragraph import Paragraph


class TestParagraph(TestSection):
    def create_section(self, offset: int, _bytes: bytes) -> Section:
        return Paragraph(offset, _bytes)

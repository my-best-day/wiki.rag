
from .test_section import TestSection
from gen.element.section import Section
from gen.element.header import Header


class TestHeader(TestSection):
    def create_section(self, offset: int, _bytes: bytes) -> Section:
        return Header(offset, _bytes)

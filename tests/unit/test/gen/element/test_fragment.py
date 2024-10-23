
from .test_section import TestSection
from gen.element.section import Section
from gen.element.fragment import Fragment


class TestFragment(TestSection):
    def create_section(self, offset: int, _bytes: bytes) -> Section:
        section = Section(offset, _bytes)
        return Fragment(section, offset, _bytes)

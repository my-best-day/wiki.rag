import unittest
from .test_list_container import TestListContainer
from gen.element.segment import Segment
from gen.element.section import Section


class TestSegment(TestListContainer):
    container_class = Segment

    def setUp(self):
        self.sections = [
            Section(17, b'hello'),
            Section(23, b'world'),
        ]
        self.container = Segment()
        for section in self.sections:
            self.container.append_element(section)

        _bytes = b'h\xc3\xa9llo!'
        self.dirty_sections = [
            Section(23, _bytes),
            Section(28, _bytes),
        ]
        self.dirty = Segment()
        for dirty_section in self.dirty_sections:
            self.dirty.append_element(dirty_section)


if __name__ == '__main__':
    unittest.main()

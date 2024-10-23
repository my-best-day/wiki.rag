import unittest
from typing import Iterator
from gen.element.section import Section
from gen.element.list_container import ListContainer
from .common_container_tests import common_container_tests


class TestListContainer(unittest.TestCase):

    def setUp(self):
        self.sections = [
            Section(17, b'hello'),
            Section(23, b'world'),
        ]
        self.container = ListContainer()
        for section in self.sections:
            self.container.append_element(section)

        _bytes = b'h\xc3\xa9llo!'
        self.dirty_sections = [
            Section(23, _bytes),
            Section(28, _bytes),
        ]
        self.dirty = ListContainer()
        for dirty_section in self.dirty_sections:
            self.dirty.append_element(dirty_section)

    def test_common(self):
        for test_func in common_container_tests(self.container, self.sections):
            test_func()

    def test_common_dirty(self):
        for test_func in common_container_tests(self.dirty, self.dirty_sections):
            test_func()

    def test_constructor(self):
        empty = ListContainer()
        self.assertEqual(len(list(empty.elements)), 0)

    def test_elements_and_append_element(self):
        self.assertEqual(list(self.container.elements), self.sections)

    def test_offset(self):
        self.assertEqual(self.container.offset, self.sections[0].offset)

        container = ListContainer()
        container.append_element(self.sections[0])
        self.assertEqual(container.offset, self.sections[0].offset)

        container.append_element(self.sections[1])
        self.assertEqual(container.offset, self.sections[0].offset)

    def test_text(self):
        self.assertEqual(
            self.container.text,
            self.sections[0].text + self.sections[1].text)

    def test_bad_construction(self):
        empty = ListContainer()
        # offset is None
        with self.assertRaises(ValueError):
            empty.offset

    def test_clean_text(self):
        self.assertEqual(self.dirty.clean_text, 'hello!hello!')

    def test_byte_length(self):
        self.assertEqual(
            self.dirty.byte_length,
            self.dirty_sections[0].byte_length + self.dirty_sections[1].byte_length
        )

    def test_char_length(self):
        self.assertEqual(
            self.dirty.char_length,
            self.dirty_sections[0].char_length + self.dirty_sections[1].char_length
        )

    def test_clean_length(self):
        self.assertEqual(
            self.dirty.clean_length,
            self.dirty_sections[0].clean_length + self.dirty_sections[1].clean_length
        )

    def test_append_bytes_and_reset(self):
        self.sections[0].append_bytes(b' <<sweet>> ')
        self.assertEqual(self.container.text, 'hello <<sweet>> world')
        self.assertEqual(self.container.clean_text, 'hello sweet world')

    def test_prepend_and_reset(self):
        self.sections[0].prepend_bytes(b'hey$$$ ')
        self.assertEqual(self.container.offset, self.sections[0].offset)
        self.assertEqual(self.container.text, 'hey$$$ helloworld')
        self.assertEqual(self.container.clean_text, 'hey helloworld')

    def test_elements_property_returns_iterator(self):
        self.assertIsInstance(self.container.elements, Iterator)

    def test_append_non_element(self):
        with self.assertRaises(AssertionError):
            self.container.append_element("not an element")

    def test_offset_with_empty_container(self):
        empty_container = ListContainer()
        with self.assertRaises(ValueError):
            _ = empty_container.offset

    def test_bytes_property(self):
        self.assertEqual(self.container.bytes, b'helloworld')

    def test_reset_clears_cache(self):
        # Access properties to populate cache
        _ = self.container.bytes
        _ = self.container.text
        _ = self.container.clean_text

        # Modify an element directly (not recommended in practice)
        self.sections[0]._bytes = b'modified'

        # Reset the container
        self.container.reset()

        # Check if cache is cleared
        self.assertEqual(self.container.bytes, b'modifiedworld')
        self.assertEqual(self.container.text, 'modifiedworld')
        self.assertEqual(self.container.clean_text, 'modifiedworld')


if __name__ == '__main__':
    unittest.main()

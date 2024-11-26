import json
import unittest
from io import StringIO, BytesIO
from unittest.mock import mock_open, patch

from gen.element.store import Store
from gen.element.header import Header
from gen.element.article import Article
from gen.element.element import Element
from gen.element.section import Section
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment
from .byte_reader_tst import TestByteReader


class TestStore(unittest.TestCase):

    def setUp(self):
        self.store = Store()

    def test_write_and_load(self):
        section = Section(12, b'Hello, World!')
        handle = StringIO()
        self.store.write_elements_to_handle(handle, [section])

        test_byte_reader = TestByteReader.from_element(section)
        Element.instances.clear()
        handle.seek(0)

        self.store.load_elements_from_handle(test_byte_reader, handle)

        self.assertEqual(len(Element.instances), 1)
        self.assertIsInstance(Element.instances[section.uid], Section)
        section2 = Element.instances[section.uid]
        self.assertEqual(section2.offset, section.offset)
        self.assertEqual(section2.bytes, section.bytes)

    def test_write_and_load_multiple(self):
        sec1 = Section(0, b"section 1")
        sec2 = Section(sec1.byte_length + 1, b"section 2")
        sec3 = Section(sec2.byte_length + 1, b"section 3")
        sec4 = Section(sec3.byte_length + 1, b"section 4")
        sec5 = Section(sec4.byte_length + 1, b"section 5")
        sec6 = Section(sec5.byte_length + 1, b"section 6")

        _bytes = b''.join([sec1.bytes, sec2.bytes, sec3.bytes, sec4.bytes, sec5.bytes, sec6.bytes])

        _, fragment1 = sec2.split(-4, after_char=True, include_first=False, include_remainder=True)
        fragment2, _ = sec5.split(4, after_char=True, include_first=True, include_remainder=False)

        header = Header(0, b'')
        article = Article(header)

        segment1 = Segment(article, sec1)
        segment1.append_element(sec2)

        segment2 = Segment(article, sec3)
        segment2.append_element(sec4)

        segment3 = Segment(article, sec5)
        segment3.append_element(sec6)

        extended_segment = ExtendedSegment(segment2)
        extended_segment.before_overlap = fragment1
        extended_segment.after_overlap = fragment2

        handle = StringIO()
        self.store.write_elements_to_handle(handle, Element.instances.values())

        test_byte_reader = TestByteReader(_bytes)
        Element.instances.clear()
        handle.seek(0)

        self.store.load_elements_from_handle(test_byte_reader, handle)

    @patch("builtins.open", new_callable=mock_open)
    def test_store_elements(self, mock_file):
        section = Section(12, b'Hello, World!')
        path = '/tmp/test_store_elements.json'
        self.store.store_elements(path, [section])

        mock_file.assert_called_once_with(path, 'w')
        handle = mock_file()
        handle.write.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_load_elements(self, mock_open_func):
        section = Section(12, b'Hello, World!')
        xdata = section.to_xdata()
        json_xdata = json.dumps(xdata)

        text_file_path = '/tmp/test_text_file.txt'
        element_store_path = '/tmp/test_load_elements.json'

        # Separate mocks for each file path to avoid relying on call order
        text_file = BytesIO(b' ' * 12 + b'Hello, World!')
        json_file = StringIO(json_xdata + '\n')

        # Set up side effect to match file paths with mocks
        def open_side_effect(filepath, *args, **kwargs):
            if filepath == text_file_path:
                return text_file
            elif filepath == element_store_path:
                return json_file
            else:
                raise FileNotFoundError(f"Mocked open does not recognize the path: {filepath}")

        mock_open_func.side_effect = open_side_effect

        Element.instances.clear()
        self.store.load_elements(text_file_path, element_store_path)
        section2 = Element.instances[section.uid]

        self.assertEqual(len(Element.instances), 1)
        self.assertIsInstance(section2, Section)
        self.assertEqual(section2.offset, section.offset)
        self.assertEqual(section2.bytes, section.bytes)

    @patch("builtins.open")
    def test_buffer_size(self, mock_open_func):
        sections = []
        for i in range(5):
            bts = b'Hello, World!'
            lng = len(bts)
            sections.append(Section(i * lng, bts))

        Store._buffer_size = 2
        store = Store()
        buffer = StringIO()
        store.write_elements_to_handle(buffer, sections)

        buffer.seek(0)
        text = buffer.read()
        lines = text.split('\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[-1], '')


if __name__ == '__main__':
    unittest.main()

import unittest
from uuid import UUID
from io import StringIO

from gen.element.store import Store
from gen.element.header import Header
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.element import Element
from gen.element.fragment import Fragment
from gen.element.paragraph import Paragraph
from gen.element.list_container import ListContainer
from gen.element.extended_segment import ExtendedSegment

from .byte_reader_tst import TestByteReader


class TestElement(unittest.TestCase):
    def setUp(self):
        Element.instances.clear()

    def test_normalize_text_empty_string(self):
        self.assertEqual(Element.normalize_text(""), "")

    def test_normalize_text_clean_text(self):
        self.assertEqual(Element.normalize_text("abcDEF123 ,.!?'\"-"), "abcdef123 ,.!?'\"-")

    def test_normalize_text_special_characters(self):
        self.assertEqual(Element.normalize_text("ab@#$%^&*()cd"), "ab cd")

    def test_normalize_text_multiple_spaces(self):
        self.assertEqual(Element.normalize_text("  Multiple   Spaces  "), "multiple spaces")

    def test_normalize_text_mixed_case(self):
        self.assertEqual(Element.normalize_text("Mixed CASE text"), "mixed case text")

    def test_normalize_text_whitespace_characters(self):
        self.assertEqual(Element.normalize_text("Special\nCharacters\tAnd\rWhitespace"),
                         "special characters and whitespace")

    def test_normalize_text_non_ascii(self):
        self.assertEqual(Element.normalize_text("Café & Co."), "cafe co.")
        self.assertEqual(Element.normalize_text(
            # cspell:disable-next-line
            "Números en español: 1º 2º 3º"), "numeros en espanol 1 2 3")

    def test_normalize_text_long_input(self):
        n = 10
        m = 10
        long_input = "A" * n + "@#$%" * m + "Z" * n
        expected_output = "a" * n + " " + "z" * n
        self.assertEqual(Element.normalize_text(long_input), expected_output.strip())

    def test_split_naive(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo world'
        section = Section(offset, _bytes)
        first, second = section.split(7)
        self.assertIsInstance(first, Fragment)
        self.assertIsInstance(second, Fragment)
        self.assertEqual(first.offset, 23)
        self.assertEqual(first.bytes, b'h\xc3\xa9llo ')
        self.assertEqual(second.offset, 30)
        self.assertEqual(second.bytes, b'world')

    def test_split_multi_bytes_char(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo world'
        section = Section(offset, _bytes)
        first, second = section.split(2)
        self.assertIsInstance(first, Fragment)
        self.assertIsInstance(second, Fragment)
        self.assertEqual(first.offset, 23)
        self.assertEqual(first.bytes, b'h')
        self.assertEqual(second.offset, 24)
        self.assertEqual(second.bytes, b'\xc3\xa9llo world')

        first, second = section.split(2, after_char=True)
        self.assertIsInstance(first, Fragment)
        self.assertIsInstance(second, Fragment)
        self.assertEqual(first.offset, 23)
        self.assertEqual(first.bytes, b'h\xc3\xa9')
        self.assertEqual(second.offset, 26)
        self.assertEqual(second.bytes, b'llo world')

    def test_str_lol(self):
        element = Section(0, b"")
        self.assertEqual(str(element), f"Section (uid={element.uid})")

    def test_to_xdata(self):
        element = Section(15, b"hello")
        expected = {'class': 'Section',
                    'uid': str(element.uid),
                    'offset': 15,
                    'length': element.byte_length}
        self.assertEqual(element.to_xdata(), expected)

        element = Section(27, b"world")
        expected = {'class': 'Section',
                    'uid': str(element.uid),
                    'offset': 27,
                    'length': element.byte_length}
        self.assertEqual(element.to_xdata(), expected)

    def test_hierarchy_from_xdata(self):
        element = Section(15, b"hello")
        xdata = element.to_xdata()
        byte_reader = TestByteReader.from_element(element)

        element2 = Element.hierarchy_from_xdata(xdata, byte_reader)
        self.assertIsInstance(element2, Section)
        self.assertEqual(element2.offset, element.offset)
        self.assertEqual(element2.bytes, element2.bytes)

    def test_hierarchy_from_xdata_article(self):
        Element.instances.clear()
        header = Header(40, b'header')
        article = Article(header)

        header_end = header.offset + header.byte_length
        paragraph1 = Paragraph(header_end, b'paragraph 1', article)
        paragraph1_end = paragraph1.offset + paragraph1.byte_length
        paragraph2 = Paragraph(paragraph1_end, b'paragraph 2', article)
        self.assertEqual(len(article._paragraphs), 2)

        element_json_buffer = StringIO()
        store = Store()
        store.write_elements_to_handle(element_json_buffer, Element.instances.values())
        _bytes = b' ' * 40 + header.bytes + paragraph1.bytes + paragraph2.bytes
        text_reader = TestByteReader(_bytes)

        Element.instances.clear()
        element_json_buffer.seek(0)
        store.load_elements_from_handle(text_reader, element_json_buffer)

        article2 = Element.instances[article.uid]
        self.assertIsInstance(article2, Article)
        self.assertEqual(article2.header.bytes, b'header')
        self.assertEqual(len(article2._paragraphs), 2)
        self.assertEqual(article2._paragraphs[0].bytes, paragraph1.bytes)
        self.assertEqual(article2._paragraphs[1].bytes, paragraph2.bytes)

    def test_extended_segment(self):
        sec0 = Section(0, b"before overlap")
        sec1 = Section(sec0.offset + sec0.byte_length, b"section 1")
        sec2 = Section(sec1.offset + sec1.byte_length, b"section 2")
        sec3 = Section(sec2.offset + sec2.byte_length, b"section 3")
        sec4 = Section(sec3.offset + sec3.byte_length, b"section 4")
        sec5 = Section(sec4.offset + sec4.byte_length, b"after overlap")

        segment1 = Segment(sec1)
        segment1.append_element(sec2)

        segment2 = Segment(sec3)
        segment2.append_element(sec4)

        extended_segment = ExtendedSegment(segment1)
        extended_segment.append_element(segment2)
        extended_segment.before_overlap = sec0
        extended_segment.after_overlap = sec5

        xdata_list = []
        for segment in [segment1, segment2]:
            for element in segment.elements:
                xdata_list.append(element.to_xdata())

        xdata_list.extend([
            extended_segment.segment.to_xdata(),
            extended_segment.to_xdata(),
            extended_segment.before_overlap.to_xdata(),
            extended_segment.after_overlap.to_xdata()
        ])
        byte_reader = TestByteReader.from_element(extended_segment)

        Element.instances.clear()

        objects = []
        for xdata in xdata_list:
            obj = Element.hierarchy_from_xdata(xdata, byte_reader)
            objects.append(obj)
        for xdata in xdata_list:
            uid = UUID(xdata['uid'])
            Element.instances[uid].resolve_dependencies(xdata)

        extended_segment2 = objects[6]

        self.assertIsInstance(extended_segment2, ExtendedSegment)
        self.assertEqual(extended_segment2.before_overlap.bytes, b"before overlap")
        self.assertEqual(extended_segment2.segment.bytes, b"section 1section 2section 3section 4")
        self.assertEqual(extended_segment2.after_overlap.bytes, b"after overlap")

    def test_fragment(self):
        section = Section(0, b"hello world")
        fragment = Fragment(section, 6, b"world")

        xdata = fragment.to_xdata()
        byte_reader = TestByteReader.from_element(section)
        fragment2 = Element.hierarchy_from_xdata(xdata, byte_reader)
        self.assertIsInstance(fragment2, Fragment)
        self.assertEqual(fragment2.offset, 6)
        self.assertEqual(fragment2.bytes, b"world")
        self.assertIsInstance(fragment2.parent, Section)

    def test_header(self):
        header = Header(39, b'header')

        xdata = header.to_xdata()
        byte_reader = TestByteReader.from_element(header)
        header2 = Element.hierarchy_from_xdata(xdata, byte_reader)
        self.assertIsInstance(header2, Header)
        self.assertEqual(header2.offset, 39)
        self.assertEqual(header2.bytes, b'header')

    def test_list_container(self):
        sec1 = Section(0, b"section 1")
        sec2 = Section(sec1.offset + sec1.byte_length, b"section 2")  # 9
        sec3 = Section(sec2.offset + sec2.byte_length, b"section 3")  # 18
        sec4 = Section(sec3.offset + sec3.byte_length, b"section 4")  # 27

        list_container_1a = ListContainer(sec1)
        list_container_1a.append_element(sec2)

        list_container_1b = ListContainer()
        list_container_1b.append_element(sec3)
        list_container_1b.append_element(sec4)

        _bytes = b''
        xdata_list = []
        for list_container in [list_container_1a, list_container_1b]:
            for element in list_container.elements:
                xdata_list.append(element.to_xdata())
            xdata_list.append(list_container.to_xdata())
            _bytes += list_container.bytes

        byte_reader = TestByteReader(_bytes)

        Element.instances.clear()

        objects = [Element.hierarchy_from_xdata(xdata, byte_reader) for xdata in xdata_list]
        for xdata in xdata_list:
            uid = UUID(xdata['uid'])
            Element.instances[uid].resolve_dependencies(xdata)

        list_container_2a = objects[2]
        self.assertIsInstance(list_container_2a, ListContainer)
        self.assertEqual(list_container_2a.element_count, 2)
        self.assertEqual(list_container_2a.offset, 0)
        self.assertEqual(list_container_2a._elements[0].offset, 0)
        self.assertEqual(list_container_2a._elements[1].offset, 9)
        self.assertEqual(list_container_2a._elements[1].bytes, b"section 2")

        list_container_2b = objects[5]
        self.assertIsInstance(list_container_2b, ListContainer)
        self.assertEqual(list_container_2b.element_count, 2)
        self.assertEqual(list_container_2b.offset, 18)
        self.assertEqual(list_container_2b._elements[0].offset, 18)
        self.assertEqual(list_container_2b._elements[1].offset, 27)
        self.assertEqual(list_container_2b._elements[1].bytes, b"section 4")

    def test_paragraph(self):
        header = Header(30, b'header')
        article = Article(header)
        paragraph = Paragraph(39, b'paragraph', article)

        xdata = paragraph.to_xdata()
        byte_reader = TestByteReader.from_element(paragraph)
        paragraph2 = Element.hierarchy_from_xdata(xdata, byte_reader)
        self.assertIsInstance(paragraph2, Paragraph)
        self.assertEqual(paragraph2.offset, 39)
        self.assertEqual(paragraph2.bytes, b'paragraph')

    def test_section(self):
        section = Section(39, b'section')

        xdata = section.to_xdata()
        byte_reader = TestByteReader.from_element(section)
        section2 = Element.hierarchy_from_xdata(xdata, byte_reader)
        self.assertIsInstance(section2, Section)
        self.assertEqual(section2.offset, 39)
        self.assertEqual(section2.bytes, b'section')

    def test_segment(self):
        sec1 = Section(39, b'section')
        segment = Segment(sec1)
        segment.append_element

        xdata_list = [
            sec1.to_xdata(),
            segment.to_xdata()
        ]
        byte_reader = TestByteReader.from_element(segment)

        Element.instances.clear()

        objects = []
        for xdata in xdata_list:
            obj = Element.hierarchy_from_xdata(xdata, byte_reader)
            objects.append(obj)
        for xdata in xdata_list:
            uid = UUID(xdata['uid'])
            Element.instances[uid].resolve_dependencies(xdata)

        segment2 = objects[1]
        self.assertIsInstance(segment2, Segment)
        self.assertEqual(segment2.offset, 39)
        self.assertEqual(segment2.bytes, b'section')

    def test_abstract_element(self):
        element = Element()

        with self.assertRaises(NotImplementedError):
            element.offset

        with self.assertRaises(NotImplementedError):
            element.bytes

        with self.assertRaises(NotImplementedError):
            element.text

        with self.assertRaises(NotImplementedError):
            element.clean_text

        with self.assertRaises(NotImplementedError):
            element.byte_length

        with self.assertRaises(NotImplementedError):
            element.char_length

        with self.assertRaises(NotImplementedError):
            element.clean_length


if __name__ == '__main__':
    unittest.main()

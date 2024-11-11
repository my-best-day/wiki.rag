import json
import unittest
from gen.element.header import Header
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.overlap import Overlap
from gen.element.element import Element
from gen.element.fragment import Fragment
from gen.element.paragraph import Paragraph
from gen.element.list_container import ListContainer
from gen.element.extended_segment import ExtendedSegment


class TestElement(unittest.TestCase):

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
        self.assertEqual(str(element), f"Section (index={element.index})")

    def test_to_data(self):
        element = Section(15, b"hello")
        expected = {'class': 'Section', 'offset': 15, 'text': 'hello'}
        self.assertEqual(element.to_data(), expected)

        element = Section(27, b"world")
        expected = {'class': 'Section', 'offset': 27, 'text': 'world'}
        self.assertEqual(element.to_data(), expected)

    def test_to_json(self):
        element = Section(15, b"hello")
        expected = {'class': 'Section', 'offset': 15, 'text': 'hello'}
        expected_json_string = json.dumps(expected)
        self.assertEqual(element.to_json(), expected_json_string)

        element = Section(27, b"world")
        expected = {'class': 'Section', 'offset': 27, 'text': 'world'}
        expected_json_string = json.dumps(expected)
        self.assertEqual(element.to_json(), expected_json_string)

    def test_hierarchy_from_data(self):
        data = {'class': 'Section', 'offset': 15, 'text': 'hello'}
        element = Element.hierarchy_from_data(data)
        self.assertIsInstance(element, Section)
        self.assertEqual(element.offset, 15)
        self.assertEqual(element.bytes, b'hello')

    def test_hierarchy_from_data_article(self):
        article = Article(Header(39, b'header'))
        article.append_paragraph(Paragraph(40, b'paragraph 1'))
        article.append_paragraph(Paragraph(60, b'paragraph 2'))

        data = article.to_data()
        article2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(article2, Article)
        self.assertEqual(article2.header.bytes, b'header')
        self.assertEqual(article2._paragraphs[0].bytes, b'paragraph 1')
        self.assertEqual(article2._paragraphs[1].bytes, b'paragraph 2')

    def test_extended_segment(self):
        segment1 = Segment(Section(0, b"section 1"))
        segment1.append_element(Section(10, b"section 2"))

        segment2 = Segment(Section(20, b"section 3"))
        segment2.append_element(Section(40, b"section 4"))

        extended_segment = ExtendedSegment(segment1)
        extended_segment.append_element(segment2)
        extended_segment.before_overlap = Overlap(b"before overlap")
        extended_segment.after_overlap = Overlap(b"after overlap")

        data = extended_segment.to_data()
        extended_segment2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(extended_segment2, ExtendedSegment)
        self.assertEqual(extended_segment2.before_overlap.bytes, b"before overlap")
        self.assertEqual(extended_segment2.segment.bytes, b"section 1section 2section 3section 4")
        self.assertEqual(extended_segment2.after_overlap.bytes, b"after overlap")

    def test_fragment(self):
        section = Section(0, b"hello world")
        fragment = Fragment(section, 6, b"world")
        data = fragment.to_data()

        fragment2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(fragment2, Fragment)
        self.assertEqual(fragment2.offset, 6)
        self.assertEqual(fragment2.bytes, b"world")
        self.assertIsInstance(fragment2.parent_section, Section)

    def test_header(self):
        header = Header(39, b'header')
        data = header.to_data()

        header2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(header2, Header)
        self.assertEqual(header2.offset, 39)
        self.assertEqual(header2.bytes, b'header')

    def test_list_container(self):
        list_container_1a = ListContainer(Section(0, b"section 1"))
        list_container_1a.append_element(Section(10, b"section 2"))

        list_container_1b = ListContainer()
        list_container_1b.append_element(Section(20, b"section 3"))
        list_container_1b.append_element(Section(40, b"section 4"))

        data_a = list_container_1a.to_data()
        data_b = list_container_1b.to_data()

        list_container_2a = Element.hierarchy_from_data(data_a)
        self.assertIsInstance(list_container_2a, ListContainer)
        self.assertEqual(list_container_2a.element_count, 2)
        self.assertEqual(list_container_2a.offset, 0)
        self.assertEqual(list_container_2a._elements[0].offset, 0)
        self.assertEqual(list_container_2a._elements[1].offset, 10)
        self.assertEqual(list_container_2a._elements[1].bytes, b"section 2")

        list_container_2b = Element.hierarchy_from_data(data_b)
        self.assertIsInstance(list_container_2b, ListContainer)
        self.assertEqual(list_container_2b.element_count, 2)
        self.assertEqual(list_container_2b.offset, 20)
        self.assertEqual(list_container_2b._elements[0].offset, 20)
        self.assertEqual(list_container_2b._elements[1].offset, 40)
        self.assertEqual(list_container_2b._elements[1].bytes, b"section 4")

    def test_overlap(self):
        overlap = Overlap(b"overlap")
        data = overlap.to_data()

        overlap2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(overlap2, Overlap)
        self.assertEqual(overlap2.bytes, b"overlap")

    def test_paragraph(self):
        paragraph = Paragraph(39, b'paragraph')
        data = paragraph.to_data()

        paragraph2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(paragraph2, Paragraph)
        self.assertEqual(paragraph2.offset, 39)
        self.assertEqual(paragraph2.bytes, b'paragraph')

    def test_section(self):
        section = Section(39, b'section')
        data = section.to_data()

        section2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(section2, Section)
        self.assertEqual(section2.offset, 39)
        self.assertEqual(section2.bytes, b'section')

    def test_segment(self):
        segment = Segment(Section(39, b'section'))
        segment.append_element
        data = segment.to_data()

        segment2 = Element.hierarchy_from_data(data)
        self.assertIsInstance(segment2, Segment)
        self.assertEqual(segment2.offset, 39)
        self.assertEqual(segment2.bytes, b'section')

    def test_json(self):
        element = Section(15, b"hello")
        expected = {'class': 'Section', 'offset': 15, 'text': 'hello'}
        expected_json_string = json.dumps(expected)
        self.assertEqual(element.to_json(), expected_json_string)

        element = Section(27, b"world")
        expected = {'class': 'Section', 'offset': 27, 'text': 'world'}
        expected_json_string = json.dumps(expected)
        self.assertEqual(element.to_json(), expected_json_string)

        element2 = Element.hierarchy_from_json(expected_json_string)
        self.assertIsInstance(element2, Section)
        self.assertEqual(element2.offset, 27)
        self.assertEqual(element2.bytes, b'world')

    def test_abstract_element(self):
        element = Element()

        with self.assertRaises(NotImplementedError):
            Element.from_data({})

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

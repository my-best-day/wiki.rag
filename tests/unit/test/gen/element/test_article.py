import unittest
from typing import Iterator
from gen.element.paragraph import Paragraph
from gen.element.article import Article
from gen.element.flat.flat_article import FlatArticle
from gen.element.header import Header
from gen.element.element import Element

from ...xutils.byte_reader_tst import TestByteReader


class TestArticle(unittest.TestCase):

    def setUp(self):
        header = Header(17, b'hello')
        self.article = Article(header)
        paragraph1 = Paragraph(22, b'world', self.article)
        paragraph2 = Paragraph(30, b'dear', self.article)
        self.elements = [header, paragraph1, paragraph2]

        _bytes = b'h\xc3\xa9llo!'
        header = Header(23, _bytes)
        self.dirty = Article(header)
        paragraph1 = Paragraph(28, _bytes, self.dirty)
        paragraph2 = Paragraph(37, _bytes, self.dirty)
        self.dirty_elements = [header, paragraph1, paragraph2]

    def test_constructor(self):
        self.assertEqual(self.article.header, self.elements[0])
        self.assertEqual(self.article.paragraph_count, 2)
        paragraphs = list(self.article.paragraphs)
        self.assertEqual(paragraphs[0], self.elements[1])
        self.assertEqual(paragraphs[1], self.elements[2])
        self.assertEqual(self.article.element_count, 3)

    def test_elements_and_append_element(self):
        self.assertEqual(list(self.article.elements), self.elements)

    def test_offset(self):
        self.assertEqual(self.article.offset, self.elements[0].offset)

        article = Article(self.elements[0])
        article.append_paragraph(self.elements[1])
        self.assertEqual(article.offset, self.elements[0].offset)

        article.append_paragraph(self.elements[2])
        self.assertEqual(article.offset, self.elements[0].offset)

    def test_text(self):
        self.assertEqual(
            self.article.text,
            ''.join([p.text for p in self.elements])
        )

    def test_clean_text(self):
        self.assertEqual(
            self.article.clean_text,
            ''.join([p.clean_text for p in self.elements])
        )

    def test_byte_length(self):
        self.assertEqual(
            self.dirty.byte_length,
            sum([p.byte_length for p in self.dirty_elements])
        )

    def test_char_length(self):
        self.assertEqual(
            self.dirty.char_length,
            sum([p.char_length for p in self.dirty_elements])
        )

    def test_clean_length(self):
        self.assertEqual(
            self.dirty.clean_length,
            sum([p.clean_length for p in self.dirty_elements])
        )

    def test_append_bytes_and_reset(self):
        self.elements[0].append_bytes(b' <<sweet>> ')
        self.assertEqual(self.article.text, 'hello <<sweet>> worlddear')
        self.assertEqual(self.article.clean_text, 'hello sweet worlddear')

    def test_elements_property_returns_iterator(self):
        self.assertIsInstance(self.article.elements, Iterator)

    def test_append_non_element(self):
        with self.assertRaises(AssertionError):
            self.article.append_element("not an element")

    def test_offset_with_empty_container(self):
        with self.assertRaises(AssertionError):
            Article(Header(None, b''))

    def test_bytes_property(self):
        self.assertEqual(self.article.bytes, b'helloworlddear')

    def test_reset_clears_cache(self):
        # Access properties to populate cache
        _ = self.article.bytes
        _ = self.article.text
        _ = self.article.clean_text

        # Modify an element directly (not recommended in practice)
        self.elements[0]._bytes = b'modified'

        # Reset the container
        self.article.reset()

        # Check if cache is cleared
        self.assertEqual(self.article.bytes, b'modifiedworlddear')
        self.assertEqual(self.article.text, 'modifiedworlddear')
        self.assertEqual(self.article.clean_text, 'modifiedworlddear')

    def test_to_flat_article(self):
        flat_article = self.article.to_flat_article()
        test_byte_reader = TestByteReader.from_element(self.article)
        flat_article._byte_reader = test_byte_reader
        self.assertEqual(flat_article.uid, self.article.uid)
        self.assertEqual(flat_article.offset, self.article.offset)
        self.assertEqual(flat_article.bytes, self.article.bytes)
        self.assertEqual(flat_article.text, self.article.text)
        self.assertEqual(flat_article.clean_text, self.article.clean_text)
        self.assertEqual(flat_article.byte_length, self.article.byte_length)
        self.assertEqual(flat_article.char_length, self.article.char_length)
        self.assertEqual(flat_article.clean_length, self.article.clean_length)

        self.assertEqual(flat_article.header.text, self.article.header.text)
        self.assertEqual(flat_article.header.offset, self.article.header.offset)
        self.assertEqual(flat_article.header.byte_length, self.article.header.byte_length)
        self.assertEqual(flat_article.header.char_length, self.article.header.char_length)

        self.assertEqual(flat_article.body.text, self.article.body.text)
        self.assertEqual(flat_article.body.offset, self.article.body.offset)
        self.assertEqual(flat_article.body.byte_length, self.article.body.byte_length)
        self.assertEqual(flat_article.body.char_length, self.article.body.char_length)

        xdata = flat_article.to_xdata()
        Element.instances.clear()
        flat_article = FlatArticle.from_xdata(xdata, test_byte_reader)
        self.assertEqual(flat_article.uid, self.article.uid)

        self.assertEqual(flat_article.header.offset, self.article.header.offset)
        self.assertEqual(flat_article.header.byte_length, self.article.header.byte_length)

        self.assertEqual(flat_article.body.offset, self.article.body.offset)
        self.assertEqual(flat_article.body.byte_length, self.article.body.byte_length)


if __name__ == '__main__':
    unittest.main()

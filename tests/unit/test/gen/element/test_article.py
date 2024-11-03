import unittest
from typing import Iterator
from gen.element.paragraph import Paragraph
from gen.element.article import Article
from gen.element.header import Header


class TestArticle(unittest.TestCase):

    def setUp(self):
        self.paragraphs = [
            Header(17, b'hello'),
            Paragraph(23, b'world'),
            Paragraph(31, b'dear'),
        ]
        self.article = Article(self.paragraphs[0])
        for paragraph in self.paragraphs[1:]:
            self.article.append_paragraph(paragraph)

        _bytes = b'h\xc3\xa9llo!'
        self.dirty_paragraphs = [
            Header(23, _bytes),
            Paragraph(28, _bytes),
            Paragraph(37, _bytes),
        ]
        self.dirty = Article(self.dirty_paragraphs[0])
        for dirty_paragraph in self.dirty_paragraphs[1:]:
            self.dirty.append_element(dirty_paragraph)

    def test_constructor(self):
        self.assertEqual(self.article.header, self.paragraphs[0])
        self.assertEqual(list(self.article.paragraphs), self.paragraphs[1:])

    def test_elements_and_append_element(self):
        self.assertEqual(list(self.article.elements), self.paragraphs)

    def test_offset(self):
        self.assertEqual(self.article.offset, self.paragraphs[0].offset)

        article = Article(self.paragraphs[0])
        article.append_paragraph(self.paragraphs[1])
        self.assertEqual(article.offset, self.paragraphs[0].offset)

        article.append_paragraph(self.paragraphs[2])
        self.assertEqual(article.offset, self.paragraphs[0].offset)

    def test_text(self):
        self.assertEqual(
            self.article.text,
            ''.join([p.text for p in self.paragraphs])
        )

    def test_clean_text(self):
        self.assertEqual(
            self.article.clean_text,
            ''.join([p.clean_text for p in self.paragraphs])
        )

    def test_byte_length(self):
        self.assertEqual(
            self.dirty.byte_length,
            sum([p.byte_length for p in self.dirty_paragraphs])
        )

    def test_char_length(self):
        self.assertEqual(
            self.dirty.char_length,
            sum([p.char_length for p in self.dirty_paragraphs])
        )

    def test_clean_length(self):
        self.assertEqual(
            self.dirty.clean_length,
            sum([p.clean_length for p in self.dirty_paragraphs])
        )

    def test_append_bytes_and_reset(self):
        self.paragraphs[0].append_bytes(b' <<sweet>> ')
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
        self.paragraphs[0]._bytes = b'modified'

        # Reset the container
        self.article.reset()

        # Check if cache is cleared
        self.assertEqual(self.article.bytes, b'modifiedworlddear')
        self.assertEqual(self.article.text, 'modifiedworlddear')
        self.assertEqual(self.article.clean_text, 'modifiedworlddear')


if __name__ == '__main__':
    unittest.main()

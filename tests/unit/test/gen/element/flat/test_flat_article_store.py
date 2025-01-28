import unittest
from pathlib import Path
from unittest.mock import patch

from gen.element.store import Store
from gen.element.element import Element
from gen.element.flat.flat_article import FlatArticle
from gen.element.flat.flat_article_store import FlatArticleStore

from ....xutils.byte_reader_tst import TestByteReader


class TestFlatArticleStore(unittest.TestCase):

    # uid: UUID,
    # header_offset: int,
    # header_byte_length: int,
    # body_offset: int,
    # body_byte_length: int,
    # byte_reader: ByteReader
    def setUp(self):
        self.byte_reader = TestByteReader(
            b'= header =\nbody of evidence\n= header2 =\nproof of evidence\n'
        )
        self.flat_article0 = FlatArticle(0, 0, 11, 11, 17, self.byte_reader)
        self.flat_article1 = FlatArticle(1, 28, 12, 40, 18, self.byte_reader)
        self.flat_articles = [self.flat_article0, self.flat_article1]
        self.store = Store()

    @patch.object(Store, 'load_elements_byte_reader')
    def test_read_flat_articles(self, mock_load_elements_byte_reader):

        def load_elements_byte_reader_side_effect(byte_reader, path):
            Element.instances = {fa.uid: fa for fa in self.flat_articles}

        mock_load_elements_byte_reader.side_effect = load_elements_byte_reader_side_effect

        flat_article_store = FlatArticleStore(
            '/dev/null/prefix',
            self.byte_reader,
            self.store
        )
        flat_articles = flat_article_store.load_flat_articles()
        self.assertEqual(flat_articles, self.flat_articles)
        self.assertEqual(flat_articles[0].header.bytes, b'= header =\n')
        self.assertEqual(flat_articles[0].body.bytes, b'body of evidence\n')
        self.assertEqual(flat_articles[1].header.bytes, b'= header2 =\n')
        self.assertEqual(flat_articles[1].body.bytes, b'proof of evidence\n')

        # to read flat articles, we need a byte reader
        flat_article_store = FlatArticleStore('/dev/null/prefix')
        with self.assertRaises(ValueError):
            flat_article_store.load_flat_articles()

    @patch.object(Store, 'store_elements')
    def test_write_flat_articles(self, mock_store_elements):
        flat_article_store_path = Path('/dev/null/prefix_flat_articles.json')
        flat_article_store = FlatArticleStore(
            '/dev/null/prefix',
            self.byte_reader,
            self.store
        )
        flat_article_store.write_flat_articles(self.flat_articles)
        mock_store_elements.assert_called_once()
        args, _ = mock_store_elements.call_args
        self.assertEqual(args[0], flat_article_store_path)
        self.assertEqual(args[1], self.flat_articles)


if __name__ == "__main__":
    unittest.main()

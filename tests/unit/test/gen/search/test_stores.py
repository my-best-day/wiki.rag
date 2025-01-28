import os
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from gen.element.element import Element
from search.stores import Stores
from gen.embedding_store import EmbeddingStore, StoreMode
from xutils.embedding_config import EmbeddingConfig
from ...xutils.byte_reader_tst import TestByteReader
from gen.data.segment_record_store import SegmentRecord


class TestFlatArticleStore:
    def __init__(self, articles):
        self.articles = articles
        self.load_flat_articles_call_counter = 0

    def load_flat_articles(self):
        self.load_flat_articles_call_counter += 1
        return self.articles


class TestSegmentRecordStore:
    def __init__(self, segment_records):
        self.segment_records = segment_records
        self.load_segment_records_call_counter = 0

    def load_segment_records(self):
        self.load_segment_records_call_counter += 1
        return self.segment_records


class TestEmbeddingStore:
    def __init__(self, uids_and_embeddings):
        self.uids_and_embeddings = uids_and_embeddings
        self.load_embeddings_call_counter = 0

    def load_embeddings(self):
        self.load_embeddings_call_counter += 1
        return self.uids_and_embeddings


class TestStores(unittest.TestCase):

    def create_stores(
        self,
        text_byte_reader=None ,
        segment_record_store=None,
        flat_article_store=None,
        embedding_store=None
    ):
        if text_byte_reader is None:
            text_byte_reader = MagicMock()
        if flat_article_store is None:
            flat_article_store = MagicMock()
        if segment_record_store is None:
            segment_record_store = MagicMock()
        if embedding_store is None:
            embedding_store = MagicMock()

        stores = Stores(
            text_byte_reader,
            flat_article_store,
            segment_record_store,
            embedding_store
        )
        return stores

    def setUp(self):
        self.embedding_config = EmbeddingConfig('path_prefix', 1)

        self.mock_article0 = MagicMock()
        self.mock_article1 = MagicMock()
        self.mock_article2 = MagicMock()
        self.mock_articles = [self.mock_article0, self.mock_article1, self.mock_article2]

        self.segment_record0 = SegmentRecord(0, 0, 0, 0, 0)
        self.segment_record1 = SegmentRecord(1, 0, 1, 0, 0)
        self.segment_record2 = SegmentRecord(2, 1, 0, 0, 0)
        self.segment_record3 = SegmentRecord(3, 2, 0, 0, 0)
        self.segment_record4 = SegmentRecord(4, 2, 1, 0, 0)
        self.segment_records = \
            [self.segment_record0, self.segment_record1, self.segment_record2,
             self.segment_record3, self.segment_record4]

        self.mock_uids = [0, 0, 1, 2, 2]
        self.mock_embeddings = np.array(
            [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8], [0.9, 1.0]])
        self.mock_uids_and_embeddings = (self.mock_uids, self.mock_embeddings)

    @patch('search.stores.EmbeddingStore', autospec=True)
    def test_create_stores(self, mock_embedding_store):
        text_file_path = '/dev/null/text.txt'
        embedding_config = self.embedding_config

        # Set up the mock EmbeddingStore
        embedding_store_path_str = EmbeddingStore.get_store_path(embedding_config)
        embedding_store_path = Path(embedding_store_path_str)
        mock_embedding_store.get_store_path.return_value = embedding_store_path_str
        mock_embedding_store_instance = mock_embedding_store.return_value

        # Execute the test
        stores = Stores.create_stores(
            text_file_path,
            embedding_config
        )

        # Assertions
        self.assertIsInstance(stores, Stores)
        self.assertEqual(stores.text_byte_reader.path, text_file_path)
        path = str(stores.flat_article_store.flat_article_store_path)
        prefix = embedding_config.prefix
        self.assertTrue(path.startswith(prefix))

        # Ensure the mock was used
        mock_embedding_store.assert_called_once_with(
            path=embedding_store_path,
            mode=StoreMode.READ,
            allow_empty=False
        )
        self.assertEqual(stores.embedding_store, mock_embedding_store_instance)

    @patch('logging.Logger.info')
    def test_background_load_not_called(self, _):
        """
        tests that background_load is not called when UNIT_TESTING is set to 1
        tests that background_load is called when UNIT_TESTING is set to 0
        # TODO: this needs to be improve to test the side effect - if data is loaded,
        # TODO: rather than just checking that the methods are called
        """
        with patch('search.stores.Thread') as mock_thread:
            with patch.dict(os.environ, {"UNIT_TESTING": "1"}):
                stores = self.create_stores()
                stores.background_load()

                mock_thread.assert_not_called()

    def test_background_load_called(self):
        with patch('search.stores.Thread') as mock_thread:
            with patch("search.stores.RLock") as mock_rlock:
                with patch.dict(os.environ, {"UNIT_TESTING": "0"}):
                    mock_thread_instance = MagicMock()
                    mock_thread.return_value = mock_thread_instance

                    def start_side_effect():
                        _, argv = mock_thread.call_args
                        target = argv['target']
                        target()

                    mock_thread_instance.start.side_effect = start_side_effect

                    stores = self.create_stores()
                    stores.background_load()

                    mock_thread.assert_called_once()
                    mock_thread_instance.start.assert_called_once()

                    stores.flat_article_store.load_flat_articles.assert_called_once()
                    stores.segment_record_store.load_segment_records.assert_called_once()
                    stores.embedding_store.load_embeddings.assert_called_once()

                    mock_rlock_instance = mock_rlock.return_value
                    expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                    self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

    def test_get_segment_text(self):
        """test that the stores' byte reader is used using the segment record's offset and length"""
        test_text_byte_reader = TestByteReader(b'0123456789')
        segment_record = SegmentRecord(1, 0, 1, 3, 4)
        stores = self.create_stores(test_text_byte_reader)
        text = stores.get_segment_text(segment_record)
        self.assertEqual(text, '3456')

    def test_get_article_by_index(self):
        stores = self.create_stores()
        stores._articles = self.mock_articles

        article = stores.get_article_by_index(1)
        self.assertEqual(article, self.mock_article1)

        article = stores.get_article_by_index(2)
        self.assertEqual(article, self.mock_article2)

        article = stores.get_article_by_index(0)
        self.assertEqual(article, self.mock_article0)

    def test_get_segment_record_by_index(self):
        """test that the stores' segment records are used using the segment record index"""
        stores = self.create_stores()
        stores._segment_records = self.segment_records

        segment_record = stores.get_segment_record_by_index(1)
        self.assertEqual(segment_record, self.segment_record1)

        segment_record = stores.get_segment_record_by_index(2)
        self.assertEqual(segment_record, self.segment_record2)

        segment_record = stores.get_segment_record_by_index(0)
        self.assertEqual(segment_record, self.segment_record0)

    def test_get_embeddings_article_indexes(self):
        """test that the stores' embeddings article indexes are used"""
        stores = self.create_stores()
        stores._segment_records = self.segment_records
        article_indexes = stores.get_embeddings_article_indexes()
        self.assertEqual(article_indexes, self.mock_uids)

    def test_articles_empty(self):
        """
        when _articles is None, the lock is used and the output of
        _load_flat_articles is set to _articles
        """
        Element.instances.clear()
        with patch("search.stores.RLock") as mock_rlock:
            # when _load_flat_articles is called, it sets _articles to mock_articles
            flat_article_store = TestFlatArticleStore(self.mock_articles)
            stores = self.create_stores(flat_article_store=flat_article_store)

            # assert we start from a clean state
            self.assertIsNotNone(Element.instances)
            self.assertIsNone(stores._articles)

            # expect the lock to be used and the output of _load_flat_articles to be set
            articles = stores.articles
            mock_rlock_instance = mock_rlock.return_value
            expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
            self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)
            self.assertIs(articles, self.mock_articles)

    def test_articles_not_empty(self):
        """
        when _articles is not None, the lock is not not used and the output of
        _load_flat_articles is not used
        """
        Element.instances.clear()
        with patch.object(Stores, '_load_flat_articles', return_value=None) \
                as mock_load_flat_articles:
            with patch("search.stores.RLock") as mock_rlock:
                mock_load_flat_articles.side_effect = \
                    lambda: setattr(stores, '_articles', None)

                stores = self.create_stores()
                stores._articles = self.mock_articles

                # Call the articles property to trigger the loading again
                articles = stores.articles

                # Assert that the articles returned are the same as the first call
                self.assertIs(articles, self.mock_articles)

                # Assert that the lock was not used
                mock_rlock_instance = mock_rlock.return_value
                mock_rlock_instance.assert_not_called()
                # Ensure it was not called again
                mock_load_flat_articles.assert_not_called()

    def test_articles_double_lock(self):
        """
        _articles is None, the lock is used, _articles is set when the lock is captured and
        so _load_flat_articles is not called
        """
        Element.instances.clear()
        with patch.object(Stores, '_load_flat_articles', return_value=None) \
                as mock_load_flat_articles:
            with patch("search.stores.RLock") as mock_rlock:
                # when the lock is capture, set _articles
                mock_rlock_instance = mock_rlock.return_value
                mock_rlock_instance.__enter__.side_effect = \
                    lambda: setattr(stores, '_articles', self.mock_articles)

                # we hope this is not called
                mock_load_flat_articles.side_effect = \
                    lambda: setattr(stores, '_articles', None)

                stores = self.create_stores()
                # start from a clean state
                self.assertIsNotNone(Element.instances)
                self.assertIsNone(stores._articles)

                articles = stores.articles

                mock_rlock_instance = mock_rlock.return_value
                expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

                mock_load_flat_articles.assert_not_called()

                self.assertIs(articles, self.mock_articles)

    def test_segment_records_empty(self):
        """
        when _segment_records is None, the lock is used and the output of
        _load_segment_records is set to _segment_records
        """
        with patch("search.stores.RLock") as mock_rlock:
            segment_record_store = TestSegmentRecordStore(self.segment_records)
            stores = self.create_stores(segment_record_store=segment_record_store)

            # start from a clean state
            self.assertIsNotNone(Element.instances)
            self.assertIsNone(stores._segment_records)

            segment_records = stores.segment_records

            mock_rlock_instance = mock_rlock.return_value
            expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
            self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)
            self.assertIs(segment_records, self.segment_records)

    def test_segment_records_not_empty(self):
        """
        when _segment_records is not None, the lock is not not used and the output of
        _load_segment_records is not used
        """
        with patch("search.stores.RLock") as mock_rlock:
            segment_record_store = TestSegmentRecordStore(self.segment_records)
            stores = self.create_stores(segment_record_store=segment_record_store)

            stores._segment_records = self.segment_records

            segment_records = stores.segment_records
            self.assertIs(segment_records, self.segment_records)
            mock_rlock_instance = mock_rlock.return_value
            mock_rlock_instance.assert_not_called()
            self.assertEqual(segment_record_store.load_segment_records_call_counter, 0)

    def test_segment_records_double_lock(self):
        """
        _segment_records is None, the lock is used, _segment_records is set when the lock is
        captured and so _load_segment_records is not called
        """
        with patch("search.stores.RLock") as mock_rlock:
            segment_record_store = TestSegmentRecordStore(self.segment_records)
            stores = self.create_stores(segment_record_store=segment_record_store)

            # start from a clean state
            self.assertIsNotNone(Element.instances)
            self.assertIsNone(stores._segment_records)

            mock_rlock_instance = mock_rlock.return_value
            mock_rlock_instance.__enter__.side_effect = \
                lambda: setattr(stores, '_segment_records', self.segment_records)

            segment_records = stores.segment_records
            self.assertIs(segment_records, self.segment_records)
            mock_rlock_instance.assert_not_called()
            self.assertEqual(segment_record_store.load_segment_records_call_counter, 0)

    def test_uids_and_embeddings_empty(self):
        """
        when _uids_and_embeddings is None, the lock is used and the output of
        _load_uids_and_embeddings is set to _uids_and_embeddings
        """
        with patch("search.stores.RLock") as mock_rlock:
            embedding_store = TestEmbeddingStore(self.mock_uids_and_embeddings)
            stores = self.create_stores(embedding_store=embedding_store)

            # start from a clean state
            self.assertIsNotNone(Element.instances)
            self.assertIsNone(stores._uids_and_embeddings)

            uids_and_embeddings = stores.uids_and_embeddings

            mock_rlock_instance = mock_rlock.return_value
            expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
            self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)
            self.assertIs(uids_and_embeddings, self.mock_uids_and_embeddings)

    def test_uids_and_embeddings_not_empty(self):
        """
        when _uids_and_embeddings is not None, the lock is not not used and the output of
        _load_uids_and_embeddings is not used
        """
        with patch("search.stores.RLock") as mock_rlock:
            embedding_store = TestEmbeddingStore(None)
            stores = self.create_stores(embedding_store=embedding_store)
            stores._uids_and_embeddings = self.mock_uids_and_embeddings

            uids_and_embeddings = stores.uids_and_embeddings
            self.assertIs(uids_and_embeddings, self.mock_uids_and_embeddings)
            mock_rlock_instance = mock_rlock.return_value
            mock_rlock_instance.assert_not_called()
            self.assertEqual(embedding_store.load_embeddings_call_counter, 0)

    def test_uids_and_embeddings_double_lock(self):
        """
        _uids_and_embeddings is None, the lock is used, _uids_and_embeddings is set when the lock is
        captured and so _load_uids_and_embeddings is not called
        """
        with patch("search.stores.RLock") as mock_rlock:
            embedding_store = TestEmbeddingStore(None)
            stores = self.create_stores(embedding_store=embedding_store)

            # start from a clean state
            self.assertIsNotNone(Element.instances)
            self.assertIsNone(stores._uids_and_embeddings)

            mock_rlock_instance = mock_rlock.return_value
            mock_rlock_instance.__enter__.side_effect = \
                lambda: setattr(stores, '_uids_and_embeddings', self.mock_uids_and_embeddings)

            uids_and_embeddings = stores.uids_and_embeddings
            self.assertIs(uids_and_embeddings, self.mock_uids_and_embeddings)
            mock_rlock_instance.assert_not_called()
            self.assertEqual(embedding_store.load_embeddings_call_counter, 0)

    def test_protected_load_flat_articles(self):
        test_flat_article_store = TestFlatArticleStore(self.mock_articles)

        stores = self.create_stores(flat_article_store=test_flat_article_store)

        self.assertIsNone(stores._articles)
        stores._load_flat_articles()
        self.assertIs(stores._articles, self.mock_articles)

    def test_protected_load_segment_records(self):
        test_segment_record_store = TestSegmentRecordStore(self.segment_records)

        stores = self.create_stores(segment_record_store=test_segment_record_store)
        self.assertIsNone(stores._segment_records)
        stores._load_segment_records()
        self.assertIs(stores._segment_records, self.segment_records)

    def test_protected_load_uids_and_embeddings(self):
        embedding_store = TestEmbeddingStore(self.mock_uids_and_embeddings)
        stores = self.create_stores(embedding_store=embedding_store)
        stores._load_uids_and_embeddings()
        self.assertIs(stores._uids_and_embeddings, self.mock_uids_and_embeddings)


if __name__ == '__main__':
    unittest.main()

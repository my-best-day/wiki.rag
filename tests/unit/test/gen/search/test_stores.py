import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from gen.element.element import Element
from gen.element.section import Section
from gen.element.article import Article
from gen.element.header import Header
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment
from gen.search.stores import Stores


class TestStores(unittest.TestCase):

    @patch('logging.Logger.info')
    def test_background_load(self, _):
        with patch('gen.search.stores.Thread') as mock_thread:
            with patch('gen.search.stores.Stores._load_segments') as mock_load_segments:
                with patch('gen.search.stores.Stores._load_embeddings') as mock_load_embeddings:
                    with patch('gen.search.stores.RLock') as mock_rlock:

                        mock_thread_instance = MagicMock()
                        mock_thread.return_value = mock_thread_instance

                        def start_side_effect():
                            _, argv = mock_thread.call_args
                            target = argv['target']
                            target()

                        mock_thread_instance.start.side_effect = start_side_effect

                        stores = Stores('text_file_path', 'path_prefix', 1)
                        stores.background_load()

                        mock_thread.assert_called_once()
                        mock_thread_instance.start.assert_called_once()

                        mock_load_segments.assert_called_once()
                        mock_load_embeddings.assert_called_once()

                        mock_rlock_instance = mock_rlock.return_value
                        expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                        self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

    def test_protected_load_segments(self):
        with patch("gen.search.stores.Store") as mock_store:
            mock_store_instance = MagicMock()
            mock_store.return_value = mock_store_instance
            mock_store_instance.load_elements = MagicMock()
            stores = Stores('text_file_path', 'path_prefix', 1)
            stores._segments_loaded = True
            stores._load_segments()
            self.assertFalse(mock_store_instance.load_elements.called)

            stores._segments_loaded = False
            stores._load_segments()
            self.assertTrue(stores._segments_loaded)
            mock_store_instance.load_elements.assert_called_once()
            args, _ = mock_store_instance.load_elements.call_args
            self.assertEqual(args, (Path('text_file_path'), Path('path_prefix_1_segments.json')))

    def test_protected_load_embeddings(self):
        with patch("gen.search.stores.EmbeddingStore") as mock_embedding_store:
            mock_embedding_store_instance = MagicMock()
            mock_embedding_store.return_value = mock_embedding_store_instance
            mock_embedding_store_instance.load_embeddings = MagicMock()
            mock_embedding_store_instance.load_embeddings.return_value = (['uids'], ['embeddings'])
            stores = Stores('text_file_path', 'path_prefix', 1)
            stores._embeddings = 'embeddings'
            stores._load_embeddings()

            self.assertFalse(mock_embedding_store_instance.load_embeddings.called)

            stores._embeddings = None
            stores._load_embeddings()
            self.assertIsNotNone(stores._embeddings)
            mock_embedding_store_instance.load_embeddings.assert_called_once()

    def test_embeddings(self):
        with patch("gen.search.stores.Stores._load_embeddings") as mock_load_embeddings:
            with patch("gen.search.stores.RLock") as mock_rlock:

                stores = Stores('text_file_path', 'path_prefix', 1)
                self.assertIsNone(stores._uids)
                self.assertIsNone(stores._embeddings)

                stores._uids = ['uids']
                stores._embeddings = ['embeddings']
                uids, embeddings = stores.embeddings

                mock_rlock_instance = mock_rlock.return_value
                expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

                mock_load_embeddings.assert_called_once()
                self.assertEqual(uids, ['uids'])
                self.assertEqual(embeddings, ['embeddings'])

    def test_extended_segments(self):
        Element.instances.clear()
        with patch("gen.search.stores.Stores._load_segments") as mock_load_segments:
            with patch("gen.search.stores.RLock") as mock_rlock:

                stores = Stores('text_file_path', 'path_prefix', 1)
                self.assertIsNone(stores._extended_segments)

                header = Header(14, b'header', 'header_uid')
                section = Section(20, b'section', 'section_uid')
                article = Article(header, 'article_uid')
                segment = Segment(article, section, 'seg_uid')
                extended_segment = ExtendedSegment(segment, 'extended_segment_uid')

                Element.instances.update({
                    header.uid: header,
                    article.uid: article,
                    segment.uid: segment,
                    extended_segment.uid: extended_segment
                })

                extended_segments = stores.extended_segments

                mock_rlock_instance = mock_rlock.return_value
                expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

                mock_load_segments.assert_called_once()
                self.assertEqual(extended_segments, [extended_segment])

                extended_segments = stores.extended_segments
                mock_load_segments.assert_called_once()
                self.assertEqual(extended_segments, [extended_segment])

    def test_articles(self):
        Element.instances.clear()
        with patch("gen.search.stores.Stores._load_segments") as mock_load_segments:
            with patch("gen.search.stores.RLock") as mock_rlock:

                stores = Stores('text_file_path', 'path_prefix', 1)
                self.assertIsNotNone(Element.instances)
                self.assertIsNone(stores._articles)

                header = Header(14, b'header', 'header_uid')
                section = Section(20, b'section', 'section_uid')
                article = Article(header, 'article_uid')
                segment = Segment(article, section, 'seg_uid')
                extended_segment = ExtendedSegment(segment, 'extended_segment_uid')

                # FIXME: this is not needed, rid of it
                Element.instances.update({
                    header.uid: header,
                    article.uid: article,
                    segment.uid: segment,
                    extended_segment.uid: extended_segment
                })

                articles = stores.articles

                mock_rlock_instance = mock_rlock.return_value
                expected_calls = [call.__enter__(), call.__exit__(None, None, None)]
                self.assertEqual(mock_rlock_instance.mock_calls, expected_calls)

                mock_load_segments.assert_called_once()
                self.assertEqual(articles, [article])

                articles = stores.articles
                mock_load_segments.assert_called_once()
                self.assertEqual(articles, [article])

    def test_get_article(self):
        header = Header(14, b'header', 'header_uid')
        article = Article(header, 'article_uid')

        stores = Stores('text_file_path', 'path_prefix', 1)
        Element.instances.update({
            article.uid: article
        })
        article2 = stores.get_article('article_uid')
        self.assertIs(article, article2)

    def test_get_embeddings_article_ids(self):
        extended_segments = []

        header = Header(14, b'header', 'header_uid1')
        section = Section(20, b'section', 'section_uid1')
        article = Article(header, 'article_uid1')
        segment = Segment(article, section, 'seg_uid1')
        extended_segment = ExtendedSegment(segment, 'extended_segment_uid1')
        extended_segments.append(extended_segment)

        header = Header(14, b'header', 'header_uid2')
        section = Section(20, b'section', 'section_uid2')
        article = Article(header, 'article_uid2')
        segment = Segment(article, section, 'seg_uid2')
        extended_segment = ExtendedSegment(segment, 'extended_segment_uid2')
        extended_segments.append(extended_segment)

        stores = Stores('text_file_path', 'path_prefix', 1)
        stores._extended_segments = extended_segments
        article_uids = stores.get_embeddings_article_ids()
        self.assertEqual(article_uids, ['article_uid1', 'article_uid2'])


if __name__ == '__main__':
    unittest.main()

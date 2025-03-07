import os
import unittest
import numpy as np
import numpy.testing as npt
from unittest.mock import MagicMock, patch, PropertyMock
from search.k_nearest_finder import KNearestFinder
from xutils.embedding_config import EmbeddingConfig


class TestKNearestFinder(unittest.TestCase):

    def setUp(self):
        # stops Encoders from proactively loading the model
        os.environ['UNIT_TESTING'] = '1'
        self.embed_config = EmbeddingConfig(
            prefix='path_prefix',
            max_len=1,
            l2_normalize=True
        )

    # mock encoder so we do not load the actual model
    @patch('search.k_nearest_finder.Stores')
    @patch('search.k_nearest_finder.Encoder')
    def test_uids_and_embeddings(self, mock_encoder, mock_stores):
        uids = ['uid1', 'uid2']
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])

        mock_stores_instance = MagicMock()
        mock_stores_instance.uids_and_embeddings = (uids, embeddings)
        mock_stores.return_value = mock_stores_instance

        k_nearest_finder = KNearestFinder(mock_stores_instance, self.embed_config)
        self.assertIsNone(k_nearest_finder._uids)
        self.assertIsNone(k_nearest_finder._embeddings)
        uids2, embeddings2 = k_nearest_finder.uids_and_embeddings
        npt.assert_array_equal(embeddings2, embeddings)

        uids3, embeddings3 = k_nearest_finder.uids_and_embeddings
        self.assertIs(uids3, uids2)
        self.assertIs(embeddings3, embeddings2)

    @patch('search.k_nearest_finder.EmbeddingUtils.morph_embeddings')
    @patch.object(KNearestFinder, 'uids_and_embeddings', new_callable=PropertyMock)
    def test_uids_and_normalized_embeddings(self, mock_uids_and_embeddings, mock_morph_embeddings):
        uids = MagicMock()
        embeddings = MagicMock()
        normalized_embeddings = MagicMock()

        mock_uids_and_embeddings.return_value = (uids, embeddings)
        mock_morph_embeddings.return_value = normalized_embeddings

        k_nearest_finder = KNearestFinder(MagicMock(), self.embed_config)
        k_nearest_finder._uids = uids
        self.assertIsNone(k_nearest_finder._normalized_embeddings)
        uids2, normalized_embeddings2 = k_nearest_finder.uids_and_normalized_embeddings
        mock_uids_and_embeddings.assert_called_once()
        mock_morph_embeddings.assert_called_once_with(embeddings, self.embed_config)
        self.assertIs(uids2, uids)
        self.assertIs(normalized_embeddings2, normalized_embeddings)

        uids5, normalized_embeddings5 = k_nearest_finder.uids_and_normalized_embeddings
        self.assertIs(uids5, uids)
        self.assertIs(normalized_embeddings5, normalized_embeddings)
        mock_morph_embeddings.assert_called_once_with(embeddings, self.embed_config)

    @patch('search.k_nearest_finder.Encoder')
    def test_find_k_nearest_segments(self, mock_encoder):
        query_embeddings = np.array([[0.1, 0.2, 0.3]])  # Shape (1, 3)
        embeddings = np.array([
            [0.6, 0.7, 0.8],
            [0.3, 0.4, 0.5],
            [0.1, 0.2, 0.4],
        ])  # Shape (3, 3)
        uids = [1, 2, 3]  # Simulated UUIDs

        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = query_embeddings
        mock_encoder.return_value = mock_encoder_instance

        query = "test query"

        # Instantiate the class with mocked encoder
        mock_stores_instance = MagicMock()
        finder = KNearestFinder(mock_stores_instance, self.embed_config)
        finder._uids = uids
        finder._embeddings = embeddings

        # Call the method
        result = finder.find_k_nearest_segments(query, k=2, threshold=0.99, max_results=2)

        # Assert the expected result
        expected_result = [[3 , 0.991460],
                           [2 , 0.982708]]
        npt.assert_array_almost_equal(result, expected_result)

        # Call the method
        result = finder.find_k_nearest_segments(query, k=1, threshold=0.98, max_results=2)
        npt.assert_array_almost_equal(result, expected_result)

    @patch('search.k_nearest_finder.Encoder')
    def test_find_k_nearest_articles(self, mock_encoder):
        query_embeddings = np.array([[0.1, 0.2, 0.3]])  # Shape (1, 3)
        embeddings = np.array([
            [0.6, 0.7, 0.8],
            [0.3, 0.4, 0.5],
            [0.1, 0.2, 0.4],
        ])  # Shape (3, 3)
        uids = [1, 2, 3]  # Simulated UUIDs

        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = query_embeddings
        mock_encoder.return_value = mock_encoder_instance

        query = "test query"

        # Instantiate the class with mocked encoder
        mock_stores_instance = MagicMock()
        mock_stores_instance.get_embeddings_article_indexes.return_value = uids
        finder = KNearestFinder(mock_stores_instance, self.embed_config)
        finder._uids = uids
        finder._embeddings = embeddings

        # Call the method
        result = finder.find_k_nearest_articles(query, k=2, threshold=0.99, max_results=2)

        # Assert the expected result
        expected_result = [[3 , 0.991460],
                           [2 , 0.982708]]
        npt.assert_array_almost_equal(result, expected_result)


if __name__ == '__main__':
    unittest.main()

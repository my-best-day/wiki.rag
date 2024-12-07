import os
import unittest
import numpy as np
import numpy.testing as npt
from unittest.mock import MagicMock, patch
from gen.search.k_nearest_finder import KNearestFinder


class TestKNearestFinder(unittest.TestCase):

    def setUp(self):
        # stops Encoders from proactively loading the model
        os.environ['UNIT_TESTING'] = '1'

    # mock encoder so we do not load the actual model
    @patch('gen.search.k_nearest_finder.Stores')
    @patch('gen.search.k_nearest_finder.Encoder')
    def test_uids_and_embeddings(self, mock_encoder, mock_stores):
        uids = ['uid1', 'uid2']
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])

        mock_stores_instance = MagicMock()
        mock_stores_instance.uids_and_embeddings = (uids, embeddings)
        mock_stores.return_value = mock_stores_instance

        k_nearest_finder = KNearestFinder(mock_stores_instance)
        self.assertIsNone(k_nearest_finder._uids)
        self.assertIsNone(k_nearest_finder._embeddings)
        uids2, embeddings2 = k_nearest_finder.uids_and_embeddings
        npt.assert_array_equal(embeddings2, embeddings)
        npt.assert_array_equal(embeddings2, embeddings)

        uids3, embeddings3 = k_nearest_finder.uids_and_embeddings
        self.assertIs(uids3, uids2)
        self.assertIs(embeddings3, embeddings2)

    @patch('gen.search.k_nearest_finder.Encoder')
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
        finder = KNearestFinder(mock_stores_instance)
        finder._uids = uids
        finder._embeddings = embeddings

        # Call the method
        result = finder.find_k_nearest_segments(query, k=2)

        # Assert the expected result
        expected_result = [[3 , 0.991460],
                           [2 , 0.982708]]
        npt.assert_array_almost_equal(result, expected_result)


if __name__ == '__main__':
    unittest.main()

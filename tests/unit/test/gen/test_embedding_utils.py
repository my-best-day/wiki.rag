import unittest

import numpy as np
import numpy.testing as npt
from unittest.mock import MagicMock, patch

import torch
import torch.nn.functional as F

from gen.embedding_utils import EmbeddingUtils
from xutils.embedding_config import EmbeddingConfig


class TestEmbeddingUtils(unittest.TestCase):

    @patch('gen.embedding_utils.EmbeddingUtils.reduce_dim')
    @patch('gen.embedding_utils.EmbeddingUtils.normalize_embeddings')
    @patch('gen.embedding_utils.EmbeddingUtils.quantize_embeddings')
    def test_morph_embeddings(self, mock_quantize_embeddings, mock_normalize_embeddings,
                              mock_reduce_dim):
        embeddings = MagicMock()

        prefix = "1"
        max_len = "2"
        dim = "3"
        stype = "4"
        norm_type = "5"
        l2_normalize = "6"

        embed_config = EmbeddingConfig(
            prefix=prefix,
            max_len=max_len,
            dim=dim,
            stype=stype,
            norm_type=norm_type,
            l2_normalize=l2_normalize
        )

        mock_reduce_dim.return_value = embeddings
        mock_normalize_embeddings.return_value = embeddings
        mock_quantize_embeddings.return_value = embeddings

        result = EmbeddingUtils.morph_embeddings(embeddings, embed_config)
        mock_reduce_dim.assert_called_once_with(embeddings, embed_config.dim)
        mock_normalize_embeddings.assert_called_once_with(embeddings, embed_config.l2_normalize,
                                                          embed_config.norm_type)
        mock_quantize_embeddings.assert_called_once_with(embeddings, embed_config.stype)
        self.assertIs(result, embeddings)

    def test_reduce_dim(self):
        embeddings = MagicMock()
        embeddings.shape = (2, 3)

        prefix = "1"
        max_len = "2"
        dim = None
        stype = "4"
        norm_type = "5"
        l2_normalize = "6"

        embed_config = EmbeddingConfig(
            prefix=prefix,
            max_len=max_len,
            dim=dim,
            stype=stype,
            norm_type=norm_type,
            l2_normalize=l2_normalize
        )
        result = EmbeddingUtils.reduce_dim(embeddings, embed_config.dim)
        self.assertIs(result, embeddings)

        embed_config.dim = 4
        with self.assertRaises(ValueError):
            EmbeddingUtils.reduce_dim(embeddings, embed_config.dim)

        embed_config.dim = 3
        result = EmbeddingUtils.reduce_dim(embeddings, embed_config.dim)
        self.assertIs(result, embeddings)

        embed_config.dim = 2
        embeddings = np.array([[2, 4, 8], [7, 8, 14]])
        mean = np.mean(embeddings, axis=1, keepdims=True)
        std = np.std(embeddings, axis=1, keepdims=True)
        normalized_embeddings = (embeddings - mean) / (std + 1e-5)  # avoid division by zero
        expected = normalized_embeddings[:, :2]
        reduced = EmbeddingUtils.reduce_dim(embeddings, embed_config.dim)
        npt.assert_array_equal(reduced, expected)

    def test_normalize_embeddings_noop(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        output1 = EmbeddingUtils.normalize_embeddings(embeddings, False, None)
        self.assertIs(output1, embeddings)

    def test_normalize_embeddings(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)

        output = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        expected = self.torch_normalize(embeddings, "float32")
        self.assertEqual(output.dtype, np.float32)
        npt.assert_array_almost_equal(output, expected)

    def test_normalize_embeddings_with_cast(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)

        output = EmbeddingUtils.normalize_embeddings(embeddings, True, np.float16)
        expected = self.torch_normalize(embeddings, "float16")
        npt.assert_array_almost_equal(output, expected)

    def test_normalize_embeddings_with_cast_batch(self):
        embeddings = np.array([[[1, 2, 3], [4, 5, 6]],
                               [[7, 8, 9], [10, 11, 12]]], dtype=np.float32)

        output = EmbeddingUtils.normalize_embeddings(embeddings, True, np.float16)
        expected = self.torch_normalize(embeddings, "float16")
        npt.assert_array_almost_equal(output, expected)

    def test_quantize_embeddings_noop(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        output = EmbeddingUtils.quantize_embeddings(embeddings, None)
        self.assertIs(output, embeddings)

    def test_quantize_embeddings_noop2(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        output = EmbeddingUtils.quantize_embeddings(embeddings, "float32")
        self.assertIs(output, embeddings)

    def test_quantize_embeddings_noop3(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float16)
        output = EmbeddingUtils.quantize_embeddings(embeddings, "float16")
        self.assertIs(output, embeddings)

    def test_quantize_embeddings_no_normalization(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        with self.assertRaises(ValueError):
            EmbeddingUtils.quantize_embeddings(embeddings, "float16")

    def test_quantize_embeddings_32(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        normalized = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        output = EmbeddingUtils.quantize_embeddings(normalized, "float32")

        normalized2 = self.torch_normalize(embeddings, "float32")
        expected = normalized2.astype(np.float32)
        npt.assert_array_almost_equal(output, expected)

    def test_quantize_embeddings_16(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        normalized = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        output = EmbeddingUtils.quantize_embeddings(normalized, "float16")

        normalized2 = self.torch_normalize(embeddings, "float32")
        expected = normalized2.astype(np.float16)
        npt.assert_array_almost_equal(output, expected)

    def test_quantize_embeddings_i8(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        normalized = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        output = EmbeddingUtils.quantize_embeddings(normalized, "int8")

        normalized2 = self.torch_normalize(embeddings, "float32")
        expected = np.round(normalized2 * 127).astype(np.int8)
        npt.assert_array_almost_equal(output, expected)

    def test_quantize_embeddings_u8(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        normalized = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        output = EmbeddingUtils.quantize_embeddings(normalized, "uint8")

        normalized2 = self.torch_normalize(embeddings, "float32")
        expected = np.round((normalized2 + 1) * 127.5).astype(np.uint8)
        npt.assert_array_almost_equal(output, expected)

    def test_quantize_embeddings_unknown(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        normalized = EmbeddingUtils.normalize_embeddings(embeddings, True, None)
        with self.assertRaises(ValueError):
            EmbeddingUtils.quantize_embeddings(normalized, "uint5")

    def test_get_stype(self):
        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        self.assertEqual(EmbeddingUtils.get_stype(embeddings), "float64")

        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        self.assertEqual(EmbeddingUtils.get_stype(embeddings), "float32")

        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float16)
        self.assertEqual(EmbeddingUtils.get_stype(embeddings), "float16")

        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int8)
        self.assertEqual(EmbeddingUtils.get_stype(embeddings), "int8")

        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
        self.assertEqual(EmbeddingUtils.get_stype(embeddings), "uint8")

        embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int16)
        with self.assertRaises(ValueError):
            EmbeddingUtils.get_stype(embeddings)

    @staticmethod
    def torch_normalize(embeddings, stype):
        tensor_batch = torch.from_numpy(embeddings.astype(stype)).to('cpu')
        normalized_batch = F.normalize(tensor_batch, p=2, dim=1)
        expected = normalized_batch.detach().numpy()
        return expected


if __name__ == '__main__':
    unittest.main()

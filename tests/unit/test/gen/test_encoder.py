import sys
import time
import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock, patch
from gen.encoder import Encoder, encoder_configs


class TestEncoder(unittest.TestCase):

    def test_init(self):
        batch_size = 31
        mock_model = Mock()
        with patch.object(Encoder, "get_model", return_value=mock_model):
            encoder = Encoder(batch_size)

            self.assertEqual(encoder.config, encoder_configs['small'])
            self.assertEqual(encoder.batch_size, batch_size)
            self.assertEqual(encoder.model, mock_model)

    def test_encode(self):
        batch_size = 31
        sentences = [["sent 1", "sent 2"]]
        mock_result = Mock()
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=mock_result)

        with patch.object(Encoder, "get_model", return_value=mock_model):
            encoder = Encoder(batch_size)
            result = encoder.encode(sentences)

            self.assertIs(result, mock_result)
            args, argv = mock_model.encode.call_args
            self.assertEqual(args[0], sentences)
            self.assertEqual(argv['batch_size'], batch_size)

    def test_get_model(self):
        mock_model = Mock()
        batch_size = 31
        encoder = Encoder(batch_size)
        with patch.object(encoder, "_get_model", return_value=mock_model):
            model = encoder.get_model()

            self.assertEqual(model, mock_model)

    @patch.dict("sys.modules", {"sentence_transformers": MagicMock()})
    @patch("torch.cuda.is_available", return_value=True)
    def test_protected_get_model(self, mock_cuda):
        t0 = time.time()
        mock_model = Mock()
        mock_sentence_transformer = MagicMock(return_value=mock_model)
        mock_sentence_transformers = sys.modules["sentence_transformers"]
        mock_sentence_transformers.SentenceTransformer = mock_sentence_transformer
        mock

        model_id = "model_id"

        encoder = Encoder(31)
        model = encoder._get_model(model_id)

        self.assertEqual(model, mock_model)
        mock_sentence_transformer.assert_called_once_with(
            model_name_or_path=model_id,
            device='cuda',
            trust_remote_code=True
        )
        t1 = time.time()
        print(f"Time to test protected get model: {(t1 - t0):.3f} sec")

    def test_get_device(self):
        with patch("torch.cuda.is_available", return_value=True):
            device = Encoder.get_device()
            self.assertEqual(device, "cuda")

        with patch("torch.cuda.is_available", return_value=False):
            device = Encoder.get_device()
            self.assertEqual(device, "cpu")


if __name__ == '__main__':
    unittest.main()

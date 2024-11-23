import unittest
from unittest.mock import Mock, MagicMock, patch
from gen.encoder import Encoder, encoder_configs


class TestEncoder(unittest.TestCase):

    def test_init(self):
        batch_size = 31
        mock_model = Mock()
        max_len = 128
        with patch.object(Encoder, "get_model", return_value=(mock_model, max_len)):
            encoder = Encoder(batch_size)

            self.assertEqual(encoder.config, encoder_configs['small'])
            self.assertEqual(encoder.batch_size, batch_size)
            self.assertEqual(encoder.model, mock_model)
            self.assertEqual(encoder.max_len, max_len)

    def test_encode(self):
        batch_size = 31
        sentences = [["sent 1", "sent 2"]]
        mock_result = Mock()
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=mock_result)
        max_len = 128

        with patch.object(Encoder, "get_model", return_value=(mock_model, max_len)):
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
        with patch("gen.encoder.SentenceTransformer", return_value=mock_model):
            model, max_len = encoder.get_model()

            self.assertEqual(model, mock_model)
            self.assertEqual(max_len, 256)

    def test_get_device(self):
        with patch("torch.cuda.is_available", return_value=True):
            device = Encoder.get_device()
            self.assertEqual(device, "cuda")

        with patch("torch.cuda.is_available", return_value=False):
            device = Encoder.get_device()
            self.assertEqual(device, "cpu")


if __name__ == '__main__':
    unittest.main()

import unittest
from io import BytesIO
from pathlib import Path
from xutils.byte_reader import ByteReader
from unittest.mock import mock_open, patch


class TestByteReader(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open)
    def test_byte_reader(self, mock_open):
        text_file = BytesIO(
            b'0123456789'
            + b'abcdefghij'
            + b'!@#$%^&*()'
            + b'\x41\xC3\xA9\xE2\x82\xAC')
        mock_open.return_value = text_file

        path = Path("/dev/null")

        byte_reader = ByteReader(path)
        _bytes = byte_reader.read_bytes(0, 12)
        self.assertEqual(_bytes, b'0123456789ab')
        _bytes = byte_reader.read_bytes(0, 12)
        self.assertEqual(_bytes, b'0123456789ab')
        _bytes = byte_reader.read_bytes(10, 12)
        self.assertEqual(_bytes, b'abcdefghij!@')
        _bytes = byte_reader.read_bytes(20, 12)
        self.assertEqual(_bytes, b'!@#$%^&*()\x41\xC3')
        _bytes = byte_reader.read_bytes(22, 12)
        self.assertEqual(_bytes, b'#$%^&*()\x41\xC3\xA9\xE2')
        _bytes = byte_reader.read_bytes(24, 12)
        self.assertEqual(_bytes, b'%^&*()\x41\xC3\xA9\xE2\x82\xAC')
        _bytes = byte_reader.read_bytes(0, 12)
        self.assertEqual(_bytes, b'0123456789ab')

    def test_cleanup(self):
        path = Path("/dev/null")

        byte_reader = ByteReader(path)
        byte_reader.cleanup()
        byte_reader.cleanup()


if __name__ == '__main__':
    unittest.main()

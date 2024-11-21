import argparse
import unittest
from unittest.mock import Mock

from attr import validate
from gen.element.section import Section
from gen.element_validator import ElementValidator
# relative import
from .element.byte_reader_tst import TestByteReader


class TestElementValidator(unittest.TestCase):
    def setUp(self):
        parser = argparse.ArgumentParser(description="unittest")
        parser.add_argument("--text", default="text.txt", type=str, help="Path to the text file")
        self.args = parser.parse_args(args=[])

    def test_byte_reader(self):
        validator = ElementValidator(self.args)
        self.assertIsNone(validator._byte_reader)
        validator.byte_reader
        self.assertIsNotNone(validator._byte_reader)

    def test_handle(self):
        validator = ElementValidator(self.args)
        validator.validate_element = Mock()
        validator.cleanup = Mock()
        validator.forward = Mock()

        section = Section(0, b'0123456789')
        validator.handle(section)
        validator.validate_element.assert_called_once_with(section)
        validator.cleanup.assert_not_called()
        validator.forward.assert_not_called()

        validator.validate_element.reset_mock()
        validator.handle(None)
        validator.validate_element.assert_not_called()
        validator.cleanup.assert_called_once()
        validator.forward.assert_called_once_with(None)

    def test_validate_element(self):
        byte_reader = TestByteReader(b'0123456789')
        section = Section(3, b'3456789')
        validator = ElementValidator(self.args)
        validator._byte_reader = byte_reader
        validator.forward = Mock()
        validator.validate_element(section)
        validator.forward.assert_called_once_with(section)

        # use very long bytes to test format_text
        section = Section(3, b'abcdefghij' * 50)
        validator.forward.reset_mock()
        with self.assertRaises(ValueError):
            validator.validate_element(section)

    def test_forward(self):
        validator = ElementValidator(self.args)

        next_handler = Mock()
        validator.chain(next_handler)
        validator.forward(self)
        next_handler.handle.assert_called_once_with(self)

    def test_cleanup(self):
        validator = ElementValidator(self.args)
        mock_reader = Mock()
        validator._byte_reader = mock_reader
        validator.cleanup()
        mock_reader.cleanup.assert_called_once()
        self.assertIsNone(validator._byte_reader)


if __name__ == '__main__':
    unittest.main()

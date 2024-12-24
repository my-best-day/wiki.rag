import argparse
import unittest
from unittest.mock import Mock

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

        section = Section(0, b'0123456789')
        validator.handle(section)
        validator.validate_element.assert_called_once_with(section)
        validator.cleanup.assert_not_called()

        validator.validate_element.reset_mock()
        validator.handle(None)
        validator.validate_element.assert_not_called()
        validator.cleanup.assert_called_once()

    def test_validate_element(self):
        byte_reader = TestByteReader(b'0123456789')
        section = Section(3, b'3456789')
        validator = ElementValidator(self.args)
        validator._byte_reader = byte_reader
        validator.validate_element(section)

        # use very long bytes to test format_text
        section = Section(3, b'abcdefghij' * 50)
        with self.assertRaises(ValueError):
            validator.validate_element(section)

    def test_validate_elements(self):
        byte_reader = TestByteReader(b'0123456789')
        section = Section(3, b'3456789')
        validator = ElementValidator(self.args)
        validator._byte_reader = byte_reader
        validator.handle = Mock()
        validator.validate_elements([section])
        # validate handles was called twice, once with section and once with None
        self.assertEqual(validator.handle.call_count, 2)
        validator.handle.assert_any_call(section)
        validator.handle.assert_any_call(None)

    def test_validate_elements_negative(self):
        byte_reader = TestByteReader(b'0123456789')
        section1 = Section(3, b'3456789')
        section2 = Section(3, b'abcdefghij' * 50)
        validator = ElementValidator(self.args)
        validator._byte_reader = byte_reader
        with self.assertRaises(ValueError):
            validator.validate_elements([section1, section2])

    def test_cleanup(self):
        validator = ElementValidator(self.args)
        mock_reader = Mock()
        validator._byte_reader = mock_reader
        validator.cleanup()
        mock_reader.cleanup.assert_called_once()
        self.assertIsNone(validator._byte_reader)

        # safe to call cleanup multiple times
        validator.cleanup()
        mock_reader.cleanup.assert_called_once()


if __name__ == '__main__':
    unittest.main()

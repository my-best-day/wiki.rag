import unittest
from gen.element.section import Section


class TestSection(unittest.TestCase):

    def create_section(self, offset: int, _bytes: bytes) -> Section:
        return Section(offset, _bytes)

    def test_constructor(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        self.assertEqual(section._offset, offset)
        self.assertEqual(section._bytes, _bytes)

    def test_offset(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        self.assertEqual(section.offset, offset)

    def test_text(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        self.assertEqual(section.text, 'héllo!')

    def test_bad_construction(self):
        offset = None
        _bytes = None

        # offset is None
        with self.assertRaises(AssertionError):
            self.create_section(offset, _bytes)  # NOSONAR

        # offset not an integer
        offset = '12'
        with self.assertRaises(AssertionError):
            self.create_section(offset, _bytes)  # NOSONAR

        # offset is negative
        offset = -1
        with self.assertRaises(AssertionError):
            self.create_section(offset, _bytes)  # NOSONAR

        # offset is valid, _bytes is None
        offset = 0
        with self.assertRaises(AssertionError):
            self.create_section(offset, _bytes)  # NOSONAR

        # _bytes is str, not bytes
        _bytes = ''
        with self.assertRaises(AssertionError):
            self.create_section(offset, _bytes)  # NOSONAR

        _bytes = b''
        section = self.create_section(offset, _bytes)  # NOSONAR

        self.assertEqual(section.offset, offset)
        self.assertEqual(section.bytes, _bytes)

    def test_clean_text(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)  # NOSONAR
        cleaned_text = section.clean_text
        self.assertEqual(cleaned_text, 'hello!')

        # check memoization
        self.assertIs(section.clean_text, cleaned_text)

    def test_byte_length(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)  # NOSONAR
        self.assertEqual(section.byte_length, len(_bytes))

    def test_char_length(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        self.assertEqual(section.char_length, len('héllo!'))

    def test_clean_length(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        self.assertEqual(section.clean_length, len('hello!'))

    def test_append_bytes_and_reset(self):
        offset = 23
        _bytes = b'h\xc3\xa9llo!'
        section = self.create_section(offset, _bytes)
        section.append_bytes(b'abc')
        self.assertEqual(section.offset, offset)
        self.assertEqual(section.bytes, b'h\xc3\xa9llo!abc')
        self.assertEqual(section.text, 'héllo!abc')
        self.assertEqual(section.clean_text, 'hello!abc')


if __name__ == '__main__':
    unittest.main()

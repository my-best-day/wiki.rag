import unittest
from gen.element.chunk import Chunk


class TestChunk(unittest.TestCase):

    def test_init(self):
        chunk = Chunk(10, b'hello')
        self.assertEqual(chunk.offset, 10)
        self.assertEqual(chunk.bytes, b'hello')

    def test_init_invalid_offset(self):
        with self.assertRaises(AssertionError):
            Chunk(-1, b'hello')

    def test_init_invalid_bytes(self):
        with self.assertRaises(AssertionError):
            Chunk(0, "not bytes")

    def test_offset_property(self):
        chunk = Chunk(5, b'world')
        self.assertEqual(chunk.offset, 5)

    def test_bytes_property(self):
        chunk = Chunk(0, b'test')
        self.assertEqual(chunk.bytes, b'test')

    def test_prepend_bytes(self):
        chunk = Chunk(10, b'world')
        chunk.prepend_bytes(b'hello ')
        self.assertEqual(chunk.offset, 4)
        self.assertEqual(chunk.bytes, b'hello world')

    def test_prepend_bytes_empty(self):
        chunk = Chunk(5, b'test')
        chunk.prepend_bytes(b'')
        self.assertEqual(chunk.offset, 5)
        self.assertEqual(chunk.bytes, b'test')

    def test_prepend_bytes_invalid_type(self):
        chunk = Chunk(0, b'test')
        with self.assertRaises(AssertionError):
            chunk.prepend_bytes("not bytes")

    def test_immutability_of_properties(self):
        chunk = Chunk(0, b'test')
        with self.assertRaises(AttributeError):
            chunk.offset = 5
        with self.assertRaises(AttributeError):
            chunk.bytes = b'new'


if __name__ == '__main__':
    unittest.main()

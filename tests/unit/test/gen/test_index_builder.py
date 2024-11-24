import unittest
from unittest.mock import Mock
from gen.index_builder import IndexBuilder


class TestIndexBuilder(unittest.TestCase):
    def test_init(self):
        args = Mock()
        builder = IndexBuilder(args)
        self.assertIs(builder.args, args)
        self.assertEqual(builder.articles, [])


if __name__ == '__main__':
    unittest.main()

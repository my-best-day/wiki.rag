import unittest

from xutils.encoding_utils import EncodingUtils


class TestEncodingUtils(unittest.TestCase):
    def test_adjust_split_point_trivial_before(self):
        _bytes = b'abc'
        after = False

        index = 0
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 2
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    def test_adjust_split_point_trivial_after(self):
        _bytes = b'abc'
        after = True

        index = 0
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 2
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    def test_adjust_split_point_trivial_before_negative_index(self):
        _bytes = b'abc'
        after = False

        index = -1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = -4
            EncodingUtils.adjust_split_point(_bytes, index, after)

    def test_adjust_split_point_trivial_after_negative_index(self):
        _bytes = b'abc'
        after = True

        index = -1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    def test_adjust_split_point_multi_before(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = False

        index = 0
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 2
        expected = 1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 3
        expected = 1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 4
        expected = 1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 5
        expected = 5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    def test_adjust_split_point_multi_after(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = True

        index = 0
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 2
        expected = 5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 3
        expected = 5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 4
        expected = 5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = 5
        expected = 5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = 6
            EncodingUtils.adjust_split_point(_bytes, index, after)

    def test_adjust_split_point_multi_negative_before(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = False

        index = -1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -4
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -5
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -6
        expected = -6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    def test_adjust_split_point_multi_negative_after(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = True

        index = -1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -4
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -5
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -6
        expected = -6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = -7
            EncodingUtils.adjust_split_point(_bytes, index, after)


if __name__ == '__main__':
    unittest.main()

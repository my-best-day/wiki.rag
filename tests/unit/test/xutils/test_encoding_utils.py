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
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = -4
            EncodingUtils.adjust_split_point(_bytes, index, after)

    def test_adjust_split_point_trivial_after_negative_index(self):
        _bytes = b'abc'
        after = True

        index = -1
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = len(_bytes) + index
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

        index = 6
        expected = 6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = 7
            EncodingUtils.adjust_split_point(_bytes, index, after)

    def test_adjust_split_point_multi_negative_before(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = False

        index = -1
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = len(_bytes) + -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = len(_bytes) + -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -4
        expected = len(_bytes) + -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -5
        expected = len(_bytes) + -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -6
        expected = len(_bytes) + -6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

    # TODO: try sign_mode 0 and -1

    def test_adjust_split_point_multi_negative_after(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = True

        index = -1
        expected = len(_bytes) + index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = len(_bytes) + -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = len(_bytes) + -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -4
        expected = len(_bytes) + -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -5
        expected = len(_bytes) + -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        index = -6
        expected = len(_bytes) + -6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = -7
            EncodingUtils.adjust_split_point(_bytes, index, after)

    def test_adjust_split_point_multi_after_sign_mode_minus_1(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = True

        index = 0
        expected = index - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 1
        expected = index - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 2
        expected = 5 - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 3
        expected = 5 - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 4
        expected = 5 - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 5
        expected = 5 - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        index = 6
        expected = 6 - len(_bytes)
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = 7
            EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=-1)

    def test_adjust_split_point_multi_negative_after_sign_mode_0(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = True

        index = -1
        expected = index
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        index = -2
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        index = -3
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        index = -4
        expected = -1
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        index = -5
        expected = -5
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        index = -6
        expected = -6
        adjusted = EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)
        self.assertEqual(adjusted, expected)

        with self.assertRaises(ValueError):
            index = -7
            EncodingUtils.adjust_split_point(_bytes, index, after, sign_mode=0)

    def test_at_end_of_string(self):
        _bytes = b'a' + b'\xF0\x9F\x8D\x94' + b'z'
        after = False

        chunk = _bytes[:len(_bytes)]
        index = len(chunk)
        expected = index
        adjusted = EncodingUtils.adjust_split_point(chunk, index, after)
        self.assertEqual(adjusted, expected)

        chunk = _bytes[:len(_bytes) - 1]
        index = len(chunk)
        expected = index
        adjusted = EncodingUtils.adjust_split_point(chunk, index, after)
        self.assertEqual(adjusted, expected)

        chunk = _bytes[:len(_bytes) - 2]
        index = len(chunk)
        expected = 1
        adjusted = EncodingUtils.adjust_split_point(chunk, index, after)
        self.assertEqual(adjusted, expected)


if __name__ == '__main__':
    unittest.main()

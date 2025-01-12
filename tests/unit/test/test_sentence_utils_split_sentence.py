# cSpell:disable

import unittest

from xutils.sentence_utils import SentenceUtils

# error handling? not here, there....


class TestSentenceUtilsSplitSentence(unittest.TestCase):
    # TODO: test b''.join(fragments) == sentence
    # TODO: test regex, think of edge cases?
    # TODO

    # no need to split - len(text) == max_len
    def test_eq_max_len(self):
        text = b'equal to max_len'
        fragments = SentenceUtils.split_sentence(text, len(text))
        self.assertEqual(len(fragments), 1)
        self.assertIs(fragments[0], text)
        self.assertEqual(b''.join(fragments), text)

    # no need to split - len(text) < max_len
    def test_lt_max_len(self):
        text = b'shorter than max_len'
        fragments = SentenceUtils.split_sentence(text, len(text) + 1)
        self.assertEqual(len(fragments), 1)
        self.assertIs(fragments[0], text)
        self.assertEqual(b''.join(fragments), text)

    # split in half, no adjustment can take place
    def test_split_half(self):
        text = b'123456'
        fragments = SentenceUtils.split_sentence(text, 4)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'123')
        self.assertEqual(fragments[1], b'456')
        self.assertEqual(b''.join(fragments), text)

    # split in half, no adjustment can take place
    def test_split_sentences_split_half_w_spaces(self):
        text = b'123 456 '
        fragments = SentenceUtils.split_sentence(text, 4)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'123 ')
        self.assertEqual(fragments[1], b'456 ')
        self.assertEqual(b''.join(fragments), text)

    # zero extend, no adjustment can take place
    def test_basic_adjustment_zero(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 0)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], text[:24])  # b'I love internationalizat'
        self.assertEqual(fragments[1], text[24:])  # b'ion- now how about you?'
        self.assertEqual(b''.join(fragments), text)

    # extend is not enough to reach \W+\w+
    def test_basic_adjustment_not_sufficient(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 2)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], text[:24])
        self.assertEqual(fragments[1], text[24:])
        self.assertEqual(b''.join(fragments), text)

    # minimal extend, word stitched together, no room for trailing non-word bytes
    def test_basic_adjustment_minimal(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 3)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'I love internationalization')
        self.assertEqual(fragments[1], b'- now how about you?')
        self.assertEqual(b''.join(fragments), text)

    # word stitched together, room for some of the trailing non-word bytes
    def test_basic_adjustment_roomy_1(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 4)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'I love internationalization-')
        self.assertEqual(fragments[1], b' now how about you?')
        self.assertEqual(b''.join(fragments), text)

    # word stitched together, room for some of the trailing non-word bytes
    def test_basic_adjustment_roomy_2(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 5)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'I love internationalization- ')
        self.assertEqual(fragments[1], b'now how about you?')
        self.assertEqual(b''.join(fragments), text)

    # word stitched together, room for the trailing non-word bytes
    def test_basic_adjustment_roomy_3(self):
        text = b'I love internationalization- now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 6)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'I love internationalization- ')
        self.assertEqual(fragments[1], b'now how about you?')
        self.assertEqual(b''.join(fragments), text)

    # grab as many non-word bytes as possible, doesn't have to be all of them
    def test_basic_adjustment_roomy_4(self):
        text = b'I love internationalization-  now how about you?'

        fragments = SentenceUtils.split_sentence(text, 25, 5)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], b'I love internationalization- ')
        self.assertEqual(fragments[1], b' now how about you?')
        self.assertEqual(b''.join(fragments), text)

    # cannot adjust, trailing doesn't have \W+\w+
    def test_basic_adjustment_roomy_5(self):
        text = b'I love internationalization-                    '

        fragments = SentenceUtils.split_sentence(text, 25, 5)
        self.assertEqual(len(fragments), 2)
        self.assertEqual(fragments[0], text[:24])  # b'I love internationalizat'
        self.assertEqual(fragments[1], text[24:])  # b'ion-                    '
        self.assertEqual(b''.join(fragments), text)

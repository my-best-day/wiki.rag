import unittest

from xutils.sentence_utils import SentenceUtils

# error handling? not here, there....


class TestSentenceUtilsSplitBytes(unittest.TestCase):
    def test_split_bytes_into_sentences(self):
        text = b'''
Mrs. Smith went to www.google.com to search for Ph.D. programs. She
typed "U.S. is great!" and "John F. Kennedy was a president." Her
friend, Dr. Brown, replied, "Do you mean U.S.S.R.?" They
also discussed 3.14 and other constants. She
said, "Look at Inc. Ltd. Co. examples..." Finally
, she added: "Ellipses are cool...but overused."
'''

        sentences = SentenceUtils.split_bytes_into_sentences(text)

        self.assertEqual(b''.join(sentences), text)
        self.assertEqual(len(sentences), 9)
        self.assertEqual(sentences[0],
                         b"\nMrs. Smith went to www.google.com to search for Ph.D. programs. ")
        self.assertEqual(sentences[1], b'She\ntyped "U.S. is great!" ')
        self.assertEqual(sentences[2], b'and "John F. Kennedy was a president." ')
        self.assertEqual(sentences[3], b'Her\nfriend, Dr. Brown, replied, "Do you mean U.S.S.R.?" ')
        self.assertEqual(sentences[4], b'They\nalso discussed 3.14 and other constants. ')
        self.assertEqual(sentences[5], b'She\nsaid, "Look at Inc. Ltd. Co. examples..." ')
        self.assertEqual(sentences[6], b'Finally\n, she added: "Ellipses are cool...')
        self.assertEqual(sentences[7], b'but overused."\n')
        self.assertEqual(sentences[8], b'')

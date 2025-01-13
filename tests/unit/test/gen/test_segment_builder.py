import unittest
from unittest.mock import patch

from gen.segment_builder import SegmentBuilder
from xutils.sentence_utils import SentenceUtils


class TestSegmentBuilder(unittest.TestCase):

    def setUp(self):
        self.sentences_per_document = [
            [b'This is a test sentence 11.', b'This is another test sentence 12.'],
            [b'Test sentence 21.', b'Another test sentence 22.'],
            [b'single sentence 31.'],
            [b'Sentence 41.', b'Sentence 42.'],
        ]

    def test_log_interval_override(self):
        with patch.object(SegmentBuilder, 'LOG_INTERVAL', 2):
            self.assertEqual(SegmentBuilder.LOG_INTERVAL, 2)  # Ensure override works

    @patch.object(SegmentBuilder, 'LOG_INTERVAL', 2)
    @patch.object(SegmentBuilder, 'segmentize_document')
    def test_segmentize_documents(self, mock_segmentize_document):

        max_length = 30
        sentences_per_document = self.sentences_per_document

        mock_segmentize_document.side_effect = [
            [b'This is a test sentence 11.', b'This is another test sentence 12.'],
            [b'Test sentence 21.', b'Another test sentence 22.'],
            [b'single sentence 31.'],
            [b'Sentence 41.Sentence 42.'],
        ]

        segments_per_document = SegmentBuilder.segmentize_documents(
            max_length,
            sentences_per_document
        )

        self.assertEqual(segments_per_document, [
            [b'This is a test sentence 11.', b'This is another test sentence 12.'],
            [b'Test sentence 21.', b'Another test sentence 22.'],
            [b'single sentence 31.'],
            [b'Sentence 41.Sentence 42.'],
        ])

    @patch.object(SegmentBuilder, 'split_sentence')
    @patch.object(SegmentBuilder, 'get_balanced_seg_length')
    @patch.object(SegmentBuilder, 'can_add_sentence')
    def test_segmentize_document(
        self,
        mock_can_add_sentence,
        mock_get_balanced_seg_length,
        mock_split_sentence,
    ):
        base_length = 25
        sentences = [
            b'This is a test sentence 11.',   # 27
            b'Short ',
            b'sentence 12.'  # 19
        ]
        mock_get_balanced_seg_length.return_value = 23
        mock_split_sentence.return_value = [b'This is a test ', b'sentence 11.']
        mock_can_add_sentence.side_effect = [True, False, True, False]
        expected_segments = [b'This is a test ', b'sentence 11.Short ', b'sentence 12.']
        segments = SegmentBuilder.segmentize_document(
            base_length,
            sentences
        )
        self.assertEqual(segments, expected_segments)

    @patch.object(SegmentBuilder, 'split_sentence')
    @patch.object(SegmentBuilder, 'get_balanced_seg_length')
    @patch.object(SegmentBuilder, 'can_add_sentence')
    def test_segmentize_document_custom_split_sentence(
        self,
        mock_can_add_sentence,
        mock_get_balanced_seg_length,
        mock_split_sentence,
    ):
        base_length = 25
        sentences = [
            b'This is a test sentence 11.',   # 27
            b'Short ',
            b'sentence 12.'  # 19
        ]
        mock_get_balanced_seg_length.return_value = 23
        mock_split_sentence.return_value = [b'This is a test ', b'sentence 11.']
        mock_can_add_sentence.side_effect = [True, False, True, False]
        expected_segments = [b'This is a test ', b'sentence 11.Short ', b'sentence 12.']
        segments = SegmentBuilder.segmentize_document(
            base_length,
            sentences,
            split_sentence=mock_split_sentence
        )
        self.assertEqual(segments, expected_segments)

    @patch.object(SegmentBuilder, 'split_sentence')
    @patch.object(SegmentBuilder, 'get_balanced_seg_length')
    @patch.object(SegmentBuilder, 'can_add_sentence')
    def test_segmentize_document_custom_split_empty(
        self,
        mock_can_add_sentence,
        mock_get_balanced_seg_length,
        mock_split_sentence,
    ):
        base_length = 25
        sentences = []
        mock_get_balanced_seg_length.return_value = 25
        expected_segments = []
        segments = SegmentBuilder.segmentize_document(
            base_length,
            sentences,
            split_sentence=mock_split_sentence
        )
        mock_split_sentence.assert_not_called()
        mock_can_add_sentence.assert_not_called()
        self.assertEqual(segments, expected_segments)

    def test_get_balanced_seg_length(self):
        # 100 / 24 => 4, 100 / 4 => 25
        balanced = SegmentBuilder.get_balanced_seg_length(100, 25)
        self.assertEqual(balanced, 25)

        # 99 / 25 => 4, 99 / 4 => 24.75 => 25
        balanced = SegmentBuilder.get_balanced_seg_length(99, 25)
        self.assertEqual(balanced, 25)

        # 77 / 25 => 4, 77 / 4 => 19.25 => 20
        balanced = SegmentBuilder.get_balanced_seg_length(77, 25)
        self.assertEqual(balanced, 20)

        # 76 / 25 => 4, 76 / 4 => 19
        balanced = SegmentBuilder.get_balanced_seg_length(76, 25)
        self.assertEqual(balanced, 19)

        # 75 / 25 => 3, 75 / 3 => 25
        balanced = SegmentBuilder.get_balanced_seg_length(75, 25)
        self.assertEqual(balanced, 25)

    @patch.object(SentenceUtils, 'split_sentence')
    def test_split_sentence(self, mock_split_sentence):
        sentence = b'does not matter'
        base_length = 4
        mock_split_sentence.return_value = [b'one ', b'two']
        fragments = SegmentBuilder.split_sentence(sentence, base_length)
        self.assertEqual(fragments, mock_split_sentence.return_value)

    def test_is_sentence_too_long(self):
        sentence = b'does not matter'
        result = SegmentBuilder.is_sentence_too_long(len(sentence), sentence)
        self.assertFalse(result)

        result = SegmentBuilder.is_sentence_too_long(len(sentence) + 1, sentence)
        self.assertFalse(result)

        result = SegmentBuilder.is_sentence_too_long(len(sentence) - 1, sentence)
        self.assertTrue(result)

    def test_can_add_sentence(self):
        result = SegmentBuilder.can_add_sentence(10, 6, b'one', b'two')
        self.assertTrue(result)

        result = SegmentBuilder.can_add_sentence(10, 6, b'one', b'two123')
        self.assertTrue(result)

        result = SegmentBuilder.can_add_sentence(10, 6, b'one', b'two1234')
        self.assertTrue(result)

        result = SegmentBuilder.can_add_sentence(10, 6, b'one', b'two12345')
        self.assertFalse(result)

        result = SegmentBuilder.can_add_sentence(10, 6, b'two1237', b'on')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

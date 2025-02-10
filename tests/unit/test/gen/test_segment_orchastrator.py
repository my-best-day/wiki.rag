import unittest
from unittest.mock import patch, MagicMock, call, mock_open

from pathlib import Path

from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord
from gen.segment_orchestrator import SegmentOrchestrator


class TestSegmentOrchestrator(unittest.TestCase):

    def setUp(self):
        self.records = [
            # seg ind, deco ind, rel ind, offset, length
            SegmentRecord(0, 0, 0, 0, 10),
            SegmentRecord(1, 0, 1, 10, 21),
            SegmentRecord(2, 0, 2, 31, 32),
            SegmentRecord(3, 1, 0, 63, 7),
            SegmentRecord(4, 1, 1, 70, 8),
            SegmentRecord(5, 2, 0, 78, 9),
            SegmentRecord(6, 3, 0, 87, 10),
            SegmentRecord(7, 3, 1, 97, 11),
        ]

        self.segments_per_document = [
            [b'hello pig ', b'how are you doing ha.', b' it is so great to finally meet '],
            [b'tigers!', b'ant eat?'],
            [b'elephants'],
            [b'dirt panda', b'brown bear.']
        ]

        self.adjusted_records = [
            # seg ind, deco ind, rel ind, offset, length
            [SegmentRecord(0, 0, 0, 0, 12),
             SegmentRecord(1, 0, 1, 8, 25),
             SegmentRecord(2, 0, 2, 29, 34)],
            [SegmentRecord(3, 1, 0, 63, 9),
             SegmentRecord(4, 1, 1, 68, 10)],
            [SegmentRecord(5, 2, 0, 78, 9)],
            [SegmentRecord(6, 3, 0, 87, 12),
             SegmentRecord(7, 3, 1, 95, 13)],
        ]

        self.adjusted_segments_per_document = [
            [b'hello pig ho', b'g how are you doing ha. i', b'a. it is so great to finally meet '],
            [b'tigers!an', b's!ant eat?'],
            [b'elephants'],
            [b'dirt pandabr', b'dabrown bear.']  # cspell:disable-line
        ]

        self.overlaps = [
            [b'', b'ho'], [b'g ', b' i'], [b'a.', b''],
            [b'', b'an'], [b's!', b''],
            [b'', b''],
            [b'', b'br'], [b'da', b'']
        ]

    @patch('gen.segment_orchestrator.SegmentOrchestrator.verify_segments')
    @patch('gen.segment_orchestrator.SegmentOrchestrator.dump_raw_segments')
    @patch('gen.segment_overlap_setter.SegmentOverlapSetter.set_overlaps_for_documents')
    @patch('gen.segment_orchestrator.SegmentOrchestrator.describe_segments')
    @patch('gen.segment_orchestrator.SegmentBuilder.segmentize_documents')
    def test_build_segments_with_patches_with_dump_and_verify(
        self,
        mock_segmentize_documents,
        mock_describe_segments,
        mock_set_overlaps_for_documents,
        mock_dump_raw_segments,
        mock_verify_segments,
    ):
        max_len = 10
        sentences_per_document = MagicMock()
        document_offsets = [record.offset for record in self.records]
        text_file_path = Path('text_file.txt')
        text_byte_reader = ByteReader(text_file_path)
        segment_dump_path = Path('segment_dump.txt')
        document_count = 8

        mock_segmentize_documents.return_value = self.segments_per_document
        mock_set_overlaps_for_documents.return_value = \
            self.adjusted_records, self.adjusted_segments_per_document

        segment_record_store = MagicMock()

        SegmentOrchestrator.build_segments(
            max_len,
            sentences_per_document,
            document_offsets,
            segment_record_store,
            text_byte_reader,
            segment_dump_path,
            document_count
        )

        mock_segmentize_documents.assert_called_once_with(
            max_len,
            sentences_per_document,
            split_sentence=None,
            document_count=document_count
        )

        mock_describe_segments.assert_has_calls([
            call(self.segments_per_document, max_len),
            call(self.adjusted_segments_per_document, max_len)
        ])

        mock_set_overlaps_for_documents.assert_called_once_with(
            max_len,
            document_offsets,
            self.segments_per_document
        )

        mock_dump_raw_segments.assert_called_once_with(
            segment_dump_path,
            self.adjusted_segments_per_document
        )

        mock_verify_segments.assert_called_once()
        args, _ = mock_verify_segments.call_args
        self.assertIsInstance(args[0], ByteReader)
        self.assertEqual(args[0].path, text_file_path)
        self.assertEqual(args[1], self.adjusted_segments_per_document)
        self.assertEqual(args[2], self.adjusted_records)

        segment_record_store.save_segment_records.assert_called_once_with(
            self.adjusted_records
        )

    @patch('gen.segment_orchestrator.SegmentOrchestrator.verify_segments')
    @patch('gen.segment_orchestrator.SegmentOrchestrator.dump_raw_segments')
    @patch('gen.segment_overlap_setter.SegmentOverlapSetter.set_overlaps_for_documents')
    @patch('gen.segment_orchestrator.SegmentOrchestrator.describe_segments')
    @patch('gen.segment_orchestrator.SegmentBuilder.segmentize_documents')
    def test_build_segments_with_patches_without_dump_and_verify(
        self,
        mock_segmentize_documents,
        mock_describe_segments,
        mock_set_overlaps_for_documents,
        mock_dump_raw_segments,
        mock_verify_segments,
    ):
        max_len = 10
        sentences_per_document = MagicMock()
        document_offsets = [record.offset for record in self.records]
        text_byte_reader = None
        segment_dump_path = None
        document_count = None

        mock_segmentize_documents.return_value = self.segments_per_document
        mock_set_overlaps_for_documents.return_value = \
            self.adjusted_records, self.adjusted_segments_per_document

        segment_record_store = MagicMock()

        SegmentOrchestrator.build_segments(
            max_len,
            sentences_per_document,
            document_offsets,
            segment_record_store,
            text_byte_reader,
            segment_dump_path,
            document_count
        )

        mock_segmentize_documents.assert_called_once_with(
            max_len,
            sentences_per_document,
            split_sentence=None,
            document_count=document_count
        )

        mock_describe_segments.assert_has_calls([
            call(self.segments_per_document, max_len),
            call(self.adjusted_segments_per_document, max_len)
        ])

        mock_set_overlaps_for_documents.assert_called_once_with(
            max_len,
            document_offsets,
            self.segments_per_document
        )

        mock_dump_raw_segments.assert_not_called()

        mock_verify_segments.assert_not_called()

        segment_record_store.save_segment_records.assert_called_once_with(
            self.adjusted_records
        )

    @patch('gen.segment_orchestrator.pd.Series')
    def test_describe_segments(self, mock_series):
        max_len = 10
        segments_per_document = self.segments_per_document
        segment_count_per_document = [len(segment_list) for segment_list in segments_per_document]
        segment_lengths = [
            len(segment)
            for document_segments in segments_per_document
            for segment in document_segments
        ]

        # Call the method
        SegmentOrchestrator.describe_segments(segments_per_document, max_len)

        # Validate segment_count_per_document
        mock_series.assert_any_call(segment_count_per_document)

        # Validate segment_lengths
        mock_series.assert_any_call(segment_lengths)

    # def test_dump_raw_segments(self):
    @patch('gen.segment_orchestrator.json.dump')
    @patch('gen.segment_orchestrator.open', new_callable=mock_open)
    def test_dump_raw_segments(self, mock_open_func, mock_json_dump):
        segment_dump_path = Path('segment_dump.txt')
        stringified_adjusted_segments_per_document = [
            [segment.decode('utf-8') for segment in document_segments]
            for document_segments in self.adjusted_segments_per_document
        ]
        SegmentOrchestrator.dump_raw_segments(
            segment_dump_path,
            self.adjusted_segments_per_document
        )

        mock_open_func.assert_called_once_with(segment_dump_path, 'w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(
            stringified_adjusted_segments_per_document,
            mock_open_func.return_value
        )

    @patch('gen.segment_orchestrator.SegmentVerifier.verify')
    def test_verify_segments(self, mock_verify):
        byte_reader = MagicMock()
        SegmentOrchestrator.verify_segments(
            byte_reader,
            self.adjusted_segments_per_document,
            self.adjusted_records
        )

        mock_verify.assert_called_once()
        args, _ = mock_verify.call_args
        self.assertIs(args[0], byte_reader)
        self.assertIs(args[1], self.adjusted_records)
        self.assertIs(args[2], self.adjusted_segments_per_document)


if __name__ == "__main__":
    unittest.main()

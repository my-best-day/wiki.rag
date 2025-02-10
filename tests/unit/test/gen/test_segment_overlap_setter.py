import unittest
from unittest.mock import patch
from gen.data.segment_record import SegmentRecord
from gen.segment_overlap_setter import SegmentOverlapSetter


class TestSegmentOverlapSetter(unittest.TestCase):
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
            [b'dirt pandabr', b'dabrown bear.']
        ]

        self.overlaps = [
            [b'', b'ho'], [b'g ', b' i'], [b'a.', b''],
            [b'', b'an'], [b's!', b''],
            [b'', b''],
            [b'', b'br'], [b'da', b'']
        ]

    @patch('gen.segment_overlap_setter.SegmentOverlapSetter.set_overlaps_for_segments')
    def test_set_overlaps_for_documents(self, mock_set_overlaps_for_segments):
        max_len = 10
        document_offsets = [record.offset for record in self.records]
        segments_per_document = self.segments_per_document
        expected_records = \
            [record for doc_records in self.adjusted_records for record in doc_records]
        expected_segments_per_document = self.adjusted_segments_per_document

        mock_set_overlaps_for_segments.side_effect = [
            (self.adjusted_records[0], self.adjusted_segments_per_document[0]),
            (self.adjusted_records[1], self.adjusted_segments_per_document[1]),
            (self.adjusted_records[2], self.adjusted_segments_per_document[2]),
            (self.adjusted_records[3], self.adjusted_segments_per_document[3])
        ]

        adjusted_records, adjusted_segments_per_document = \
            SegmentOverlapSetter.set_overlaps_for_documents(
                max_len,
                document_offsets,
                segments_per_document
            )

        self.assertEqual(adjusted_records, expected_records)
        self.assertEqual(adjusted_segments_per_document, expected_segments_per_document)

    @patch('gen.segment_overlap_setter.SegmentOverlapSetter.get_overlaps')
    def test_set_overlaps_for_segments(self, mock_get_overlaps):
        max_len = 10

        mock_get_overlaps.side_effect = self.overlaps

        for i in range(len(self.segments_per_document)):
            base_adjusted_segment_record = self.adjusted_records[i][0]
            base_segment_index = base_adjusted_segment_record.segment_index
            base_segment_record = self.records[base_segment_index]
            document_index = base_segment_record.document_index
            base_offset = base_segment_record.offset
            segments = self.segments_per_document[i]
            adjusted_records, adjusted_segments = SegmentOverlapSetter.set_overlaps_for_segments(
                max_len,
                base_segment_index,
                document_index,
                base_offset,
                segments
            )
            expected_records = self.adjusted_records[i]
            expected_segments = self.adjusted_segments_per_document[i]
            self.assertEqual(adjusted_records, expected_records)
            self.assertEqual(adjusted_segments, expected_segments)


if __name__ == '__main__':
    unittest.main()

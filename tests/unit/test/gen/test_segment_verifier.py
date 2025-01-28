# cSpell: ignore

import json
import random
import unittest
import pandas as pd
from unittest.mock import MagicMock, patch, call, mock_open

from xutils.byte_reader import ByteReader
from gen.segment_verifier import SegmentVerifier
from gen.data.segment_record import SegmentRecord

from ..xutils.byte_reader_tst import TestByteReader


class TestSegmentVerifier(unittest.TestCase):

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

    # test that calls verify with the output of read_segment_records and read_segment_dump
    @patch('gen.segment_verifier.SegmentVerifier.read_segment_dump')
    @patch('gen.segment_verifier.SegmentVerifier.verify')
    def test_verify_files(self, mock_verify, mock_read_dump):
        mock_records = MagicMock()
        mock_dump = MagicMock()
        mock_verify_result = MagicMock()

        mock_read_dump.return_value = mock_dump
        mock_verify.return_value = mock_verify_result

        segment_record_store = MagicMock()
        segment_record_store.load_segment_records.return_value = mock_records

        SegmentVerifier.verify_files(
            text_file_path='test.txt',
            segment_record_store=segment_record_store,
            dump_file_path='test.dump',
            mode='random',
            n=10
        )

        segment_record_store.load_segment_records.assert_called_once()
        mock_read_dump.assert_called_once_with('test.dump')
        mock_verify.assert_called_once()
        argc, _ = mock_verify.call_args
        self.assertIsInstance(argc[0], ByteReader)
        self.assertEqual(argc[0].path, 'test.txt')
        self.assertEqual(argc[1], mock_records)
        self.assertEqual(argc[2], mock_dump)
        self.assertEqual(argc[3], 'random')
        self.assertEqual(argc[4], 10)

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_random(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        random.seed(1)
        sample_records = random.sample(self.records, 2)

        random.seed(1)
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='random',
            n=2
        )

        mock_verify_records.assert_called_once()
        argc, _ = mock_verify_records.call_args
        self.assertIs(argc[0], mock_byte_reader)
        self.assertEqual(argc[1], sample_records)
        self.assertIs(argc[2], self.segments_per_document)

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_first(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        records = self.records
        first_records = [records[0], records[3], records[5], records[6]]

        sample_records = first_records
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='first',
            n=-1
        )

        mock_verify_records.assert_called_once()
        argc, _ = mock_verify_records.call_args
        self.assertIs(argc[0], mock_byte_reader)
        self.assertEqual(argc[1], sample_records)
        self.assertIs(argc[2], self.segments_per_document)

        sample_records = first_records[:3]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='first',
            n=3
        )

        argc, _ = mock_verify_records.call_args
        self.assertEqual(argc[1], sample_records)

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_document(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        records = self.records
        document_records = [
            [records[0], records[1], records[2]],
            [records[3], records[4]],
            [records[5]],
            [records[6], records[7]]
        ]

        sample_records = document_records[1]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='document',
            n=1
        )

        mock_verify_records.assert_called_once()
        argc, _ = mock_verify_records.call_args
        self.assertIs(argc[0], mock_byte_reader)
        self.assertEqual(argc[1], sample_records)
        self.assertIs(argc[2], self.segments_per_document)

        sample_records = document_records[2]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='document',
            n=2
        )

        argc, _ = mock_verify_records.call_args
        self.assertEqual(argc[1], sample_records)

        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='document',
            n=8
        )

        argc, _ = mock_verify_records.call_args
        self.assertEqual(argc[1], [])

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_segment(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        records = self.records

        sample_records = [records[4]]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='segment',
            n=4
        )

        mock_verify_records.assert_called_once()
        argc, _ = mock_verify_records.call_args
        self.assertIs(argc[0], mock_byte_reader)
        self.assertEqual(argc[1], sample_records)
        self.assertIs(argc[2], self.segments_per_document)

        sample_records = [records[5]]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='segment',
            n=5
        )

        argc, _ = mock_verify_records.call_args
        self.assertEqual(argc[1], sample_records)

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_unknown_mode(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        with self.assertRaises(ValueError):
            SegmentVerifier.verify(
                byte_reader=mock_byte_reader,
                segment_records=self.records,
                segments_per_document=self.segments_per_document,
                mode='unknown',
                n=4
            )

    @patch('gen.segment_verifier.SegmentVerifier.verify_records')
    def test_verify_all(self, mock_verify_records):
        mock_byte_reader = MagicMock()

        records = self.records

        sample_records = records[:4]
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='all',
            n=4
        )

        mock_verify_records.assert_called_once()
        argc, _ = mock_verify_records.call_args
        self.assertIs(argc[0], mock_byte_reader)
        self.assertEqual(argc[1], sample_records)
        self.assertIs(argc[2], self.segments_per_document)

        sample_records = records
        SegmentVerifier.verify(
            byte_reader=mock_byte_reader,
            segment_records=self.records,
            segments_per_document=self.segments_per_document,
            mode='all',
            n=-1
        )

        argc, _ = mock_verify_records.call_args
        self.assertEqual(argc[1], sample_records)

    @patch('gen.segment_verifier.SegmentVerifier.verify_record')
    def test_verify_records(self, mock_verify_record):
        test_byte_reader = MagicMock()

        SegmentVerifier.verify_records(
            byte_reader=test_byte_reader,  # NOSONAR
            sample_records=self.records,
            segments_per_document=self.segments_per_document
        )

        mock_verify_record.assert_has_calls([
            call(test_byte_reader, self.records[0], self.segments_per_document),
            call(test_byte_reader, self.records[1], self.segments_per_document),
            call(test_byte_reader, self.records[2], self.segments_per_document),
            call(test_byte_reader, self.records[3], self.segments_per_document),
            call(test_byte_reader, self.records[4], self.segments_per_document),
            call(test_byte_reader, self.records[5], self.segments_per_document),
            call(test_byte_reader, self.records[6], self.segments_per_document),
            call(test_byte_reader, self.records[7], self.segments_per_document)
        ])

    def test_verify_record(self):
        sentences = self.segments_per_document
        flattened = [sentence for doc_sentences in sentences for sentence in doc_sentences]
        text = b''.join(flattened)

        test_byte_reader = TestByteReader(text)

        is_match = SegmentVerifier.verify_record(
            byte_reader=test_byte_reader,  # NOSONAR
            record=self.records[4],
            segments_per_document=self.segments_per_document
        )
        self.assertTrue(is_match)

        record = self.records[4]
        bad_record = SegmentRecord(
            record.segment_index,
            record.document_index,
            record.relative_segment_index,
            record.offset + 1,
            record.length - 1
        )

        is_match = SegmentVerifier.verify_record(
            byte_reader=test_byte_reader,  # NOSONAR
            record=bad_record,
            segments_per_document=self.segments_per_document
        )
        self.assertFalse(is_match)

    @patch("gen.segment_verifier.SegmentVerifier.convert_segment_strings_to_bytes")
    @patch("builtins.open", new_callable=mock_open)
    def test_read_segment_dump(self, mock_open, mock_convert_segment_strings_to_bytes):
        string_dump = [[text.decode() for text in doc_sentences] for
                       doc_sentences in self.segments_per_document]
        json_dump = json.dumps(string_dump)
        mock_open.return_value.read.return_value = json_dump

        mock_convert_segment_strings_to_bytes.return_value = self.segments_per_document

        dump = SegmentVerifier.read_segment_dump('test.dump')
        mock_open.assert_called_once_with('test.dump', 'r')
        mock_convert_segment_strings_to_bytes.assert_called_once_with(string_dump)
        self.assertEqual(dump, self.segments_per_document)

    def test_convert_segment_strings_to_bytes(self):
        string_dump = [[text.decode() for text in doc_sentences] for
                       doc_sentences in self.segments_per_document]
        bytes_dump = SegmentVerifier.convert_segment_strings_to_bytes(string_dump)
        self.assertEqual(bytes_dump, self.segments_per_document)

    @patch('pandas.read_csv')
    def test_read_segment_records(self, mock_read_csv):
        records_df = pd.DataFrame(self.records)
        mock_read_csv.return_value = records_df

        records = SegmentVerifier.read_segment_records('test.csv')
        mock_read_csv.assert_called_once_with('test.csv', index_col=False)
        self.assertEqual(records, self.records)


if __name__ == '__main__':
    unittest.main()

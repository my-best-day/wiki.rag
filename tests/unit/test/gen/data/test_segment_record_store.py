import io
import unittest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from gen.data.segment_record import SegmentRecord
from gen.data.segment_record_store import SegmentRecordStore


class TestSegmentRecordStore(unittest.TestCase):

    def setUp(self):
        self.segment_record0 = SegmentRecord(0, 0, 0, 0, 0)
        self.segment_record1 = SegmentRecord(1, 0, 1, 0, 0)
        self.segment_record2 = SegmentRecord(2, 1, 0, 0, 0)
        self.segment_record3 = SegmentRecord(3, 2, 0, 0, 0)
        self.segment_record4 = SegmentRecord(4, 2, 1, 0, 0)
        self.segment_records = \
            [self.segment_record0, self.segment_record1, self.segment_record2,
             self.segment_record3, self.segment_record4]

    def test_init(self):
        prefix = "/dev/null/prefix"
        max_len = 100
        store = SegmentRecordStore(path_prefix=prefix, max_len=max_len)
        self.assertEqual(store.path_prefix, prefix)
        self.assertEqual(store.max_len, max_len)

    @patch.object(SegmentRecordStore, 'read_segment_record_df')
    def test_load_segment_records(self, mock_read_segment_record_df):
        df = pd.DataFrame(self.segment_records, columns=SegmentRecord._fields)
        mock_read_segment_record_df.return_value = df
        store = SegmentRecordStore('/dev/null/prefix', 100)
        segment_record_list = store.load_segment_records()
        self.assertEqual(len(segment_record_list), 5)
        self.assertEqual(segment_record_list, self.segment_records)

    def test_read_segment_record_df(self):
        segment_records = self.segment_records
        segment_record_df = pd.DataFrame(segment_records, columns=SegmentRecord._fields)
        buffer = io.StringIO()
        segment_record_df.to_csv(buffer, index=False)
        buffer.seek(0)

        store = SegmentRecordStore('/dev/null/prefix', 100)
        output_df = store.read_segment_record_df(buffer)
        pd.testing.assert_frame_equal(segment_record_df, output_df)

    @patch('pandas.DataFrame.to_csv')
    def test_save_segment_records(self, mock_to_csv):
        store = SegmentRecordStore('/dev/null/prefix', 100)
        store.save_segment_records(self.segment_records)

        mock_to_csv.assert_called_once_with(store.get_segment_record_store_path(), index=False)

    @patch.object(SegmentRecordStore, 'write_segment_records')
    def test_save_segment_records2(self, mock_write_segment_records):
        store = SegmentRecordStore('/dev/null/prefix', 100)
        store.save_segment_records(self.segment_records)

        expected_path = store.get_segment_record_store_path()
        segment_records = self.segment_records
        expected_df = pd.DataFrame(segment_records, columns=SegmentRecord._fields)
        mock_write_segment_records.assert_called_once()
        args, _ = mock_write_segment_records.call_args
        self.assertEqual(args[0], expected_path)
        pd.testing.assert_frame_equal(args[1], expected_df)

    def test_write_segment_record_df(self):
        segment_records = self.segment_records
        segment_record_df = pd.DataFrame(segment_records, columns=SegmentRecord._fields)
        buffer = io.StringIO()
        store = SegmentRecordStore('/dev/null/prefix', 100)
        store.write_segment_records(buffer, segment_record_df)

        buffer.seek(0)
        output_df = pd.read_csv(buffer, index_col=False)
        pd.testing.assert_frame_equal(output_df, segment_record_df)

    def test_get_segment_record_store_path(self):
        store = SegmentRecordStore('/dev/null/prefix', 100)
        expected_path = Path('/dev/null/prefix_100_segment_records.csv')
        self.assertEqual(store.get_segment_record_store_path(), expected_path)


if __name__ == "__main__":
    unittest.main()

import json
import random
import logging
from typing import List, Optional
import pandas as pd

from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord

logger = logging.getLogger(__name__)


class SegmentVerifier:
    """
    Verify the offset and length of segments by using these to read from the text file
    and compare the result with the segment bytes.

    The segments bytes are either given from the segment when it is created, or from the
    dump that saves the bytes.

    Offer various way to select segments to verify such as random, first of each document,
    all segments of a documents, specific segment, or all segments.
    """

    @staticmethod
    def verify_files(
        text_file_path: str,
        segment_records_path: str,
        dump_file_path: str,
        mode: str,
        n: int
    ):
        """
        Verify the segments after the build process using the dump file.

        Args:
            text_file_path (str): Path to the text file.
            segment_file_path (str): Path to the segment records file.
            dump_file_path (str): Path to the segment dump file.
            mode (str): Mode to select segments to verify.
            n (int): Number of segments to verify.
        """
        byte_reader = ByteReader(text_file_path)
        segment_records = SegmentVerifier.read_segment_records(segment_records_path)
        segments_per_document = SegmentVerifier.read_segment_dump(dump_file_path)

        SegmentVerifier.verify(
            byte_reader,
            segment_records,
            segments_per_document,
            mode,
            n
        )

    @staticmethod
    def verify(
        byte_reader: ByteReader,
        segment_records: List[SegmentRecord],
        segments_per_document: List[List[bytes]],
        mode: str,
        n: int
    ):
        """
        Verify that the segments' offset and length are correct by reading from the text file
        and comparing the result with the segment bytes.

        Args:
            byte_reader (ByteReader): Byte reader to read from the text file.
            segment_records (List[SegmentRecord]): List of segment records.
            segments_per_document (List[List[bytes]]): List of segments per document.
            mode (str): Mode to select segments to verify.
            n (int): Number of segments to verify.
        """
        sampler_map = {
            "random": SegmentVerifier.random_sample,
            "first": SegmentVerifier.first_of_firsts,
            "document": SegmentVerifier.target_document,
            "segment": SegmentVerifier.verify_segment,
            "all": SegmentVerifier.all_segments,
        }
        if mode not in sampler_map:
            raise ValueError(f"Unknown mode {mode}")
        sampler = sampler_map[mode]
        sample_records = sampler(segment_records, n)

        SegmentVerifier.verify_records(
            byte_reader,
            sample_records,
            segments_per_document
        )

    @staticmethod
    def verify_records(
        byte_reader: ByteReader,
        sample_records: List[SegmentRecord],
        segments_per_document: List[List[bytes]]
    ) -> None:
        """
        Verify the segments' offset and length are correct by reading from the text file
        and comparing the result with the segment bytes.

        Args:
            byte_reader (ByteReader): Byte reader to read from the text file.
            sample_records (List[SegmentRecord]): List of segment records to verify.
            segments_per_document (List[List[bytes]]): List of segments per document.
        """
        for record in sample_records:
            SegmentVerifier.verify_record(
                byte_reader,
                record,
                segments_per_document
            )

    @staticmethod
    def verify_record(
        byte_reader: ByteReader,
        record: SegmentRecord,
        segments_per_document: List[List[bytes]]
    ) -> bool:
        reader_bytes = byte_reader.read_bytes(record.offset, record.length)
        segment_bytes = segments_per_document[record.document_index][record.relative_segment_index]

        is_match = segment_bytes == reader_bytes
        if is_match:
            logger.debug("+ segment %s of doc %s rel index %s match",
                         record.segment_index,
                         record.document_index,
                         record.relative_segment_index)
        else:
            template = """
- segment %s of doc %s rel index %s does not match

expected: %s

actual  : %s
"""
            logger.info(
                template,
                record.segment_index,
                record.document_index,
                record.relative_segment_index,
                segment_bytes,
                reader_bytes
            )
        return is_match

    @staticmethod
    def random_sample(
        segment_records: list[SegmentRecord],
        n: int
    ) -> list[SegmentRecord]:
        """random sample of segments to verify"""
        sample_records = random.sample(segment_records, n)
        sample_records.sort(key=lambda record: record.segment_index)
        return sample_records

    @staticmethod
    def first_of_firsts(
        segment_records: List[SegmentRecord],
        n: int
    ) -> List[SegmentRecord]:
        """the first segment of the first n documents"""
        sample_records = []
        for record in segment_records:
            # relative-index == 0 -> first segment of a document
            if record.relative_segment_index == 0:
                sample_records.append(record)
                if n > 1 and len(sample_records) >= n:
                    break

        return sample_records

    @staticmethod
    def target_document(
        segment_records: List[SegmentRecord],
        n: int,
    ) -> List[SegmentRecord]:
        """all segments of a document"""
        sample_records = []
        for record in segment_records:
            if record.document_index == n:
                sample_records.append(record)
            elif len(sample_records) > 0:
                break
        return sample_records

    @staticmethod
    def verify_segment(
        segment_records: List[SegmentRecord],
        n: int,
    ) -> List[SegmentRecord]:
        """a specific segment"""
        sample_records = [segment_records[n]]

        return sample_records

    @staticmethod
    def all_segments(
        segment_records: List[SegmentRecord],
        n: Optional[int] = None
    ) -> List[SegmentRecord]:
        """all segments / first n segments"""
        if n is None or n < 0:
            sample_records = segment_records[:]
        else:
            sample_records = segment_records[:n]
        return sample_records

    @staticmethod
    def read_segment_dump(segment_file_path: str) -> List[List[bytes]]:
        """reads segment strings from a json file, converts them to bytes"""
        with open(segment_file_path, 'r') as json_file:
            segment_strings_per_document = json.load(json_file)

        segments_per_document = SegmentVerifier.convert_segment_strings_to_bytes(
            segment_strings_per_document
        )
        return segments_per_document

    @staticmethod
    def convert_segment_strings_to_bytes(
        string_list_list: List[List[str]]
    ) -> List[List[bytes]]:
        """dump is a json file, json files only support strings, no bytes, so we must convert"""
        bytes_list_list = [
            [segment.encode('utf-8') for segment in string_list]
            for string_list in string_list_list
        ]
        return bytes_list_list

    @staticmethod
    def read_segment_records(segment_file_path: str) -> List[SegmentRecord]:
        """reads segment records from a csv file"""
        segment_df = pd.read_csv(segment_file_path, index_col=False)
        segment_records = list(segment_df.itertuples(index=False, name="SegmentRecord"))
        return segment_records

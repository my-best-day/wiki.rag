import json
import random
import logging
from typing import List, Optional
import pandas as pd

from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord

logger = logging.getLogger(__name__)


class SegmentVerifier:

    @staticmethod
    def random_sample(
        segment_records: list[SegmentRecord],
        n: int
    ) -> list[SegmentRecord]:
        sample_records = random.sample(segment_records, n)
        sample_records.sort(key=lambda record: record.segment_index)
        return sample_records

    @staticmethod
    def first_of_firsts(
        segment_records: List[SegmentRecord],
        n: int
    ) -> List[SegmentRecord]:
        # keep: sample_records = segment_records[:10]
        sample_records = []
        for record in segment_records:
            # relative-index == 0 -> first segment of a document
            if record.relative_segment_index == 0:
                sample_records.append(record)
                if len(sample_records) >= n:
                    break

        return sample_records

    @staticmethod
    def target_document(
        segment_records: List[SegmentRecord],
        n: int,
    ) -> List[SegmentRecord]:
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
        sample_records = [segment_records[n]]

        return sample_records

    @staticmethod
    def all_segments(
        segment_records: List[SegmentRecord],
        n: Optional[int] = None
    ) -> List[SegmentRecord]:
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

    @staticmethod
    def verify_files(
        text_file_path: str,
        segment_file_path: str,
        dump_file_path: str,
        mode: str,
        n: int
    ):
        byte_reader = ByteReader(text_file_path)
        segment_records = SegmentVerifier.read_segment_records(segment_file_path)
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
        for record in sample_records:
            reader_bytes = byte_reader.read_bytes(record.offset, record.length)
            segments = segments_per_document[record.document_index]
            segment_bytes = segments[record.relative_segment_index]

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

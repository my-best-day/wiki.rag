"""
Orchestrates the segment building process.

In essence:
1. building shingling segments
2. set overlaps across segments
3. optionally dump segment text to a file for debugging
4. optionally verify the segments against the original text
5. save the segment records to a csv file
"""
import json
import random
import logging
import pandas as pd
from pathlib import Path
from typing import List, Iterator, Optional

from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord
from gen.new_segment_builder import SegmentBuilder
from gen.segment_overlap_setter import SegmentOverlapSetter

logger = logging.getLogger(__name__)


class SegmentOrchestrator:

    @staticmethod
    def build_segments(
        max_len: int,
        sentences_per_document: Iterator[List[bytes]],
        document_offsets: List[int],
        segment_file_path: Path,
        text_file_path: Optional[Path],
        segment_dump_path: Optional[Path] = None,
        document_count: Optional[int] = None,
    ):
        segments_per_document = SegmentBuilder.segmentize_documents(
            max_len, sentences_per_document, document_count)

        SegmentOrchestrator.describe_segments(segments_per_document, max_len)

        segment_records, segments_per_document = SegmentOverlapSetter.set_overlaps_for_documents(
            max_len,
            document_offsets,
            segments_per_document
        )

        SegmentOrchestrator.describe_segments(segments_per_document, max_len)

        if segment_dump_path:
            SegmentOrchestrator.dump_raw_segments(segment_dump_path, segments_per_document)

        if text_file_path:
            byte_reader = ByteReader(text_file_path)
            SegmentOrchestrator.verify_segments(byte_reader, segments_per_document, segment_records)

        SegmentOrchestrator.save_segment_records(segment_file_path, segment_records)

    @staticmethod
    def describe_segments(
        segments_per_document: List[List[bytes]],
        max_len: int
    ) -> None:
        """log segment statistics - segment count per document and segment lengths"""
        segment_count_per_document = [len(segment_list) for segment_list in segments_per_document]
        count_series = pd.Series(segment_count_per_document)

        segment_lengths = [
            len(segment)
            for document_segments in segments_per_document
            for segment in document_segments
        ]
        segment_lengths_series = pd.Series(segment_lengths)

        logger.info("base length: %s", max_len)
        logger.debug("segments per document:\n%s", count_series.describe())
        logger.info("segment lengths:\n%s", segment_lengths_series.describe())

    # for debugging
    @staticmethod
    def dump_raw_segments(
        segment_dump_path: Path,
        segments_per_document: List[List[bytes]]
    ) -> None:
        """
        Save the segments' text to a json file to be used by verify_segments.py
        """
        segments_per_document = [
            [segment.decode('utf-8') for segment in document_segments]
            for document_segments in segments_per_document
        ]

        with open(segment_dump_path, 'w') as json_file:
            json.dump(segments_per_document, json_file)

    @staticmethod
    def verify_segments(
        byte_reader: ByteReader,
        segments_per_document: List[List[bytes]],
        segment_records: List[SegmentRecord]
    ):
        sample_records = []
        for record in segment_records:
            if record[2] == 0:
                sample_records.append(record)
                if len(sample_records) >= 20:
                    break
        random_sample = random.sample(segment_records, 20)
        sample_records.extend(random_sample)

        for (segment_ind, doc_ind, rel_ind, offset, length) in sample_records:
            reader_bytes = byte_reader.read_bytes(offset, length)
            document_segments = segments_per_document[doc_ind]
            try:
                segment_bytes = document_segments[rel_ind]
            except IndexError:
                logger.error("IndexError: segment %s of document %s rel index %s",
                             segment_ind, doc_ind, rel_ind)
                raise
            is_match = segment_bytes == reader_bytes
            if is_match:
                logger.debug("+ segment %s of document %s rel index %s match",
                             segment_ind, doc_ind, rel_ind)
            else:
                logger.info("""
    - segment %s of document %s rel index %s does not match

    expected: %s

    actual  : %s
                """, segment_ind, doc_ind, rel_ind, segment_bytes, reader_bytes)

    @staticmethod
    def save_segment_records(
        segment_file_path: Path,
        records: List[SegmentRecord],
    ) -> None:
        segment_df = pd.DataFrame(
            records,
            columns=SegmentRecord._fields
        )
        segment_df.to_csv(segment_file_path, index=False)
        logger.info("*** saved to %s", segment_file_path)

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
import logging
from pathlib import Path
from typing import List, Iterator, Optional
import pandas as pd

from xutils.byte_reader import ByteReader
from gen.segment_verifier import SegmentVerifier
from gen.data.segment_record import SegmentRecord
from gen.segment_builder import SegmentBuilder, SegmentBuffer
from gen.segment_overlap_setter import SegmentOverlapSetter
from gen.data.segment_record_store import SegmentRecordStore

logger = logging.getLogger(__name__)


class SegmentOrchestrator:
    """
    Orchestrates the segment building process.

    In essence:
    1. building shingling segments
    2. set overlaps across segments
    3. optionally dump segment text to a file for debugging
    4. optionally verify the segments against the original text
    5. save the segment records to a csv file
    """

    @staticmethod
    def build_segments(
        max_len: int,
        sentences_per_document: Iterator[List[bytes]],
        document_offsets: List[int],
        segment_record_store: SegmentRecordStore,
        text_byte_reader: Optional[ByteReader],
        segment_dump_path: Optional[Path] = None,
        document_count: Optional[int] = None,
    ) -> None:
        """
        Builds segments from the provided sentences, sets overlaps between segments,
        and optionally performs various operations such as dumping segments to a file,
        verifying segments against the original text, and saving segment records to a CSV file.

        Args:
            max_len (int): The maximum length of each segment.
            sentences_per_document (Iterator[List[bytes]]): An iterator that yields lists of byte
                strings, where each list represents the sentences of a document.
            document_offsets (List[int]): A list of offsets for each document, indicating where each
                document starts in the original text.
            segment_record_store (SegmentRecordStore):
                The store where the segment records will be saved.
            text_byte_reader (Optional[ByteReader]): The byte reader for the original text for
                verification purposes.
            segment_dump_path (Optional[Path]): The file path where raw segments will be dumped for
                debugging.
            document_count (Optional[int]): The number of documents to process; if None,
                all documents will be processed.

        Returns:
        None: This method does not return any value. It performs operations that affect the file
        system and logs information about the segment building process.
        """
        segment_buffers_per_document: List[List[SegmentBuffer]] = \
            SegmentBuilder.segmentize_documents(
                max_len,
                sentences_per_document,
                split_sentence=None,
                document_count=document_count
            )  # noqa: E123

        SegmentOrchestrator.describe_segments(segment_buffers_per_document, max_len)

        segment_records, extended_segment_buffers_per_document = \
            SegmentOverlapSetter.set_overlaps_for_documents(
                max_len,
                document_offsets,
                segment_buffers_per_document
            )

        SegmentOrchestrator.describe_segments(extended_segment_buffers_per_document, max_len)

        if segment_dump_path:
            SegmentOrchestrator.dump_raw_segments(
                segment_dump_path,
                extended_segment_buffers_per_document
            )

        if text_byte_reader:
            SegmentOrchestrator.verify_segments(
                text_byte_reader,
                extended_segment_buffers_per_document,
                segment_records
            )

        segment_record_store.save_segment_records(segment_records)

    @staticmethod
    def describe_segments(
        segment_buffers_per_document: List[List[SegmentBuffer]],
        max_len: int
    ) -> None:
        """log segment statistics - segment count per document and segment lengths"""
        segment_count_per_document = [len(segment_list) for segment_list in
                                      segment_buffers_per_document]
        count_series = pd.Series(segment_count_per_document)

        segment_lengths = [
            len(segment)
            for document_segments in segment_buffers_per_document
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
        extended_segment_buffers_per_document: List[List[SegmentBuffer]]
    ) -> None:
        """
        Save the segments' text to a json file to be used by verify_segments.py
        """
        segments_per_document = [
            [segment_buffer.bytes().decode('utf-8') for segment_buffer in document_segment_buffers]
            for document_segment_buffers in extended_segment_buffers_per_document
        ]

        with open(segment_dump_path, 'w', encoding='utf-8') as json_file:
            json.dump(segments_per_document, json_file)

    @staticmethod
    def verify_segments(
        byte_reader: ByteReader,
        extended_segment_buffers_per_document: List[List[SegmentBuffer]],
        segment_records: List[SegmentRecord]
    ):
        """verify segments against the original text"""
        SegmentVerifier.verify(
            byte_reader,
            segment_records,
            extended_segment_buffers_per_document,
            mode="all",
            n=-10
        )

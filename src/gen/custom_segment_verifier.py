import logging
from pathlib import Path
from typing import List

from gen.element.store import Store
from gen.element.element import Element

from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord
from gen.element.flat.flat_extended_segment import FlatExtendedSegment

from gen.segment_verifier import SegmentVerifier

logger = logging.getLogger(__name__)


class CustomSegmentVerifier(SegmentVerifier):

    @staticmethod
    def verify_files(
        text_file_path: str,
        segment_file_path: str,
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
        flat_segments = \
            CustomSegmentVerifier.get_flat_extended_segments(text_file_path, segment_file_path)
        segment_records = \
            CustomSegmentVerifier.convert_flat_extended_segments_to_segment_records(flat_segments)
        segments_per_document = SegmentVerifier.read_segment_dump(dump_file_path)

        SegmentVerifier.verify(
            byte_reader,
            segment_records,
            segments_per_document,
            mode,
            n
        )

    @staticmethod
    def convert_flat_extended_segments_to_segment_records(
        flat_segments: List[FlatExtendedSegment]
    ) -> List[SegmentRecord]:
        segment_records = []
        article_uid_set = set()
        relative_segment_index = 0
        for segment_index, segment in enumerate(flat_segments):
            if segment.article_uid not in article_uid_set:
                article_uid_set.add(segment.article_uid)
                relative_segment_index = 0
            else:
                relative_segment_index += 1

            document_index = len(article_uid_set) - 1

            segment_record = SegmentRecord(
                segment_index=segment_index,
                document_index=document_index,
                relative_segment_index=relative_segment_index,
                offset=segment.offset,
                length=segment.byte_length
            )
            segment_records.append(segment_record)
        return segment_records

    @staticmethod
    def get_flat_extended_segments(text_file_path, segment_file_path):

        store = Store()
        store.load_elements(Path(text_file_path), segment_file_path)
        flat_segments = [element for element in Element.instances.values()
                         if isinstance(element, FlatExtendedSegment)]
        return flat_segments

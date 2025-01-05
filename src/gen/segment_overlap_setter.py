import logging
from typing import List, Tuple

from gen.data.segment_record import SegmentRecord
from xutils.overlap_setter import OverlapSetter

logger = logging.getLogger(__name__)


class SegmentOverlapSetter:
    @staticmethod
    def set_overlaps_for_documents(
        max_len: int,
        document_offsets: List[int],
        segments_per_document: List[List[bytes]]
    ) -> Tuple[List[SegmentRecord], List[List[bytes]]]:
        """
        Set overlaps for a list of documents.

        Returns a list of segment records, and a list of extended segment's text.

        The records are used to persist and reconstruct the extended segments.
        The extended segment texts are used for logging, verification, and testing.
        """

        segment_records: List[SegmentRecord] = []
        extended_segments_per_document: List[List[bytes]] = []

        segment_base_index: int = 0

        for document_index, document_segments in enumerate(segments_per_document):
            document_offset = document_offsets[document_index]

            document_segment_records, document_extended_segments = \
                SegmentOverlapSetter.set_overlaps_for_segments(
                    max_len,
                    segment_base_index,
                    document_index,
                    document_offset,
                    document_segments
                )
            extended_segments_per_document.append(document_extended_segments)
            segment_records.extend(document_segment_records)
            segment_base_index += len(document_segments)

        return segment_records, extended_segments_per_document

    @staticmethod
    def set_overlaps_for_segments(
        max_len: int,
        base_segment_index: int,
        document_index: int,
        base_offset: int,
        segments
    ) -> Tuple[List[SegmentRecord], List[bytes]]:
        """
        Set overlaps on a list of related segments.
        Returns a list of segment records, and list of segments with overlaps.

        The records are used to persist and reconstruct the extended segments.
        The list of the extended segment text is used for logging, verification, and testing.
        """
        segment_with_overlap_list = []
        segment_records = []

        segment_count = len(segments)
        prev_segment_bytes = None
        for i in range(segment_count):
            target_segment_bytes = segments[i]
            if i < segment_count - 1:
                next_segment_bytes = segments[i + 1]
            else:
                next_segment_bytes = None

            before_overlap, after_overlap = OverlapSetter.get_overlaps(
                max_len,
                target_segment_bytes,
                prev_segment_bytes,
                next_segment_bytes
            )
            segment_with_overlaps = before_overlap + target_segment_bytes + after_overlap
            segment_index = base_segment_index + i
            offset = base_offset - len(before_overlap)
            length = len(segment_with_overlaps)
            segment_record = SegmentRecord(segment_index, document_index, i, offset, length)
            segment_records.append(segment_record)

            base_offset += len(target_segment_bytes)

            segment_with_overlap_list.append(segment_with_overlaps)

            prev_segment_bytes = target_segment_bytes

        return segment_records, segment_with_overlap_list

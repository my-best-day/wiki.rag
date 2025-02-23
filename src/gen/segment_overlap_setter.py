"""
Set overlaps for a list of documents.
"""
import logging
from typing import List, Tuple, Union, Optional

from gen.data.segment_record import SegmentRecord
from gen.segment_builder import SegmentBuffer

BytesOrStr = Union[bytes, str]
OptionalBytesOrStr = Union[BytesOrStr, None]

logger = logging.getLogger(__name__)


class SegmentOverlapSetter:
    """
    Set overlaps for a list of documents.
    """

    @staticmethod
    def set_overlaps_for_documents(
        max_len: int,
        document_offsets: List[int],
        segment_buffers_per_document: List[List[SegmentBuffer]]
    ) -> Tuple[List[SegmentRecord], List[List[SegmentBuffer]]]:
        """
        Set overlaps for a list of documents.

        Returns a list of segment records, and a list of extended segment's text.

        The records are used to persist and reconstruct the extended segments.
        The extended segment texts are used for logging, verification, and testing.
        """

        segment_records: List[SegmentRecord] = []
        extended_segment_buffers_per_document: List[List[SegmentBuffer]] = []

        segment_base_index: int = 0

        for document_index, document_segment_buffers in enumerate(segment_buffers_per_document):
            document_offset = document_offsets[document_index]

            document_segment_records, document_extended_segment_buffers = \
                SegmentOverlapSetter.set_overlaps_for_segment_buffers(
                    max_len,
                    segment_base_index,
                    document_index,
                    document_offset,
                    document_segment_buffers
                )
            extended_segment_buffers_per_document.append(document_extended_segment_buffers)
            segment_records.extend(document_segment_records)
            segment_base_index += len(document_segment_buffers)

        return segment_records, extended_segment_buffers_per_document

    @staticmethod
    def set_overlaps_for_segment_buffers(
        max_len: int,
        base_segment_index: int,
        document_index: int,
        base_offset: int,
        segment_buffers: List[SegmentBuffer]
    ) -> Tuple[List[SegmentRecord], List[SegmentBuffer]]:
        """
        Set overlaps on a list of related segments.
        Returns a list of segment records, and list of segments with overlaps.

        The records are used to persist and reconstruct the extended segments.
        The list of the extended segment text is used for logging, verification, and testing.
        """
        segment_with_overlap_list = []
        segment_records = []

        segment_count = len(segment_buffers)
        prev_segment_buffer = None
        for i in range(segment_count):
            target_segment_buffer = segment_buffers[i]
            if i < segment_count - 1:
                next_segment_buffer = segment_buffers[i + 1]
            else:
                next_segment_buffer = None

            before_overlap_buffer, after_overlap_buffer = SegmentOverlapSetter.get_overlaps(
                max_len,
                target_segment_buffer,
                prev_segment_buffer,
                next_segment_buffer
            )
            segment_with_overlaps = SegmentBuffer.concat([
                before_overlap_buffer,
                target_segment_buffer,
                after_overlap_buffer
            ])
            segment_index = base_segment_index + i
            offset = base_offset - len(before_overlap_buffer)
            length = len(segment_with_overlaps)
            segment_record = SegmentRecord(segment_index, document_index, i, offset, length)
            segment_records.append(segment_record)

            base_offset += len(target_segment_buffer)

            segment_with_overlap_list.append(segment_with_overlaps)

            prev_segment_buffer = target_segment_buffer

        return segment_records, segment_with_overlap_list

    @staticmethod
    def get_overlaps(
        max_len: int,
        target_seg_buffer: SegmentBuffer,
        prev_seg_buffer: Optional[SegmentBuffer],
        next_seg_buffer: Optional[SegmentBuffer]
    ) -> Tuple[SegmentBuffer, SegmentBuffer]:
        """
        Compute overlaps for the target segment.

        Args:
            max_len (int): The maximum allowed length for the combined text.
            target_seg_text (Union[str, bytes]): The target segment text.
            prev_seg_text (opt_bytes_or_str): The previous segment text, if any.
            next_seg_text (opt_bytes_or_str): The next segment text, if any.

        Returns:
            Tuple[opt_bytes_or_str, opt_bytes_or_str]: A tuple containing the before and after
            overlaps.
        """
        before_overlap_buffer = SegmentBuffer()
        after_overlap_buffer = SegmentBuffer()

        target_seg_len = len(target_seg_buffer)
        if target_seg_len >= max_len:
            return b'', b''

        # maximum length of overlaps, to curtail the length of the overlaps
        alloted = int(0.2 * max_len)
        available = min(alloted, max_len - target_seg_len)
        room = available // 2

        prev_seg_indices = list(range(0, len(prev_seg_buffer.sentences))) if prev_seg_buffer else []
        next_seg_indices = list(range(0, len(next_seg_buffer.sentences))) if next_seg_buffer else []

        if prev_seg_indices:
            SegmentOverlapSetter.prepend_if_room(
                before_overlap_buffer,
                prev_seg_buffer,
                prev_seg_indices,
                room
            )

        if next_seg_indices:
            SegmentOverlapSetter.append_if_room(
                after_overlap_buffer,
                next_seg_buffer,
                next_seg_indices,
                room
            )

        # try again to prepend
        if prev_seg_indices:
            current_length = (
                len(target_seg_buffer)
                + len(before_overlap_buffer)
                + len(after_overlap_buffer)
            )
            room_left = max_len - current_length
            if room_left > 0:
                SegmentOverlapSetter.prepend_if_room(
                    before_overlap_buffer,
                    prev_seg_buffer,
                    prev_seg_indices,
                    room_left
                )

        if next_seg_indices:
            current_length = (
                len(target_seg_buffer)
                + len(before_overlap_buffer)
                + len(after_overlap_buffer)
            )
            room_left = max_len - current_length
            if room_left > 0:
                SegmentOverlapSetter.append_if_room(
                    after_overlap_buffer,
                    next_seg_buffer,
                    next_seg_indices,
                    room_left
                )

        return before_overlap_buffer, after_overlap_buffer

    @staticmethod
    def append_if_room(
        target_buffer: SegmentBuffer,
        next_buffer: SegmentBuffer,
        next_indexes: List[int],
        room: int
    ) -> bool:
        """
        Append a sentence from the source buffer to the target buffer if there is room.
        """
        while next_indexes:
            index = next_indexes.pop(0)
            sentence = next_buffer.sentences[index]
            if len(target_buffer) + len(sentence) <= room:
                target_buffer.append_sentence(sentence)
            else:
                next_indexes.insert(0, index)
                break

    @staticmethod
    def prepend_if_room(
        target_buffer: SegmentBuffer,
        prev_buffer: SegmentBuffer,
        prev_indexes: List[int],
        room: int
    ) -> bool:
        """
        Prepend a sentence from the source buffer to the target buffer if there is room.
        """
        while prev_indexes:
            index = prev_indexes.pop()
            sentence = prev_buffer.sentences[index]
            if len(target_buffer) + len(sentence) <= room:
                target_buffer.prepend_sentence(sentence)
            else:
                prev_indexes.append(index)
                break

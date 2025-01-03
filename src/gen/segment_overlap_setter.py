import logging
from typing import List, Tuple

from xutils.overlap_setter import OverlapSetter

logger = logging.getLogger(__name__)


class SegmentOverlapSetter:
    @staticmethod
    def set_overlaps_for_plot_list(
        max_len: int,
        plot_list,
        segments_per_plot
    ) -> Tuple[List[List[bytes]], List[Tuple[int, int, int, int, int]]]:

        overlaps_per_segment = []
        segment_records = []

        segment_index = 0

        for plot_index, plot_segment_byte_list in enumerate(segments_per_plot):
            plot = plot_list[plot_index]
            base_offset = plot.offset

            plot_with_overlaps_list, plot_segment_records = \
                SegmentOverlapSetter.set_overlaps_for_plot(
                    max_len,
                    segment_index,
                    plot_index,
                    base_offset,
                    plot_segment_byte_list
                )
            overlaps_per_segment.append(plot_with_overlaps_list)
            segment_records.extend(plot_segment_records)
            segment_index += len(plot_segment_byte_list)

        return overlaps_per_segment, segment_records

    @staticmethod
    def set_overlaps_for_plot(
        max_len: int,
        base_segment_index: int,
        plot_index: int,
        base_offset: int,
        plot_segment_byte_list
    ):
        plot_segment_with_overlaps_list = []
        segment_records = []

        segment_count = len(plot_segment_byte_list)
        prev_segment_bytes = None
        for i in range(segment_count):
            target_segment_bytes = plot_segment_byte_list[i]
            if i < segment_count - 1:
                next_segment_bytes = plot_segment_byte_list[i + 1]
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
            segment_record = (segment_index, plot_index, i, offset, length)
            segment_records.append(segment_record)

            base_offset += len(target_segment_bytes)

            plot_segment_with_overlaps_list.append(segment_with_overlaps)

            prev_segment_bytes = target_segment_bytes

        return plot_segment_with_overlaps_list, segment_records

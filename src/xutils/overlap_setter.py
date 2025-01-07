from typing import Union, Tuple
from xutils.encoding_utils import EncodingUtils

bytes_or_str = Union[bytes, str]
opt_bytes_or_str = Union[bytes_or_str, None]


class OverlapSetter:

    @staticmethod
    def get_overlaps(
        max_len: int,
        target_seg_text: bytes_or_str,
        prev_seg_text: opt_bytes_or_str,
        next_seg_text: opt_bytes_or_str
    ) -> Tuple[bytes_or_str, bytes_or_str]:
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

        Overview:
            * The method divides the extra space available in the target segment for overlaps
              taken from the previous and next segments.
            * assumes the target segment has room for overlaps, meaning
              len(target_seg_text) < max_len
            * overlap is limited to up to 0.2 * max-len

        Dictionary:
            * allowed: maximum overlap allowed regardless of room or availability
            * initial_room: total extra space available in the target segment for overlaps,
            divided equally between before and after.
            * before_overlap_len, after_overlap_len: the lengths of the before and after overlaps
            * target_seg_len, prev_seg_len, next_seg_len: the lengths of the target, before,
            and after segments
            * available_forward: unused room from before_overlap that can be reassigned to
              after_overlap
            * available_backward: unused room from after_overlap that can be reassigned to
            before_overlap

        Algorithm:
            0.  Compute target_seg_length. If greater or equal max_len, return None, None
            1.  Compute prev_seg_len and next_seg_len from the input, defaulting to 0 if None
            2.  Set allowed = 0.2 * max_len
            3.  Compute initial_room = (max-len - cur_seg_length) // 2
            4.  Calculate before_overlap_len and after_overlap_len using the minimum of:
                allowed, initial_room, and the length of the respective segments
            5.  Adjust overlap length:
            a.  if unused room remains after before_overlap, assign it to after_overlap
            b.  if unused room remains after after_overlap, assign it to before_overlap
            6.  Extract overlaps from the prev/next_seg_text using the calculated lengths
        """

        target_type = type(target_seg_text)
        assert \
            isinstance(prev_seg_text, (target_type, type(None))) \
            and \
            isinstance(next_seg_text, (target_type, type(None)))

        target_seg_len = len(target_seg_text)
        if target_seg_len >= max_len:
            return b'', b''

        prev_seg_len = len(prev_seg_text) if prev_seg_text else 0
        next_seg_len = len(next_seg_text) if next_seg_text else 0
        allowed = int(0.2 * max_len)

        initial_room = (max_len - target_seg_len) // 2
        before_overlap_len = min(allowed, initial_room, prev_seg_len)
        after_overlap_len = min(allowed, initial_room, next_seg_len)

        available_forward = initial_room - before_overlap_len
        if available_forward > 0 and after_overlap_len < allowed:
            after_overlap_len = min(allowed, initial_room + available_forward, next_seg_len)
        else:
            available_backward = initial_room - after_overlap_len
            if available_backward > 0 and before_overlap_len < allowed:
                before_overlap_len = min(allowed, initial_room + available_backward, prev_seg_len)

        if before_overlap_len > 0:
            # if prev_segment is None, we expect before_overlap to be 0
            _, before_overlap_text = EncodingUtils.split_at(
                text=prev_seg_text,
                index=-before_overlap_len,
                after_char=True,
                include_first=False,
                include_remainder=True
            )
        else:
            before_overlap_text = b''

        if after_overlap_len > 0:
            # if next_segment is None, we expect after_overlap to be 0
            assert next_seg_text is not None
            after_overlap_text, _ = EncodingUtils.split_at(
                text=next_seg_text,
                index=after_overlap_len,
                after_char=False,
                include_first=True,
                include_remainder=False
            )
        else:
            after_overlap_text = b''

        return before_overlap_text, after_overlap_text

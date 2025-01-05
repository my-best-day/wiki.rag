from typing import NamedTuple


class SegmentRecord(NamedTuple):
    segment_index: int
    document_index: int
    relative_segment_index: int
    offset: int
    length: int

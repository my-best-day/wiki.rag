"""
SegmentRecord is a record of a segment.
A compact representation of a segment.
"""
from typing import NamedTuple


class SegmentRecord(NamedTuple):
    """
    A record of a segment.
    A compact representation of a segment.
    """
    segment_index: int
    document_index: int
    relative_segment_index: int
    offset: int
    length: int

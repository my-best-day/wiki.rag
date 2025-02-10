"""
ExtendedSegment is a container of a segment and its (optional) overlaps.
"""
from uuid import UUID
from typing import Iterator, Optional
from gen.element.element import Element
from gen.element.flat.flat_extended_segment import FlatExtendedSegment
from gen.element.segment import Segment
from gen.element.container import Container


class ExtendedSegment(Container):
    """
    ExtendedSegment is a container of a segment and its (optional) overlaps.
    """
    def __init__(self, segment: Segment, uid: Optional[UUID] = None) -> None:
        """
        Initialize the ExtendedSegment.
        Args:
            segment: the segment to contain
            uid: the uid of the ExtendedSegment when loading from xdata
        """
        super().__init__(uid=uid)
        self._before_overlap: Optional[Element] = None
        # most likely we will segment.segment = segment. init _segment to None
        self._segment: Segment = segment
        self._after_overlap: Optional[Element] = None

    @property
    def before_overlap(self) -> Optional[Element]:
        """Get the leading overlap."""
        return self._before_overlap

    @before_overlap.setter
    def before_overlap(self, value: Element) -> None:
        """Set the leading overlap."""
        self._before_overlap = value
        self.reset()

    @property
    def segment(self) -> Segment:
        """Get the segment."""
        return self._segment

    @property
    def after_overlap(self) -> Optional[Element]:
        """Get the trailing overlap."""
        return self._after_overlap

    @after_overlap.setter
    def after_overlap(self, value: Element) -> None:
        """Set the trailing overlap."""
        self._after_overlap = value
        self.reset()

    @property
    def elements(self) -> Iterator[Element]:
        """Get the elements in the extended segment (container)."""
        if self.before_overlap:
            yield self.before_overlap
        yield self.segment
        if self.after_overlap:
            yield self.after_overlap

    def append_element(self, element: Element) -> None:
        """Append an element to the extended segment."""
        self.segment.append_element(element)
        self.reset()

    @property
    def offset(self) -> int:
        """Get the offset of the extended segment."""
        if self.before_overlap:
            offset = self.before_overlap.offset
        else:
            offset = self.segment.offset

        return offset

    @property
    def element_count(self) -> int:
        """The number of elements in the extended segment."""
        count = 1 if self.segment.element_count > 0 else 0
        if self.before_overlap:
            count += 1
        if self.after_overlap:
            count += 1
        return count

    @property
    def article(self):
        """Get the article of the extended segment."""
        return self.segment.article

    def to_xdata(self):
        """Convert the extended segment to xdata."""
        xdata = super().to_xdata()
        xdata['segment_uid'] = str(self.segment.uid)
        if self.before_overlap:
            xdata['before_overlap_uid'] = str(self.before_overlap.uid)
        if self.after_overlap:
            xdata['after_overlap_uid'] = str(self.after_overlap.uid)
        return xdata

    def to_flat_extended_segment(self):
        """Convert the extended segment to a flat extended segment."""
        return FlatExtendedSegment(self.uid, self.article.uid, self.offset, self.byte_length)

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        """Create an extended segment from xdata."""
        uid = UUID(xdata['uid'])
        segment_uid = UUID(xdata['segment_uid'])
        segment = Element.instances[segment_uid]
        extended_segment = cls(segment, uid=uid)
        return extended_segment

    def resolve_dependencies(self, xdata):
        """Resolve the dependencies of the extended segment."""
        super().resolve_dependencies(xdata)

        if 'before_overlap_uid' in xdata:
            before_overlap_uid = UUID(xdata['before_overlap_uid'])
            before_overlap = Element.instances[before_overlap_uid]
            self.before_overlap = before_overlap

        if 'after_overlap_uid' in xdata:
            after_overlap_uid = UUID(xdata['after_overlap_uid'])
            after_overlap = Element.instances[after_overlap_uid]
            self.after_overlap = after_overlap

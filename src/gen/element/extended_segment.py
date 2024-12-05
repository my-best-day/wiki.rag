from uuid import UUID
from typing import Iterator, Optional
from gen.element.element import Element
from gen.element.flat.flat_extended_segment import FlatExtendedSegment
from gen.element.segment import Segment
from gen.element.container import Container


class ExtendedSegment(Container):
    """
    ExtendedSegment is a container that contains a segment and (optional) overlaps.
    """
    def __init__(self, segment: Segment, uid: Optional[UUID] = None) -> None:
        super().__init__(uid=uid)
        self._before_overlap: Optional[Element] = None
        # most likely we will segment.segment = segment. init _segment to None
        self._segment: Segment = segment
        self._after_overlap: Optional[Element] = None

    @property
    def before_overlap(self) -> Optional[Element]:
        return self._before_overlap

    @before_overlap.setter
    def before_overlap(self, value: Element) -> None:
        self._before_overlap = value
        self.reset()

    @property
    def segment(self) -> Segment:
        return self._segment

    @property
    def after_overlap(self) -> Optional[Element]:
        return self._after_overlap

    @after_overlap.setter
    def after_overlap(self, value: Element) -> None:
        self._after_overlap = value
        self.reset()

    @property
    def elements(self) -> Iterator[Element]:
        if self.before_overlap:
            yield self.before_overlap
        yield self.segment
        if self.after_overlap:
            yield self.after_overlap

    def append_element(self, element: Element) -> None:
        self.segment.append_element(element)
        self.reset()

    @property
    def offset(self) -> int:
        """
        The offset of the extended segment.
        """
        if self.before_overlap:
            offset = self.before_overlap.offset
        else:
            offset = self.segment.offset

        return offset

    @property
    def element_count(self) -> int:
        """
        The number of elements in the extended segment.
        """
        count = 1 if self.segment.element_count > 0 else 0
        if self.before_overlap:
            count += 1
        if self.after_overlap:
            count += 1
        return count

    @property
    def article(self):
        return self.segment.article

    def to_xdata(self):
        xdata = super().to_xdata()
        xdata['segment_uid'] = str(self.segment.uid)
        if self.before_overlap:
            xdata['before_overlap_uid'] = str(self.before_overlap.uid)
        if self.after_overlap:
            xdata['after_overlap_uid'] = str(self.after_overlap.uid)
        return xdata

    def to_flat_extended_segment(self):
        return FlatExtendedSegment(self.uid, self.article.uid, self.offset, self.byte_length, None)

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        uid = UUID(xdata['uid'])
        segment_uid = UUID(xdata['segment_uid'])
        segment = Element.instances[segment_uid]
        extended_segment = cls(segment, uid=uid)
        return extended_segment

    def resolve_dependencies(self, xdata):
        super().resolve_dependencies(xdata)

        if 'before_overlap_uid' in xdata:
            before_overlap_uid = UUID(xdata['before_overlap_uid'])
            before_overlap = Element.instances[before_overlap_uid]
            self.before_overlap = before_overlap

        if 'after_overlap_uid' in xdata:
            after_overlap_uid = UUID(xdata['after_overlap_uid'])
            after_overlap = Element.instances[after_overlap_uid]
            self.after_overlap = after_overlap

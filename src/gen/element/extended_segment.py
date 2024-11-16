from typing import Iterator, Optional
from gen.element.container import Container
from gen.element.element import Element
from gen.element.segment import Segment


class ExtendedSegment(Container):
    """
    ExtendedSegment is a container that contains a segment and (optional) overlaps.
    """
    def __init__(self, segment: Segment) -> None:
        super().__init__()
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

    def to_data(self):
        data = super().to_data()
        data['segment'] = self.segment.to_data()
        if self.before_overlap:
            data['before_overlap'] = self.before_overlap.to_data()
        if self.after_overlap:
            data['after_overlap'] = self.after_overlap.to_data()
        return data

    def to_xdata(self):
        xdata = super().to_xdata()
        xdata['segment'] = self.segment.index
        if self.before_overlap:
            xdata['before_overlap'] = self.before_overlap.index
        if self.after_overlap:
            xdata['after_overlap'] = self.after_overlap.index
        return xdata

    @classmethod
    def from_data(cls, data):
        segment = Segment.from_data(data['segment'])
        extended_segment = cls(segment)
        if 'before_overlap' in data:
            before_overlap = Element.hierarchy_from_data(data['before_overlap'])
            extended_segment.before_overlap = before_overlap
        if 'after_overlap' in data:
            after_overlap = Element.hierarchy_from_data(data['after_overlap'])
            extended_segment.after_overlap = after_overlap
        return extended_segment

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        segment_index = xdata['segment']
        segment = Element.instances[segment_index]
        extended_segment = cls(segment)
        if 'before_overlap' in xdata:
            before_overlap_index = xdata['before_overlap']
            before_overlap = Element.instances[before_overlap_index]
            extended_segment.before_overlap = before_overlap
        if 'after_overlap' in xdata:
            after_overlap_index = xdata['after_overlap']
            after_overlap = Element.instances[after_overlap_index]
            extended_segment.after_overlap = after_overlap

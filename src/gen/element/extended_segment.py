from typing import Iterator, Union
from gen.element.container import Container
from gen.element.element import Element
from gen.element.segment import Segment


class ExtendedSegment(Container):
    """
    ExtendedSegment is a container that contains a segment and (optional) overlaps.
    """
    def __init__(self) -> None:
        super().__init__()
        self._before_overlap: Union[Element, None] = None
        self._segment: Segment = Segment()
        self._after_overlap: Union[Element, None] = None

    @property
    def before_overlap(self) -> Union[Element, None]:
        return self._before_overlap

    @before_overlap.setter
    def before_overlap(self, value: Union[Element, None]) -> None:
        self._before_overlap = value
        self.reset()

    @property
    def segment(self) -> Segment:
        return self._segment

    @segment.setter
    def segment(self, value: Segment) -> None:
        self._segment = value
        self.reset()

    @property
    def after_overlap(self) -> Union[Element, None]:
        return self._after_overlap

    @after_overlap.setter
    def after_overlap(self, value: Union[Element, None]) -> None:
        self._after_overlap = value
        self.reset()

    @property
    def elements(self) -> Iterator[Element]:
        if self.before_overlap:
            yield self.before_overlap
        yield from self.segment.elements
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

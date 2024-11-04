from gen.element.element import Element
from gen.element.container import Container
from typing import Iterator, List, Optional


class ListContainer(Container):
    def __init__(self, element: Optional[Element] = None):
        super().__init__()
        self._elements: List[Element] = []
        if element is not None:
            self.append_element(element)

    @property
    def elements(self) -> Iterator[Element]:
        return iter(self._elements)

    def append_element(self, element: Element) -> None:
        assert isinstance(element, Element), f'element must be an Element (got {type(element)})'

        self._elements.append(element)

    @property
    def offset(self) -> int:
        if not self._elements:
            raise ValueError('no elements in container')
        return self._elements[0].offset

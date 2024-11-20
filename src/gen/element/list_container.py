from uuid import UUID
from gen.element.element import Element
from gen.element.container import Container
from typing import Iterator, List, Optional


class ListContainer(Container):
    def __init__(self, element: Optional[Element] = None, uid: Optional[UUID] = None):
        super().__init__(uid=uid)
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

    @property
    def element_count(self) -> int:
        """
        The number of elements in the container.
        """
        return len(self._elements)

    def to_xdata(self):
        xdata = super().to_xdata()
        element_uids = [str(element.uid) for element in self.elements]
        xdata['element_uids'] = element_uids
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        uid = UUID(xdata['uid'])
        container = cls(uid=uid)

        return container

    def resolve_dependencies(self, xdata):
        super().resolve_dependencies(xdata)
        element_uids = xdata['element_uids']
        for element_uid in element_uids:
            element_uid = UUID(element_uid)
            element = Element.instances[element_uid]
            self.append_element(element)

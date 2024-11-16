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

    @property
    def element_count(self) -> int:
        """
        The number of elements in the container.
        """
        return len(self._elements)

    def to_data(self):
        data = super().to_data()
        data['elements'] = [element.to_data() for element in self.elements]
        return data

    def to_xdata(self):
        xdata = super().to_xdata()
        elements = [element.index for element in self.elements]
        xdata['elements'] = elements
        return xdata

    @classmethod
    def from_data(cls, data):
        elements = []
        elements_data = data['elements']
        for element_data in elements_data:
            element = Element.hierarchy_from_data(element_data)
            elements.append(element)

        container = cls()
        for element in elements:
            container.append_element(element)

        return container

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        elements = []
        for element_index in xdata['elements']:
            element = cls.instances[element_index]
            elements.append(element)

        container = cls()
        for element in elements:
            container.append_element(element)

        return container

from abc import ABC, abstractmethod
from typing import Iterator, Union
from gen.element.element import Element


class Container(Element, ABC):
    """
    A Container is an element that contains (group) other elements.
    """
    def __init__(self):
        Element.__init__(self)
        ABC.__init__(self)
        # for caching, see reset()
        self.__bytes: Union[bytes, None] = None
        self.__text: Union[str, None] = None
        self.__clean_text: Union[str, None] = None

    @property
    @abstractmethod
    def elements(self) -> Iterator[Element]:
        """
        Iterate over the elements in the container.
        """
        raise NotImplementedError

    # not sure this belongs here
    @abstractmethod
    def append_element(self, element: Element) -> None:
        """
        Append an element to the container.
        """
        raise NotImplementedError

    @property
    def bytes(self) -> bytes:
        """
        The bytes of the container.
        """
        if self.__bytes is None:
            self.__bytes = b''.join(element.bytes for element in self.elements)
        return self.__bytes

    @property
    def text(self) -> str:
        """
        The text of the container.
        """
        if self.__text is None:
            self.__text = ''.join(element.text for element in self.elements)
        return self.__text

    @property
    def clean_text(self) -> str:
        """
        The clean text of the container.
        """
        if self.__clean_text is None:
            self.__clean_text = Element.normalize_text(self.text)
        return self.__clean_text

    @property
    def byte_length(self) -> int:
        """
        The byte length of the container.
        """
        byte_length = sum(element.byte_length for element in self.elements)
        return byte_length

    @property
    def char_length(self) -> int:
        """
        The character length of the container.
        """
        char_length = sum(element.char_length for element in self.elements)
        return char_length

    @property
    def clean_length(self) -> int:
        """
        The clean length of the container.
        """
        clean_length = len(self.clean_text)
        return clean_length

    def reset(self) -> None:
        """
        Reset the memoizations of the container.
        """
        for element in self.elements:
            if callable(getattr(element, 'reset', None)):
                element.reset()
        self.__bytes = None
        self.__text = None
        self.__clean_text = None

    @property
    def element_count(self) -> int:
        """
        The number of elements in the container.
        """
        return len(list(self.elements))

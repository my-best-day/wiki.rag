from typing import Tuple, TYPE_CHECKING
from gen.element.element import Element

if TYPE_CHECKING:
    from gen.element.fragment import Fragment


def is_positive_number(value):
    return isinstance(value, (int, float)) and value >= 0


class Section(Element):
    """
    A section is a single concrete element. It has an offset and bytes.
    The other properties are derived.
    """

    def __init__(self, offset: int, _bytes: bytes) -> None:
        super().__init__()

        assert isinstance(_bytes, bytes), f'bytes must be a bytes object (got {type(_bytes)})'
        assert is_positive_number(offset), f'offset must be a positive number (got {type(offset)})'

        self._offset = offset
        self._bytes = _bytes

        # for caching, see reset()
        self.__text = None
        self.__clean_text = None

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def bytes(self) -> bytes:
        return self._bytes

    @property
    def text(self) -> str:
        if self.__text is None:
            self.__text = self.bytes.decode('utf-8')
        return self.__text

    @property
    def clean_text(self) -> str:
        if self.__clean_text is None:
            self.__clean_text = self.normalize_text(self.text)
        return self.__clean_text

    @property
    def byte_length(self) -> int:
        return len(self.bytes)

    @property
    def char_length(self) -> int:
        return len(self.text)

    @property
    def clean_length(self) -> int:
        return len(self.clean_text)

    def prepend_bytes(self, _bytes: bytes) -> None:
        self._bytes = _bytes + self._bytes
        self._offset -= len(_bytes)
        self.reset()

    def append_bytes(self, _bytes: bytes) -> None:
        self._bytes += _bytes
        self.reset()

    def reset(self) -> None:
        self.__text = None
        self.__clean_text = None

    def split(self, byte_length: int) -> Tuple['Fragment', 'Fragment']:
        from gen.element.fragment import Fragment

        first = Fragment(self, self.offset, self.bytes[:byte_length])
        remainder = Fragment(self, self.offset + byte_length, self.bytes[byte_length:])
        return first, remainder

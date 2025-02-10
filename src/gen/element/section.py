"""
Section is a single concrete element. It has an offset and bytes.
The other properties are derived.
"""
from typing import Optional
from uuid import UUID
from gen.element.element import Element


def is_positive_number(value):
    """Check if a value is a positive number."""
    return isinstance(value, (int, float)) and value >= 0


class Section(Element):
    """
    A section is a single concrete element. It has an offset and bytes.
    The other properties are derived.
    """

    def __init__(self, offset: int, _bytes: bytes, uid: Optional[UUID] = None) -> None:
        """
        Initialize the section.
        Args:
            offset: the offset of the section
            _bytes: the bytes of the section
            uid: the uid of the section when loading from xdata
        """
        super().__init__(uid=uid)

        assert isinstance(_bytes, bytes), f'bytes must be a bytes object (got {type(_bytes)})'
        assert is_positive_number(offset), f'offset must be a positive number (got {type(offset)})'

        self._offset = offset
        self._bytes = _bytes

        # for caching, see reset()
        self.__text = None
        self.__clean_text = None

    def to_xdata(self) -> dict:
        """Convert the section to xdata."""
        xdata = super().to_xdata()
        xdata['offset'] = self.offset
        xdata['length'] = self.byte_length
        return xdata

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        """Create a section from xdata."""
        uid = UUID(xdata['uid'])
        offset = xdata['offset']
        length = xdata['length']
        _bytes = byte_reader.read_bytes(offset, length)
        section = cls(offset, _bytes, uid=uid)
        return section

    @property
    def offset(self) -> int:
        """Get the offset of the section."""
        return self._offset

    @property
    def bytes(self) -> bytes:
        """Get the bytes of the section."""
        return self._bytes

    @property
    def text(self) -> str:
        """Get the text of the section."""
        if self.__text is None:
            self.__text = self.bytes.decode('utf-8')
        return self.__text

    @property
    def clean_text(self) -> str:
        """Get the clean text of the section."""
        if self.__clean_text is None:
            self.__clean_text = self.normalize_text(self.text)
        return self.__clean_text

    @property
    def byte_length(self) -> int:
        """Get the byte length of the section."""
        return len(self.bytes)

    @property
    def char_length(self) -> int:
        """Get the character length of the section."""
        return len(self.text)

    @property
    def clean_length(self) -> int:
        """Get the clean length of the section."""
        return len(self.clean_text)

    def append_bytes(self, _bytes: bytes) -> None:
        """Append bytes to the section."""
        self._bytes += _bytes
        self.reset()

    def reset(self) -> None:
        """Reset the cached text and clean text."""
        self.__text = None
        self.__clean_text = None

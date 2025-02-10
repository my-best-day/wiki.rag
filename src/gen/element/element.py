"""
Define Element, an abstract base class for all elements.
"""
from typing import TYPE_CHECKING, Tuple, Optional, Dict
import re
import unicodedata
from abc import ABC
from uuid import UUID, uuid4

from xutils.encoding_utils import EncodingUtils
from xutils.byte_reader import ByteReader

if TYPE_CHECKING:  # pragma: no cover
    from gen.element.fragment import Fragment  # pragma: no cover


class Element(ABC):
    """
    Element is an abstract base class for all elements. An element provides these properties:
    - offset: the offset of the element in the file
    - bytes: the raw bytes of the element
    - text: the text of the element (bytes decoded as UTF-8)
    - clean_text: the normalized text of the element
    - byte_length: the length of the element in bytes
    - char_length: the length of the element in characters
    - clean_length: the length of the element in characters after normalizing the text
    """
    CLEAN_TEXT_PATTERN = r'[^a-zA-Z0-9\s,.!?\'"-]+'
    CLEAN_TEXT_REGEX = re.compile(CLEAN_TEXT_PATTERN)

    instances: Dict[UUID, 'Element'] = {}

    def __init__(self, uid: Optional[UUID] = None):
        if uid is None:
            uid = uuid4()
        self.uid = uid
        Element.instances[uid] = self

    def __str__(self):
        return f"{self.__class__.__name__} (uid={self.uid})"

    def to_xdata(self) -> dict:
        """Convert the element to xdata."""
        xdata = {
            'class': self.__class__.__name__,
            'uid': str(self.uid)
        }
        return xdata

    @classmethod
    def hierarchy_from_xdata(cls, xdata: dict, byte_reader: ByteReader):
        """
        Create an element from xdata.
        """
        result = Element._hierarchy_from_xdata(xdata, byte_reader)
        if result is None:
            raise ValueError(f"Unknown class: {xdata['class']}")
        return result

    @classmethod
    def _hierarchy_from_xdata(cls, xdata: dict, byte_reader: ByteReader):
        """
        Create an element from xdata.
        """
        if xdata['class'] == cls.__name__:
            return cls.from_xdata(xdata, byte_reader)
        for subclass in cls.__subclasses__():
            result = subclass._hierarchy_from_xdata(xdata, byte_reader)
            if result is not None:
                return result

    @classmethod
    def from_xdata(cls, xdata: dict, byte_reader: ByteReader):
        """Create an element from xdata."""
        raise NotImplementedError

    def resolve_dependencies(self, xdata: dict):
        """Resolved references to other elements."""
        pass

    @property
    def offset(self) -> int:
        """
        The offset of the element in the file.

        Such that open(path, "rb").seek(offset).read(byte_length) == bytes.
        """
        raise NotImplementedError

    @property
    def bytes(self) -> bytes:
        """
        The raw bytes of the element.
        """
        raise NotImplementedError

    @property
    def text(self) -> str:
        """
        The text of the element (bytes decoded as UTF-8).
        """
        raise NotImplementedError

    @property
    def clean_text(self) -> str:
        """
        The normalized text of the element.
        """
        raise NotImplementedError

    @property
    def byte_length(self) -> int:
        """
        The length of the element in bytes.
        """
        raise NotImplementedError

    @property
    def char_length(self) -> int:
        """
        The length of the element in characters.
        """
        raise NotImplementedError

    @property
    def clean_length(self) -> int:
        """
        The length of the element in characters after normalizing the text.
        """
        raise NotImplementedError

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize the text:
        - translates diacritics to their base characters
        - removes special characters
        - removes extra spaces
        - converts to lowercase
        """
        # Normalize text to NFD (Normalization Form D)
        # This splits characters with diacritics into their base characters and diacritics
        norm_text = unicodedata.normalize('NFD', text)
        # Check if the text contains diacritics
        if len(norm_text) != len(text):
            # Remove diacritics
            text = ''.join(c for c in norm_text if unicodedata.category(c) != 'Mn')
        else:
            text = norm_text
        # Remove special characters, clean spaces if needed
        text = re.sub(Element.CLEAN_TEXT_REGEX, ' ', text)
        # Normalize white spaces if the tokenizer doesn't do this for us
        text = re.sub(r"\s+", " ", text).strip()
        text = text.lower()
        return text

    def split(self, index: int, after_char: bool = False, include_first: bool = True,
              include_remainder: bool = True) -> Tuple[Optional['Fragment'], Optional['Fragment']]:
        """
        Split the element into a first and remainder fragment, adjusting the split point if
        necessary to avoid splitting in the middle of a multi-byte character.
        Args:
            byte_length: the length of the first fragment
            after_char: if True, the split point is after the character, otherwise it is before
            include_first: whether to include the first fragment
            include_remainder: whether to include the remainder fragment
        Returns:
            a tuple with the first and remainder fragment, or None if the caller does not
            want to generate one of the fragments
        """
        # import here to avoid circular import
        from gen.element.fragment import Fragment

        first_bytes, remainder_bytes = EncodingUtils.split_at(
            self.bytes,
            index,
            after_char,
            include_first,
            include_remainder
        )

        if include_first:
            first = Fragment(self, self.offset, first_bytes)
        else:
            first = None

        if include_remainder:
            offset = self.offset + len(self.bytes) - len(remainder_bytes)
            remainder = Fragment(self, offset, remainder_bytes)
        else:
            remainder = None

        return first, remainder

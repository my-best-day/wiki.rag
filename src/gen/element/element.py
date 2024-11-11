from typing import TYPE_CHECKING, Tuple, Optional
import re
import json
import unicodedata
from abc import ABC
from xutils.encoding_utils import EncodingUtils

if TYPE_CHECKING:
    from gen.element.fragment import Fragment


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

    __next_index = 0

    def __init__(self):
        self.index = Element._next_index()

    def __str__(self):
        return f"{self.__class__.__name__} (index={self.index})"

    @staticmethod
    def _next_index():
        Element.__next_index += 1
        return Element.__next_index

    def to_data(self):
        return {
            'class': self.__class__.__name__,
        }

    def to_json(self):
        return json.dumps(self.to_data())

    @classmethod
    def hierarchy_from_json(cls, json_string):
        data = json.loads(json_string)
        return cls.hierarchy_from_data(data)

    @classmethod
    def hierarchy_from_data(cls, data):
        if data['class'] == cls.__name__:
            return cls.from_data(data)
        for subclass in cls.__subclasses__():
            result = subclass.hierarchy_from_data(data)
            if result is not None:
                return result
        return None

    @classmethod
    def from_data(cls, data):
        raise NotImplementedError

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

    def split(self, byte_length: int, after_char: bool = False, include_first: bool = True,
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
        from gen.element.fragment import Fragment

        first, remainder = None, None
        # prevent splitting in the middle of a multi-byte character
        split_point = EncodingUtils.adjust_split_point(self.bytes, byte_length, after_char)

        if include_first:
            first_bytes = self.bytes[:split_point]
            first = Fragment(self, self.offset, first_bytes)

        if include_remainder:
            remainder_bytes = self.bytes[split_point:]
            remainder = Fragment(self, self.offset + split_point, remainder_bytes)

        return first, remainder

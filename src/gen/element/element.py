import re
import unicodedata
from abc import ABC


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
        self.index = Element.next_index()

    def __str__(self):
        return f"{self.__class__.__name__} (index={self.index})"

    @staticmethod
    def next_index():
        Element.__next_index += 1
        return Element.__next_index

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

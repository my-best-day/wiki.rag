#
# WIP
#
from typing import TextIO
from gen.element.element import Element


class Snippet(Element):
    """
    A snippet is an element with offset, byte length, and a file pointer.
    """

    @staticmethod
    def get_factory(file: TextIO):
        def factory(offset, byte_len, char_len, clean_len):
            return Snippet(file, offset, byte_len, char_len, clean_len)
        return factory

    def __init__(self, file: TextIO, offset: int, byte_len: int, char_len: int, clean_len: int):
        self._file = file
        self._offset = offset
        self._byte_len = byte_len
        self._char_len = char_len
        self._clean_len = clean_len

        self.__bytes = None
        self.__text = None
        self.__clean_text = None

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def byte_len(self) -> int:
        return self._byte_len

    @property
    def char_length(self) -> int:
        return self._char_len

    @property
    def clean_length(self) -> int:
        return self._clean_len

    @property
    def bytes(self) -> bytes:
        if self.__bytes is None:
            self._file.seek(self.offset)
            self.__bytes = self._file.read(self.byte_len)
        return self.__bytes

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

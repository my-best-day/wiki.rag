"""
Byte reader for reading bytes from a file at a given offset.
"""
from pathlib import Path
from typing import Union


class ByteReader:
    """
    Reads a length of bytes from a file at a given offset.
    """
    def __init__(self, path: Union[Path, str]):
        """
        Initialize the ByteReader.
        Args:
            path (Union[Path, str]): The path to the file to read.
        """
        self.path = path
        self._file = None

    @property
    def file(self):
        """Get the memoized file handle."""
        if self._file is None:
            self._file = open(self.path, "rb")
        return self._file

    def read_bytes(self, offset: int, size: int) -> bytes:
        """
        Reads the bytes from the file at the given offset.
        Args:
            offset (int): The offset to read from.
            size (int): The number of bytes to read.
        Returns:
            bytes: The bytes read from the file.
        """
        self.file.seek(offset)
        _bytes = self.file.read(size)
        return _bytes

    def cleanup(self):
        """
        Closes the file if it is open.
        Handles multiple calls.
        """
        if self._file is not None:
            self._file.close()
            self._file = None

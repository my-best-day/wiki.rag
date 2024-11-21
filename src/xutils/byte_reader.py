from pathlib import Path


class ByteReader:
    """
    Reads a length of bytes from a file at a given offset.
    """
    def __init__(self, path: Path):
        self.path = path
        self._file = None

    @property
    def file(self):
        if self._file is None:
            self._file = open(self.path, "rb")
        return self._file

    def read_bytes(self, offset: int, size: int) -> bytes:
        """reads the bytes from the file at the given offset"""
        self.file.seek(offset)
        return self.file.read(size)

    def cleanup(self):
        """closes the file if it is open. handles multiple calls."""
        if self._file is not None:
            self._file.close()
            self._file = None

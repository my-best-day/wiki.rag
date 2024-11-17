from pathlib import Path


class ByteReader:
    """
    Reads a length of bytes from a file at a given offset.
    """
    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")

    def read_bytes(self, offset: int, size: int) -> bytes:
        """reads the bytes from the file at the given offset"""
        self.file.seek(offset)
        return self.file.read(size)

    def cleanup(self):
        """closes the file if it is open. handles multiple calls."""
        if self.file is not None:
            self.file.close()
            self.file = None


def is_non_negative_int(value: int) -> bool:
    return isinstance(value, int) and value >= 0


class Chunk:
    """
    A chunk is a block of bytes with an offset we read from the input text file.

    If the chunk cut off in the middle of a paragraph, we transfer the beginning
    of the paragraph to the next chunk.
    """
    def __init__(self, offset: int, _bytes: bytes) -> None:
        """
        Create a new chunk.
        """
        assert is_non_negative_int(offset), 'offset must be a positive integer'
        assert isinstance(_bytes, bytes), 'bytes must be bytes'

        self._offset: int = offset
        self._bytes: bytes = _bytes

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def bytes(self) -> bytes:
        return self._bytes

    def prepend_bytes(self, _bytes: bytes) -> None:
        assert isinstance(_bytes, bytes), 'bytes must be bytes'

        self._bytes = _bytes + self._bytes
        self._offset -= len(_bytes)

        assert self._offset >= 0, 'offset cannot be negative'

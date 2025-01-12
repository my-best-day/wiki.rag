from gen.element.element import Element


class TestByteReader:
    @staticmethod
    def from_element(element: Element) -> 'TestByteReader':
        _bytes = b' ' * element.offset + element.bytes
        return TestByteReader(_bytes)

    def __init__(self, _bytes: bytes) -> None:
        self._bytes = _bytes

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self._bytes[offset:offset + length]

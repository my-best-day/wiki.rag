"""
FlatArticle is a flat representation of an article.
It holds the body text as a whole, not broken into paragraphs.
"""
from uuid import UUID
from gen.element.element import Element
from xutils.byte_reader import ByteReader
from xutils.attribute_proxy import AttributeProxy


class FlatArticle(Element):
    """
    A flat article is a flat representation of an article.
    It holds the body text as a whole, not broken into paragraphs.
    """
    def __init__(
        self,
        uid: UUID,
        header_offset: int,
        header_byte_length: int,
        body_offset: int,
        body_byte_length: int,
        byte_reader: ByteReader
    ) -> None:
        """
        Initialize the flat article.
        """
        super().__init__(uid=uid)
        self._header_offset: int = header_offset
        self._header_byte_length: int = header_byte_length
        self._body_offset: int = body_offset
        self._body_byte_length: int = body_byte_length

        self._byte_reader: ByteReader = byte_reader

        self.__header_bytes = None
        self.__body_bytes = None

        self.header = AttributeProxy(self, '_header')
        self.body = AttributeProxy(self, '_body')

    @property
    def _header_bytes(self):
        if self.__header_bytes is None:
            self.__header_bytes = \
                self._byte_reader.read_bytes(self._header_offset, self._header_byte_length)
        return self.__header_bytes

    @property
    def _header_text(self):
        header_text = self._header_bytes.decode('utf-8')
        return header_text

    @property
    def _header_char_length(self):
        return len(self._header_text)

    @property
    def _body_bytes(self):
        if self.__body_bytes is None:
            self.__body_bytes = \
                self._byte_reader.read_bytes(self._body_offset, self._body_byte_length)
        return self.__body_bytes

    @property
    def _body_text(self):
        body_text = self._body_bytes.decode('utf-8')
        return body_text

    @property
    def _body_char_length(self):
        return len(self._body_text)

    @property
    def offset(self):
        return self._header_offset

    @property
    def bytes(self):
        _bytes = self._header_bytes + self._body_bytes
        return _bytes

    @property
    def text(self) -> str:
        text = self.bytes.decode('utf-8')
        return text

    @property
    def clean_text(self) -> str:
        clean_text = self.normalize_text(self.text)
        return clean_text

    @property
    def byte_length(self) -> int:
        return len(self.bytes)

    @property
    def char_length(self) -> int:
        return len(self.text)

    @property
    def clean_length(self) -> int:
        return len(self.clean_text)

    def to_xdata(self) -> dict:
        xdata = super().to_xdata()
        xdata.update({
            "header_offset": self._header_offset,
            "header_byte_length": self._header_byte_length,
            "body_offset": self._body_offset,
            "body_byte_length": self._body_byte_length
        })
        return xdata

    @classmethod
    def from_xdata(cls, xdata: dict, byte_reader: ByteReader) -> "FlatArticle":
        return cls(
            uid=UUID(xdata["uid"]),
            header_offset=xdata["header_offset"],
            header_byte_length=xdata["header_byte_length"],
            body_offset=xdata["body_offset"],
            body_byte_length=xdata["body_byte_length"],
            byte_reader=byte_reader
        )

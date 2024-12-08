from uuid import UUID
from typing import Optional
from gen.element.element import Element
from gen.element.flat.flat_article import FlatArticle
from xutils.byte_reader import ByteReader


class FlatExtendedSegment(Element):
    def __init__(self, uid: UUID, article_uid: UUID, offset: int, byte_length: int,
                 byte_reader: Optional[ByteReader]) -> None:
        super().__init__(uid)
        self.article_uid: UUID = article_uid
        self._offset: int = offset
        self._byte_length: int = byte_length
        self._byte_reader: ByteReader = byte_reader

        # for caching, see reset()
        self._bytes = None

    @property
    def article(self) -> "FlatArticle":
        return Element.instances[self.article_uid]

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def bytes(self) -> bytes:
        if self._bytes is None:
            self._bytes = self._read_bytes()
        return self._bytes

    def _read_bytes(self) -> bytes:
        return self._byte_reader.read_bytes(self.offset, self._byte_length)

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
            "article_uid": str(self.article_uid),
            "offset": self.offset,
            "byte_length": self._byte_length
        })
        return xdata

    @classmethod
    def from_xdata(cls, xdata: dict, byte_reader: ByteReader) -> "FlatExtendedSegment":
        return cls(
            uid=UUID(xdata["uid"]),
            article_uid=UUID(xdata["article_uid"]),
            offset=xdata["offset"],
            byte_length=xdata["byte_length"],
            byte_reader=byte_reader
        )

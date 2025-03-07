"""
FlatExtendedSegment is a flat representation of an ExtendedSegment.
It has the header and the text (not broken into paragraphs).
"""
from uuid import UUID
from gen.element.element import Element
from gen.element.flat.flat_article import FlatArticle
from xutils.byte_reader import ByteReader


class FlatExtendedSegment(Element):
    """
    FlatExtendedSegment is a flat representation of an ExtendedSegment.
    It has the header and the text (not broken into paragraphs).
    """
    def __init__(
        self,
        uid: UUID,
        article_uid: UUID,
        offset: int,
        byte_length: int,
    ) -> None:
        """
        Initialize the flat extended segment.
        """
        super().__init__(uid)
        self.article_uid: UUID = article_uid
        self._offset: int = offset
        self._byte_length: int = byte_length
        self._byte_reader: ByteReader = None

        # for caching, see reset()
        self._bytes = None

    def set_byte_reader(self, byte_reader: ByteReader) -> None:
        """Set the byte reader."""
        self._byte_reader = byte_reader

    @property
    def article(self) -> "FlatArticle":
        """The article the segment belongs to."""
        return Element.instances[self.article_uid]

    @property
    def offset(self) -> int:
        """The offset of the segment."""
        return self._offset

    @property
    def bytes(self) -> bytes:
        """The bytes of the segment."""
        if self._bytes is None:
            self._bytes = self._read_bytes()
        return self._bytes

    def _read_bytes(self) -> bytes:
        """Read the bytes of the segment."""
        return self._byte_reader.read_bytes(self.offset, self._byte_length)

    @property
    def text(self) -> str:
        """The text of the segment."""
        text = self.bytes.decode('utf-8')
        return text

    @property
    def clean_text(self) -> str:
        """The clean text of the segment."""
        clean_text = self.normalize_text(self.text)
        return clean_text

    @property
    def byte_length(self) -> int:
        """The byte length of the segment."""
        return len(self.bytes)

    @property
    def char_length(self) -> int:
        """The character length of the segment."""
        return len(self.text)

    @property
    def clean_length(self) -> int:
        """The clean length of the segment."""
        return len(self.clean_text)

    def to_xdata(self) -> dict:
        """Convert the segment to xdata."""
        xdata = super().to_xdata()
        xdata.update({
            "article_uid": str(self.article_uid),
            "offset": self.offset,
            "byte_length": self._byte_length
        })
        return xdata

    @classmethod
    def from_xdata(cls, xdata: dict, byte_reader: ByteReader) -> "FlatExtendedSegment":
        """Create a flat extended segment from xdata."""
        flat_extended_segment = cls(
            uid=UUID(xdata["uid"]),
            article_uid=UUID(xdata["article_uid"]),
            offset=xdata["offset"],
            byte_length=xdata["byte_length"],
        )
        flat_extended_segment.set_byte_reader(byte_reader)
        return flat_extended_segment

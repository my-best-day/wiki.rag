"""
A document with a title and a body.
"""
from typing import NamedTuple
from xutils.byte_reader import ByteReader
from xutils.attribute_proxy import AttributeProxy


class PlotRecord(NamedTuple):
    """
    A record of a plot.
    A compact representation of a plot.
    """
    uid: str
    title: bytes
    offset: int
    byte_length: int


class Plot:
    """
    A plot is a document with a title and a body.
    Combines offset, length, and byte_reader to get the text.
    """
    def __init__(self, plot_record: PlotRecord, byte_reader: ByteReader):
        self.plot_record = plot_record
        self.byte_reader = byte_reader
        self.header = AttributeProxy(self, '_header')

    def __getattr__(self, name):
        """Proxy to the attributes of the plot record."""
        return getattr(self.plot_record, name)

    @property
    def bytes(self):
        """The bytes of the plot."""
        return self.byte_reader.read_bytes(self.offset, self.byte_length)

    @property
    def text(self):
        """The text of the plot."""
        return self.bytes.decode('utf-8')

    @property
    def _header_bytes(self):
        """
        The bytes of the header.
        With the help of the header proxy, access by plot.header.bytes
        """
        return self.plot_record.title

    @property
    def _header_text(self):
        """
        The text of the header.
        With the help of the header proxy, access by plot.header.text
        """
        result = self._header_bytes.decode('utf-8')
        return result

    @property
    def _header_char_length(self):
        """
        The character length of the header.
        With the help of the header proxy, access by plot.header.char_length
        """
        return len(self._header_text)

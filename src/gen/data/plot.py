from typing import NamedTuple
from xutils.byte_reader import ByteReader
from xutils.attribute_proxy import AttributeProxy

# TODO: rename to PlotRecord to match SegmentRecord


class PlotData(NamedTuple):
    uid: str
    title: bytes
    offset: int
    byte_length: int


class Plot:
    def __init__(self, plot_data: PlotData, byte_reader: ByteReader):
        self.plot_data = plot_data
        self.byte_reader = byte_reader
        self.header = AttributeProxy(self, '_header')

    def __getattr__(self, name):
        return getattr(self.plot_data, name)

    @property
    def bytes(self):
        return self.byte_reader.read_bytes(self.offset, self.byte_length)

    @property
    def text(self):
        return self.bytes.decode('utf-8')

    @property
    def _header_bytes(self):
        return self.plot_data.title

    @property
    def _header_text(self):
        result = self._header_bytes.decode('utf-8')
        return result

    @property
    def _header_char_length(self):
        return len(self._header_text)

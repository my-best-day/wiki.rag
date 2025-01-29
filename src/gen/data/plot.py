from typing import NamedTuple
from xutils.byte_reader import ByteReader

# TODO: rename to PlotRecord to match SegmentRecord


class PlotData(NamedTuple):
    uid: str
    title: str
    offset: int
    byte_length: int


class Plot:
    def __init__(self, plot_data: PlotData, byte_reader: ByteReader):
        self.plot_data = plot_data
        self.byte_reader = byte_reader

    def __getattr__(self, name):
        return getattr(self.plot_data, name)

    @property
    def bytes(self):
        return self.byte_reader.read_bytes(self.offset, self.byte_length)

    @property
    def text(self):
        return self.bytes.decode('utf-8')

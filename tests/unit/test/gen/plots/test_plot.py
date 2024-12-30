import unittest
from gen.plots.plot import Plot, PlotData
from ..element.byte_reader_tst import TestByteReader


class TestPlot(unittest.TestCase):
    def test_document_data(self):
        uid = "uid"
        title = "title"
        offset = 0
        byte_length = 100
        doc_data = PlotData(uid, title, offset, byte_length)
        self.assertEqual(doc_data.uid, uid)
        self.assertEqual(doc_data.title, title)
        self.assertEqual(doc_data.offset, offset)
        self.assertEqual(doc_data.byte_length, byte_length)

    def test_plot(self):
        uid = "uid"
        title = "title"
        offset = 4
        byte_length = 5
        doc_data = PlotData(uid, title, offset, byte_length)
        byte_reader = TestByteReader(b'01234567890')
        plot = Plot(doc_data, byte_reader)
        self.assertEqual(plot.uid, uid)
        self.assertEqual(plot.title, title)
        self.assertEqual(plot.offset, offset)
        self.assertEqual(plot.byte_length, byte_length)
        self.assertEqual(plot.bytes, b'45678')
        self.assertEqual(plot.text, '45678')


if __name__ == '__main__':
    unittest.main()

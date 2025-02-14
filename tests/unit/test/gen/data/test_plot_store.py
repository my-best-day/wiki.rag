import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from gen.data.plot_store import PlotStore
from gen.data.plot import Plot, PlotRecord
from ...xutils.byte_reader_tst import TestByteReader


class TestPlotStore(unittest.TestCase):

    def setUp(self):
        self._bytes = '0' * 8 + '1' * 10
        self.test_byte_reader = TestByteReader(self._bytes)
        self.mock_plot_record1 = PlotRecord(0, b"plot1", 0, 8)
        self.mock_plot_record2 = PlotRecord(1, b"plot2", 8, 20)
        self.mock_plot1 = Plot(self.mock_plot_record1, self.test_byte_reader)
        self.mock_plot2 = Plot(self.mock_plot_record2, self.test_byte_reader)
        self.mock_plots = [self.mock_plot1, self.mock_plot2]

    def test_init(self):
        """Test the constructor"""
        # Silly. For completeness
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        self.assertEqual(plot_store.plots_dir, plots_dir)

    def test_load_documents(self):
        """Test load_documents"""
        # Test that it returns the output of load_plots
        plots_dir = Path("/dev/null")
        self.plot_store = PlotStore(plots_dir)

        mock_plots = self.mock_plots
        with patch("gen.data.plot_store.PlotStore.load_plots", return_value=mock_plots):
            documents = self.plot_store.load_documents()
            self.assertEqual(len(documents), 2)
            self.assertEqual(documents, mock_plots)

    def test_load_plots(self):
        """Test load_plots"""
        # Test that:
        #  the byte reader is created with the correct path
        #  the result of load_plots is a list of Plot objects based on the result
        #     of load_plot_record_list
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        test_byte_reader = TestByteReader(self._bytes)
        mock_plot_record_list = [self.mock_plot_record1, self.mock_plot_record2]
        _bytes = self._bytes
        with patch("gen.data.plot_store.PlotStore.create_byte_reader",
                   return_value=test_byte_reader):
            with patch("gen.data.plot_store.PlotStore.load_plot_record_list",
                       return_value=mock_plot_record_list):
                plots = plot_store.load_plots()
            self.assertEqual(len(plots), 2)
            self.assertEqual(plots[0].plot_record, self.mock_plot_record1)
            self.assertEqual(plots[1].plot_record, self.mock_plot_record2)
            self.assertEqual(plots[0].bytes, _bytes[0:8])
            self.assertEqual(plots[1].bytes, _bytes[8:20])

    def test_load_plot_record_list(self):
        """Test load_plot_record_list"""
        # Test that method returns the content returned from pd.read_csv
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        mock_plot_record_list = [self.mock_plot_record1, self.mock_plot_record2]
        mock_plot_record_dict_list = \
            [plot_record._asdict() for plot_record in mock_plot_record_list]
        mock_plots_df = pd.DataFrame(mock_plot_record_dict_list)
        # convert the title column to strings like "b'<title>'"
        mock_plots_df['title'] = mock_plots_df['title'].apply(lambda x: str(x))

        # test that if the file does not exists, an error is raised
        with self.assertRaises(FileNotFoundError):
            plot_store.load_plot_record_list()

        # inhibit the file not found error so we can test the rest of the code
        with patch("pathlib.Path.exists", return_value=True):
            with patch("gen.data.plot_store.pd.read_csv", return_value=mock_plots_df):
                plot_record_list = plot_store.load_plot_record_list()
                self.assertEqual(plot_record_list, mock_plot_record_list)

    def test_write_plots_dataframe(self):
        """Test write_plots_dataframe"""
        # Test that plot_df.to_csv is called with the expected path
        mock_dataframe = MagicMock()
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        expected_path = plot_store.get_plots_data_path()
        plot_store.write_plots_dataframe(mock_dataframe)
        mock_dataframe.to_csv.assert_called_once_with(expected_path, index=False)

    def test_build_plots_dataframe(self):
        """Test build_plots_dataframe"""
        # Test that the dataframe is built from the plot record list
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        mock_plot_record_list = [self.mock_plot_record1, self.mock_plot_record2]
        mock_plot_record_dict_list = \
            [plot_record._asdict() for plot_record in mock_plot_record_list]
        mock_plots_df = pd.DataFrame(mock_plot_record_dict_list)
        plots_df = plot_store.build_plots_dataframe(mock_plot_record_list)
        pd.testing.assert_frame_equal(plots_df, mock_plots_df)

    def test_create_byte_reader(self):
        """Test create_byte_reader"""
        # test that the byte reader is initialized with the expected path
        plots_dir = Path("/dev/null")
        plot_store = PlotStore(plots_dir)
        mock_byte_reader_class = MagicMock()
        mock_path = Path("/dev/null/plots")
        with patch("gen.data.plot_store.ByteReader", new=mock_byte_reader_class):
            byte_reader = plot_store.create_byte_reader(mock_path)
            self.assertEqual(byte_reader, mock_byte_reader_class.return_value)
            mock_byte_reader_class.assert_called_once_with(mock_path)

    def test_get_plots_text_path(self):
        """Test get_plots_text_path"""
        # silly. test that the path is returned correctly
        plots_dir = Path("/dev/null")
        expected_path = plots_dir / 'plots'
        plot_store = PlotStore(plots_dir)
        self.assertEqual(plot_store.get_plots_text_path(), expected_path)

    def test_get_plots_data_path(self):
        """Test get_plots_data_path"""
        # silly. test that the path is returned correctly
        plots_dir = Path("/dev/null")
        expected_path = plots_dir / 'plots_data.csv'
        plot_store = PlotStore(plots_dir)
        self.assertEqual(plot_store.get_plots_data_path(), expected_path)


if __name__ == "__main__":
    unittest.main()

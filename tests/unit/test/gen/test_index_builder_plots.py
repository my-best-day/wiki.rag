import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch, call

from gen.data.plot import PlotRecord
from gen.index_builder_plots import IndexBuilderPlots


# we read titles with .read().splitlines() which eliminate the newlines
# whereas we are plots with .readline() which preserves them.
# hence the different handling of newlines between titles and plot_lines.

titles = [
    b'Animal Farm',
    b'A Clockwork Orange (novel)',
    b'The Plague',
]
titles_content = b'\n'.join(titles)

plot_lines = [
    b'Old Major, the old boar on the Manor Farm.\n',
    b'When Major dies, two young pigs.\n',
    b'The animals revolt and drive the drunken.\n',
    b'<EOS>\n',

    b'Alex is a 15-year-old living in near-future dystopian.\n',
    b'Alex\'s friends ("Bonk" in the novel\'s Anglo-Russian slang).\n',
    b'Characterized as a sociopath and a hardened juvenile delinquent.\n',
    b'<EOS>\n',

    b'The text of The Plague is divided into five parts.\n',
    b'In the town of Oran, thousands of rats, initially unnoticed.\n',
    b'<EOS>\n'
]

plots_content = b''.join(plot_lines)


class TestIndexBuilderPlots(unittest.TestCase):

    def setUp(self):
        self.plots_dir = Path("plot_dir")

        self.plot_record_list = []

        plot_offset = 0
        plot_length = 0
        for line in plot_lines:
            length = len(line)

            if line == b'<EOS>\n':
                plot_index = len(self.plot_record_list)
                title = titles[plot_index]
                plot_record = PlotRecord(plot_index, title, plot_offset, plot_length)
                self.plot_record_list.append(plot_record)
                plot_offset = plot_offset + plot_length + len(line)
                plot_length = 0
            else:
                # excludes <EOS>
                plot_length += length

    @patch.object(IndexBuilderPlots, "_build_index")
    def test_build_index(self, mock_build_index):

        mock_titles_file = MagicMock()
        mock_titles_file.read.return_value = titles_content

        open_1st_enter = MagicMock()
        open_1st_enter.__enter__.return_value = mock_titles_file

        mock_plots_file = MagicMock()
        mock_plots_file.read.return_value = plots_content  # not used

        open_2nd_enter = MagicMock()
        open_2nd_enter.__enter__.return_value = mock_plots_file

        mock_build_index.return_value = self.plot_record_list

        side_effect = [open_1st_enter, open_2nd_enter]

        with patch("builtins.open", side_effect=side_effect) as mock_open_func:
            titles_file_path = self.plots_dir / "titles"
            plots_file_path = self.plots_dir / "plots"

            index_builder = IndexBuilderPlots(self.plots_dir)
            plot_record_list = index_builder.build_index()

            mock_open_func.assert_has_calls([
                call(titles_file_path, "rb"),  # First call
                call(plots_file_path, "rb")    # Second call
            ])

            mock_build_index.assert_called_once_with(titles, mock_plots_file)
            self.assertEqual(plot_record_list, self.plot_record_list)

    def test_protected_build_index(self):
        offsets = [plot.offset for plot in self.plot_record_list]
        offsets.append(None)

        plots_file_handle = MagicMock()
        plots_file_handle.tell.side_effect = offsets
        plots_file_handle.readline.side_effect = plot_lines

        with patch.object(IndexBuilderPlots, "LOG_INTERVAL", 3):
            index_builder = IndexBuilderPlots(self.plots_dir)
            plot_record_list = index_builder._build_index(titles, plots_file_handle)

        self.assertEqual(plot_record_list, self.plot_record_list)


if __name__ == "__main__":
    unittest.main()

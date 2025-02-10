"""
Create an index of plots.
PlotRecord holds the plot's index, title, offset, and byte length.
"""
import logging
from typing import List
from pathlib import Path
from gen.data.plot import PlotRecord

logger = logging.getLogger(__name__)


class IndexBuilderPlots:
    """
    Create an index of plots.
    PlotRecord holds the plot's index, title, offset, and byte length.
    """
    LOG_INTERVAL = 10000

    def __init__(
        self,
        plots_dir: Path
    ):
        super().__init__()
        self.plots_dir = plots_dir

    def build_index(self) -> List[PlotRecord]:
        """
        Opens the plots (text) file and the titles file.
        And call _build_index to build the index of plots.
        """
        plot_dir = self.plots_dir
        plots_file_path = plot_dir / "plots"
        titles_file_path = plot_dir / "titles"

        with open(titles_file_path, "rb") as titles_file:
            titles = titles_file.read().splitlines()

        with open(plots_file_path, "rb") as plots_handle:
            return self._build_index(titles, plots_handle)

    def _build_index(self, titles: List[str], plots_handle):
        """
        Builds the index of plots.
        Keeps track of the offset and byte length of the plots.
        """
        plot_record_list: List[PlotRecord] = []

        offset: int = 0
        byte_length = 0

        new_plot = True
        while True:
            if new_plot:
                offset = plots_handle.tell()  # x
                byte_length = 0
                new_plot = False

            try:
                line = plots_handle.readline()
            except StopIteration:
                line = b''

            if not line:
                break

            elif line == b'<EOS>\n':
                uid = len(plot_record_list)
                title = titles[uid]
                plot_record = PlotRecord(uid, title, offset, byte_length)
                plot_record_list.append(plot_record)
                if len(plot_record_list) % self.LOG_INTERVAL == 0:
                    logger.info("processed %d / %d plots", len(plot_record_list), len(titles))
                new_plot = True

            else:
                line_length = len(line)
                byte_length += line_length

        return plot_record_list

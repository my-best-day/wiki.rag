"""
Build an index of articles and their paragraphs which includes the article/paragraph
offset in the file (in bytes, suitable for file_handle.seek()), and byte, text, and clean-text
lengths. Byte length is used to read the text from the file and clean-text length to calculate
segments for encoding / embedding

The implementation is more complicated than it should be because of some
experiments I did with the Chainable pattern and parallelization. This is
a learning exercise. The code could be much simpler.

Here we have
- IndexBuilder: builds the index (articles and paragraphs)
- IndexValidator: validates the offsets and byte lengths
- IndexDumper: dumps the index in a human readable format
"""
import logging
from typing import List
from pathlib import Path
from gen.data.plot import PlotData

logger = logging.getLogger(__name__)


class IndexBuilderPlots:
    LOG_INTERVAL = 10000

    def __init__(
        self,
        plots_dir: Path
    ):
        super().__init__()
        self.plots_dir = plots_dir

    def build_index(self) -> List[PlotData]:
        plot_dir = self.plots_dir
        plots_file_path = plot_dir / "plots"
        titles_file_path = plot_dir / "titles"

        with open(titles_file_path, "rb") as titles_file:
            titles = titles_file.read().splitlines()

        with open(plots_file_path, "rb") as plots_handle:
            return self._build_index(titles, plots_handle)

    def _build_index(self, titles: List[str], plots_handle):
        plot_data_list: List[PlotData] = []

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
                uid = len(plot_data_list)
                title = titles[uid]
                plot_data = PlotData(uid, title, offset, byte_length)
                plot_data_list.append(plot_data)
                if len(plot_data_list) % self.LOG_INTERVAL == 0:
                    logger.info(f"processed {len(plot_data_list)} / {len(titles)} plots")
                new_plot = True

            else:
                line_length = len(line)
                byte_length += line_length

        return plot_data_list

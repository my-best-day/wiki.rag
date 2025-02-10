"""
PlotStore is a store for plots.
"""
import logging
from pathlib import Path
from typing import List
import pandas as pd

from gen.data.plot import PlotRecord, Plot
from xutils.byte_reader import ByteReader

logger = logging.getLogger(__name__)


class PlotStore:
    """
    A store for plots.
    """
    def __init__(self, plots_dir: str):
        """
        Initialize the plot store.
        """
        plots_dir = Path(plots_dir)
        self.plots_dir = plots_dir

    def load_documents(self):
        """Load the documents from the plots text file."""
        documents = self.load_plots()
        return documents

    def load_plots(self):
        """Load the plots from the plots text file."""
        plots_text_path = self.get_plots_text_path()
        byte_reader = ByteReader(plots_text_path)
        plot_record_list = self.load_plot_record_list()
        plot_list = [Plot(plot_record, byte_reader) for plot_record in plot_record_list]
        return plot_list

    def load_plot_record_list(self):
        """Load the plot records from the plots data file."""
        plots_data_path = self.get_plots_data_path()
        if not plots_data_path.exists():
            raise FileNotFoundError(f"Plots data path {plots_data_path} does not exist")
        plots_df = pd.read_csv(plots_data_path, index_col=False)
        # titles are stored as b'title' and are loaded as strings like "b'title'"
        plots_df['title'] = plots_df['title'].apply(lambda x: eval(x))
        plot_record_list = list(plots_df.itertuples(index=False, name="PlotRecord"))
        return plot_record_list

    def write_plots_dataframe(self, plots_df: pd.DataFrame):
        """Write the plots dataframe to the plots data file."""
        plots_data_path = self.get_plots_data_path()
        plots_df.to_csv(plots_data_path, index=False)

    @staticmethod
    def build_plots_dataframe(plot_record_list: List[PlotRecord]):
        """Build a dataframe from a list of plot records."""
        plot_records = [plot_record._asdict() for plot_record in plot_record_list]
        plots_df = pd.DataFrame(plot_records)
        return plots_df

    def get_plots_text_path(self):
        """The path to the plots text file."""
        path = self.plots_dir / "plots"
        return path

    def get_plots_data_path(self):
        """The path to the plots store file."""
        path = self.plots_dir / "plots_data.csv"
        return path

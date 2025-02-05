import logging
import pandas as pd
from pathlib import Path
from typing import List

from gen.data.plot import PlotData, Plot
from xutils.byte_reader import ByteReader

logger = logging.getLogger(__name__)


class PlotStore:
    def __init__(self, plots_dir: Path):
        self.plots_dir = plots_dir

    def load_documents(self):
        documents = self.load_plots()
        return documents

    def load_plots(self):
        plots_text_path = self.get_plots_text_path()
        byte_reader = ByteReader(plots_text_path)
        plot_data_list = self.load_plot_data_list()
        plot_list = [Plot(plot_data, byte_reader) for plot_data in plot_data_list]
        return plot_list

    def load_plot_data_list(self):
        plots_data_path = self.get_plots_data_path()
        plots_df = pd.read_csv(plots_data_path, index_col=False)
        plot_data_list = list(plots_df.itertuples(index=False, name="PlotData"))
        return plot_data_list

    def write_plots_dataframe(self, plots_df: pd.DataFrame):
        plots_data_path = self.get_plots_data_path()
        plots_df.to_csv(plots_data_path, index=False)

    @staticmethod
    def build_plots_dataframe(plot_data_list: List[PlotData]):
        plot_records = [plot_data._asdict() for plot_data in plot_data_list]
        plots_df = pd.DataFrame(plot_records)
        return plots_df

    def get_plots_text_path(self):
        path = self.plots_dir / "plots"
        return path

    def get_plots_data_path(self):
        path = self.plots_dir / "plots_data.csv"
        return path

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
import argparse
import logging
from pathlib import Path
from pandas import DataFrame

from gen.data.plot import PlotData, Plot
from xutils.byte_reader import ByteReader
from gen.index_builder_plots import IndexBuilderPlots

logger = logging.getLogger(__name__)


def list_long_and_short_plots(plots_df: DataFrame):
    # get the 5 shortest and 5 longest plots
    short_plots = plots_df.nsmallest(5, 'byte_length')
    long_plots = plots_df.nlargest(5, 'byte_length')
    byte_reader = ByteReader(args.plots_dir / "plots")

    for i, plot_array in enumerate(short_plots.values):
        plot_data = PlotData(*plot_array)
        plot = Plot(plot_data, byte_reader)
        print(f"Shortest plot {i}: {plot.uid}:  {plot.title}: {plot.byte_length} bytes")
        print(plot.bytes[:200])

    for i, plot_array in enumerate(long_plots.values):
        plot_data = PlotData(*plot_array)
        plot = Plot(plot_data, byte_reader)
        print(f"Longest plot {i}: {plot.uid}:  {plot.title}: {plot.byte_length} bytes")
        print(plot.bytes[:200])


def main(args):
    plots_dir = args.plots_dir
    builder: IndexBuilderPlots = IndexBuilderPlots(plots_dir)

    plot_data_list = builder.build_index()

    plot_records = [plot_data._asdict() for plot_data in plot_data_list]
    plots_df = DataFrame(plot_records)
    logger.info(plots_df['byte_length'].describe())
    plots_df.to_csv(args.plots_dir / "plots_data.csv", index=False)

    if args.debug:
        list_long_and_short_plots(plots_df)

    print(f"Done. {len(plot_data_list)} plots")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    # parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-pd", "--plots-dir", type=str, default="ignore/plots")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)

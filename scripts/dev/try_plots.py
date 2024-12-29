#!/usr/bin/env python

import argparse
import logging
from pathlib import Path

from xutils.byte_reader import ByteReader
from gen.plots.plot import DocumentData, Plot

logger = logging.getLogger(__name__)


def show_plot(plot_dir, index, show_full_text):
    plot_data_file_path = plot_dir / "plots_data.csv"
    plot_file_path = plot_dir / "plots"

    with open(plot_data_file_path, "rt") as plot_data_file:
        plot_data_lines = plot_data_file.readlines()
    plot_data_lines.pop(0)
    plot_line = plot_data_lines[index]
    plot_record = plot_line.split(",")
    plot_record[2] = int(plot_record[2])
    plot_record[3] = int(plot_record[3])
    plot_data = DocumentData(*plot_record)
    byte_reader = ByteReader(plot_file_path)
    plot = Plot(plot_data, byte_reader)
    print(f"plot {index}: {plot.uid}:  {plot.title}: {plot.byte_length} bytes")
    text = plot.text()
    if not show_full_text:
        text = text[:200]
    print(text)


def main(args):
    show_plot(args.plots_dir, args.index, args.full)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("index", type=int, help="Index of the plot to show")
    parser.add_argument("--plots-dir", type=str, default="ignore/plots")
    parser.add_argument("--full", default=False, action="store_true")
    args = parser.parse_args()

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)

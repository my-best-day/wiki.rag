#!/usr/bin/env python
"""
Compare the bytes read from the plot file with the offset and length from the
segment records with the bytes used while creating the segments.
This requires a json dump file which needs to be created by the segment
builder - uncomment the line that calls dump_plot_segment_list_list()
"""
import logging
import argparse
from pathlib import Path

from gen.segment_verifier import SegmentVerifier
from gen.data.segment_record_store import SegmentRecordStore

logger = logging.getLogger(__name__)


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("--mode", type=str, default=None, required=True,
                        choices=["random", "first", "all", "document", "segment"])
    parser.add_argument("-n", "--number", type=int, default=None, required=True)
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    return args


def main():
    args = parse_args()
    plots_dir = args.plots_dir
    max_len = args.max_len
    mode = args.mode
    number = args.number

    text_file_path = plots_dir / "plots"
    segment_record_store = SegmentRecordStore(plots_dir / "plots", max_len)
    segment_dump_path = plots_dir / f"segments_{max_len}.json"

    SegmentVerifier.verify_files(
        text_file_path,
        segment_record_store,
        segment_dump_path,
        mode,
        number
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

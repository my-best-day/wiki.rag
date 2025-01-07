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

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("--dump-segments", default=False, action="store_true",
                        help="Dump segment bytes to a json file to be used by verify_segments.py")
    parser.add_argument("-d", "--debug", default=False, action="store_true")
    parser.add_argument("--mode", type=str, default=None, required=True,
                        choices=["random", "first", "all", "document", "segment"])
    parser.add_argument("-n", "--number", type=int, default=None, required=True)
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.text is None:
        parser.error("Please provide the path to the text file")
    text = Path(args.text)
    if not text.exists():
        parser.error(f"File {args.text} not found")

    if args.path_prefix is None:
        parser.error("Please provide the path prefix")

    if args.max_len is None:
        parser.error("Please provide the maximum segment length")

    return args


def main():
    args = parse_args()

    path_prefix = args.path_prefix
    max_len = args.max_len
    mode = args.mode
    number = args.number

    text_file_path = args.text
    segment_file_path = f"{path_prefix}_{max_len}_flat_segments.json"
    segment_dump_path = f"{args.path_prefix}_{max_len}_flat_segments_dump.json"

    SegmentVerifier.verify_files(
        text_file_path,
        segment_file_path,
        segment_dump_path,
        mode,
        number
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

#!/usr/bin/env python
"""
Compare the bytes read from the plot file with the offset and length from the
segment records with the bytes used while creating the segments.
This requires a json dump file which needs to be created by the segment
builder - uncomment the line that calls dump_plot_segment_list_list()
"""
import json
import random
import logging
import argparse
from pathlib import Path
from typing import List
import pandas as pd

from xutils.byte_reader import ByteReader

logger = logging.getLogger(__name__)


def verify_random_segments(plots_dir, n, plot_segment_list_list, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    # keep: sample_records = segment_records[:10]
    sample_records = random.sample(segment_records, n)
    verify_records(plot_segment_list_list, sample_records, byte_reader)


def verify_first_of_firsts(plots_dir, n, plot_segment_list_list, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    # keep: sample_records = segment_records[:10]
    sample_records = []
    for record in segment_records:
        # relative-index == 0 -> first segment of plot
        if record[2] == 0:
            sample_records.append(record)
            if len(sample_records) >= n:
                break

    verify_records(plot_segment_list_list, sample_records, byte_reader)


def verify_all_segments(plots_dir, plot_segment_list_list, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    verify_records(plot_segment_list_list, segment_records, byte_reader)


def verify_plot(plots_dir, n, plot_segment_list_list, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    sample_records = []
    for record in segment_records:
        if record[1] == n:
            sample_records.append(record)
        elif len(sample_records) > 0:
            break

    verify_records(plot_segment_list_list, sample_records, byte_reader)


def verify_segment(plots_dir, n, plot_segment_list_list, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    sample_records = [segment_records[n]]

    verify_records(plot_segment_list_list, sample_records, byte_reader)


def verify_records(plot_segment_list_list, sample_records, byte_reader):
    for (seg_ind, plot_ind, rel_ind, offset, length) in sample_records:
        reader_bytes = byte_reader.read_bytes(offset, length)
        plot_segment_list = plot_segment_list_list[plot_ind]
        segment_bytes = plot_segment_list[rel_ind]

        is_match = segment_bytes == reader_bytes
        if is_match:
            logger.debug("+ segment %s of plot %s rel index %s match",
                         seg_ind, plot_ind, rel_ind)
        else:
            logger.info("""
- segment %s of plot %s rel index %s does not match

expected: %s

actual  : %s
            """, seg_ind, plot_ind, rel_ind, segment_bytes, reader_bytes)


# seg_index, plot_index, rel_index, offset, length
def read_segment_records(plots_dir: str, max_len: int) -> List[List[int]]:
    """reads segment records from a csv file"""
    segment_file_path = plots_dir / f"segments_{max_len}.csv"
    segment_df = pd.read_csv(segment_file_path, index_col=False)
    segment_records = segment_df.values.tolist()
    return segment_records


def read_segment_dump(plots_dir: Path, max_len: int) -> List[List[bytes]]:
    """reads segment strings from a json file, converts them to bytes"""
    segment_file_path = plots_dir / f"segments_{max_len}.json"
    with open(segment_file_path, 'r') as json_file:
        plot_str_segment_list_list = json.load(json_file)

    plot_byte_segment_list_list = convert_segment_strings_to_bytes(
        plot_str_segment_list_list
    )
    return plot_byte_segment_list_list


def convert_segment_strings_to_bytes(
    plot_str_segment_list_list: List[List[str]]
) -> List[List[bytes]]:

    plot_byte_segment_list_list = [
        [segment.encode('utf-8') for segment in plot_segment_list]
        for plot_segment_list in plot_str_segment_list_list
    ]
    return plot_byte_segment_list_list


def main(args):
    segment_records = read_segment_records(args.plots_dir, args.max_len)
    plot_segment_list_list = read_segment_dump(args.plots_dir, args.max_len)
    if args.mode == "random":
        verify_random_segments(
            args.plots_dir,
            args.number,
            plot_segment_list_list,
            segment_records
        )
    elif args.mode == "first":
        verify_first_of_firsts(
            args.plots_dir,
            args.number,
            plot_segment_list_list,
            segment_records
        )
    elif args.mode == "plot":
        verify_plot(
            args.plots_dir,
            args.number,
            plot_segment_list_list,
            segment_records
        )
    elif args.mode == "segment":
        verify_segment(
            args.plots_dir,
            args.number,
            plot_segment_list_list,
            segment_records
        )
    elif args.mode == "all":
        verify_all_segments(
            args.plots_dir,
            plot_segment_list_list,
            segment_records
        )
    else:
        raise ValueError(f"Unknown mode {args.mode}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("--mode", type=str, default="first",
                        choices=["random", "first", "all", "plot", "segment"])
    parser.add_argument("-n", "--number", type=int, default=10)
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)

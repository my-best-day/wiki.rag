import json
import random
import logging
import argparse
import pandas as pd
from pathlib import Path

from xutils.byte_reader import ByteReader
from gen.new_segment_builder import SegmentBuilder
from gen.segment_overlap_setter import SegmentOverlapSetter

logger = logging.getLogger(__name__)


# for debugging
def dump_raw_segments(plots_dir, max_len, segments_per_plot):
    segments_per_plot = [
        [segment.decode('utf-8') for segment in plot_segment_list]
        for plot_segment_list in segments_per_plot
    ]
    segment_json_path = plots_dir / f"segments_{max_len}.json"
    with open(segment_json_path, 'w') as json_file:

        json.dump(segments_per_plot, json_file)


def describe_plot_segments(segments_per_plot, max_len):
    segment_per_plot = [len(segment_list) for segment_list in segments_per_plot]
    segment_per_plot_series = pd.Series(segment_per_plot)

    segment_lengths = [
        len(segment)
        for plot_segment_list in segments_per_plot
        for segment in plot_segment_list
    ]
    segment_lengths_series = pd.Series(segment_lengths)

    logger.info("base length: %s", max_len)
    logger.debug("segments per plot:\n%s", segment_per_plot_series.describe())
    logger.info("segment lengths:\n%s", segment_lengths_series.describe())


def verify_segments(plots_dir, segments_per_plot, segment_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)
    # keep: sample_records = segment_records[:10]

    sample_records = []
    for record in segment_records:
        # relative-index == 0 -> first segment of plot
        if record[2] == 0:
            sample_records.append(record)
            if len(sample_records) >= 20:
                break
    random_sample = random.sample(segment_records, 20)
    sample_records.extend(random_sample)

    for (segment_ind, plot_ind, rel_ind, offset, length) in sample_records:
        reader_bytes = byte_reader.read_bytes(offset, length)
        plot_segment_list = segments_per_plot[plot_ind]
        try:
            segment_bytes = plot_segment_list[rel_ind]
        except IndexError:
            logger.error("IndexError: segment %s of plot %s rel index %s",
                         segment_ind, plot_ind, rel_ind)
            raise
        is_match = segment_bytes == reader_bytes
        if is_match:
            logger.debug("+ segment %s of plot %s rel index %s match",
                         segment_ind, plot_ind, rel_ind)
        else:
            logger.info("""
- segment %s of plot %s rel index %s does not match

expected: %s

actual  : %s
            """, segment_ind, plot_ind, rel_ind, segment_bytes, reader_bytes)


def save_segment_records(records, max_len):
    segment_df = pd.DataFrame(
        records,
        columns=["segment_index", "plot_index", "rel_index", "offset", "length"]
    )
    segment_file_path = args.plots_dir / f"segments_{max_len}.csv"
    segment_df.to_csv(segment_file_path, index=False)
    logger.info("*** saved to %s", segment_file_path)


def get_plot_text_generator(plot_data_list, byte_reader):
    for plot_data in plot_data_list:
        text = byte_reader.read_bytes(plot_data.offset, plot_data.byte_length)
        yield text


def main(args):
    plots_file_path = args.plots_dir / "plots"
    plots_record_path = args.plots_dir / "plots_data.csv"

    byte_reader = ByteReader(plots_file_path)

    plots_df = pd.read_csv(plots_record_path, index_col=False)
    plot_data_list = list(plots_df.itertuples(index=False, name="PlotData"))
    plot_count = len(plot_data_list)

    max_len = args.max_len
    plot_text_generator = get_plot_text_generator(plot_data_list, byte_reader)
    segments_per_plot = SegmentBuilder.segmentize_text_list(
        max_len, plot_text_generator, plot_count)

    describe_plot_segments(segments_per_plot, max_len)

    segments_per_plot, segment_records = SegmentOverlapSetter.set_overlaps_for_plot_list(
        max_len,
        plot_data_list,
        segments_per_plot
    )

    describe_plot_segments(segments_per_plot, max_len)

    if args.dump_segments:
        dump_raw_segments(args.plots_dir, max_len, segments_per_plot)

    # remove segment_records = get_segment_records(segments_per_plot)
    verify_segments(args.plots_dir, segments_per_plot, segment_records)
    save_segment_records(segment_records, max_len)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("--dump-segments", default=False, action="store_true",
                        help="Dump segment bytes to a json file to be used by verify_segments.py")
    parser.add_argument("--debug", default=False, action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)

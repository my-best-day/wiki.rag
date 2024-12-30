import json
import random
import logging
import argparse
import pandas as pd
from typing import List
from pathlib import Path

from gen.plots.plot import PlotData, Plot

from xutils.byte_reader import ByteReader
from xutils.iterator_deque import IteratorDeque
from xutils.overlap_setter import OverlapSetter

logger = logging.getLogger(__name__)


class SegmentBuilder:
    def __init__(self, max_len: int) -> None:
        self.max_len = max_len
        self.base_length = int(0.8 * self.max_len)

    def segmentize_plots(self, plot_data_list: List[PlotData]) -> List[List[bytes]]:
        plot_segment_bytes_list_list = []
        base_length = int(0.8 * self.max_len)
        for plot_data in plot_data_list:
            plot_segments = self.segmentize_plot(base_length, plot_data)
            plot_segment_bytes_list_list.append(plot_segments)
            if len(plot_segment_bytes_list_list) % 5000 == 0:
                msg = f"processed {len(plot_segment_bytes_list_list)} / {len(plot_data_list)} plots"
                logger.info(msg)

        return plot_segment_bytes_list_list

    def segmentize_plot(
        self,
        base_length: int,
        plot_data: PlotData
    ) -> List[bytes]:

        segment_count = (plot_data.byte_length + base_length - 1) // base_length
        average_length = plot_data.byte_length // segment_count if segment_count else 0
        plot_bytes = plot_data.bytes
        delimiter = b'\n'
        sentences = plot_bytes.split(delimiter)
        sentences = [sentence + delimiter for sentence in sentences if sentence]
        sentence_iterator = IteratorDeque(iter(sentences))
        segment_byte_list = []
        segment_byte = b''
        rel_index = 0
        for sentence in sentence_iterator:
            if len(sentence) > base_length:
                # break into fragments and prepend to sentences
                try:
                    fragments = self.split_sentence(sentence, base_length)
                except ValueError:
                    logger.error(
                        "Could not split sentence of plot %s.%s: '%s'",
                        plot_data.uid, rel_index, sentence
                    )
                    raise
                sentence_iterator.extendleft(fragments)
                logger.info(f"... sentence too long at plot {plot_data.uid}, fragments: "
                            f"{len(fragments)}")

            elif self.is_there_enough_room_in_mean_length(average_length, segment_byte, sentence):
                segment_byte += sentence
            elif self.is_there_enough_room_in_base_length_and_segment_is_short(
                    base_length, segment_byte, sentence):
                segment_byte += sentence
            else:
                segment_byte_list.append(segment_byte)
                segment_byte = sentence
                rel_index += 1

        # add last segment
        if len(segment_byte) > 0:
            segment_byte_list.append(segment_byte)

        return segment_byte_list

    @staticmethod
    def is_sentence_too_long(base_length: int, sentence: str) -> bool:
        result = len(sentence) > base_length
        return result

    @staticmethod
    def is_there_enough_room_in_mean_length(
        avg_length: int,
        segment: str,
        sentence: str
    ) -> bool:
        """is there a room for the next sentence within the average length?"""
        result = len(segment) + len(sentence) <= avg_length
        return result

    @staticmethod
    def is_there_enough_room_in_base_length_and_segment_is_short(
        base_length: int,
        segment: str,
        sentence: str
    ) -> bool:
        """if segment is short, is there a room for the next sentence within the base length?"""
        is_short = len(segment) <= 0.6 * base_length
        is_room_in_base_length = len(segment) + len(sentence) <= base_length
        result = is_short and is_room_in_base_length
        return result

    @staticmethod
    def split_sentence(sentence, length):
        """
        split a sentence into fragments of a target length
        attempting to avoid splitted words between fragments.
        """
        logger.info("splitting sentence, length = %s", length)

        max_extend = 24
        frag_count = (len(sentence) + length - 1) // length
        target_length = (length // frag_count)
        safe_length = target_length - max_extend

        fragments = []
        if len(sentence) > length:
            for i in range(0, len(sentence), safe_length):
                fragments.append(sentence[i:i + safe_length])
        else:
            fragments.append(sentence)

        # find end of words at the end of a sentence and prepend to the next one
        for i in range(1, len(fragments)):
            j = 0
            fragment = fragments[i]
            length = len(fragment)
            max_steps = min(length, max_extend)
            while j < max_steps and not fragment[j:j + 1].isspace():
                j += 1
            if j < max_steps:
                j += 1
            fragments[i - 1] += fragment[:j]
            fragments[i] = fragment[j:]

            if j == max_steps:
                raise ValueError(
                    f"Could not find end of word for '{fragment}'"
                    f", length: {length}"
                    f", safe_length: {safe_length}"
                    f", target_length: {target_length}"
                    f", max_extend: {max_extend} "
                    f", max_steps: {max_steps} "
                    f", fragment index: {i} "
                )

        return fragments


def set_overlaps_for_plot_list(max_len: int, plot_segment_byte_list_list) -> List[List[bytes]]:
    segment_with_overlaps_list_list = []
    for plot_index, plot_segment_byte_list in enumerate(plot_segment_byte_list_list):
        plot_with_overlaps_list = set_overlaps_for_plot(max_len, plot_index, plot_segment_byte_list)
        segment_with_overlaps_list_list.append(plot_with_overlaps_list)
    return segment_with_overlaps_list_list


# ZZZZZZZZZZZZZZZZZ compute the offset here - offset of target - length of prev
def set_overlaps_for_plot(
    max_len: int,
    plot_index: int,
    plot_segment_byte_list
):
    plot_segment_with_overlaps_list = []

    segment_count = len(plot_segment_byte_list)
    prev_segment_bytes = None
    for i in range(segment_count):
        target_segment_bytes = plot_segment_byte_list[i]
        if i < segment_count - 1:
            next_segment_bytes = plot_segment_byte_list[i + 1]
        else:
            next_segment_bytes = None

        before_overlap, after_overlap = OverlapSetter.get_overlaps(
            max_len,
            target_segment_bytes,
            prev_segment_bytes,
            next_segment_bytes
        )
        if plot_index <= 500000:
            segment_with_overlaps = before_overlap + target_segment_bytes + after_overlap
        else:
            segment_with_overlaps = target_segment_bytes

        plot_segment_with_overlaps_list.append(segment_with_overlaps)

        prev_segment_bytes = target_segment_bytes

    return plot_segment_with_overlaps_list


# for debugging
def dump_plot_segment_list_list(plots_dir, max_len, plot_byte_segment_list_list):
    plot_segment_list_list = [
        [segment.decode('utf-8') for segment in plot_segment_list]
        for plot_segment_list in plot_byte_segment_list_list
    ]
    segment_json_path = plots_dir / f"segments_{max_len}.json"
    with open(segment_json_path, 'w') as json_file:
        json.dump(plot_segment_list_list, json_file)


def describe_plot_segments(plot_segment_list_list, max_len):
    segment_per_plot = [len(segment_list) for segment_list in plot_segment_list_list]
    segment_per_plot_series = pd.Series(segment_per_plot)

    segment_lengths = [
        len(segment)
        for plot_segment_list in plot_segment_list_list
        for segment in plot_segment_list
    ]
    segment_lengths_series = pd.Series(segment_lengths)

    print("base length:", max_len)
    print("segments per plot:\n", segment_per_plot_series.describe())
    print("segment lengths:\n", segment_lengths_series.describe())


def get_segment_records(plot_segment_list_list):
    # create a dataframe with columns:
    # segment index, plot index, segment offset, segment length
    offset = 0
    segment_records = []
    segment_index = 0
    for plot_index, plot_segment_list in enumerate(plot_segment_list_list):
        for rel_index, segment_bytes in enumerate(plot_segment_list):
            segment_length = len(segment_bytes)
            segment_data = (segment_index, plot_index, rel_index, offset, segment_length)
            segment_records.append(segment_data)
            offset += segment_length
            segment_index += 1
        offset += 6
    return segment_records


def verify_segments(plots_dir, plot_segment_list_list, segment_records):
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
        plot_segment_list = plot_segment_list_list[plot_ind]
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


def main(args):
    plots_file_path = args.plots_dir / "plots"
    plots_record_path = args.plots_dir / "plots_data.csv"

    byte_reader = ByteReader(plots_file_path)
    plots_df = pd.read_csv(plots_record_path, index_col=False)

    plot_list = []
    for record in plots_df.values:
        plot_data = PlotData(*record)
        plot = Plot(plot_data, byte_reader)
        plot_list.append(plot)

    max_len = args.max_len
    segment_builder = SegmentBuilder(max_len)
    plot_segment_list_list = segment_builder.segmentize_plots(plot_list)

    describe_plot_segments(plot_segment_list_list, max_len)

    plot_segment_list_list = set_overlaps_for_plot_list(
        max_len,
        plot_segment_list_list
    )

    describe_plot_segments(plot_segment_list_list, max_len)

    if args.dump_segments:
        dump_plot_segment_list_list(args.plots_dir, max_len, plot_segment_list_list)

    segment_records = get_segment_records(plot_segment_list_list)
    verify_segments(args.plots_dir, plot_segment_list_list, segment_records)
    save_segment_records(segment_records, max_len)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("--dump-segments", default=False, action="store_true",
                        help="Dump segment bytes to a json file to be used by verify_segments.py")
    args = parser.parse_args()

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)

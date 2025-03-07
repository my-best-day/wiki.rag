"""
Build segments for the plots dataset.
"""
import logging
import argparse
from pathlib import Path
from typing import List

from xutils.byte_reader import ByteReader
from gen.data.plot_store import PlotStore
from gen.segment_orchestrator import SegmentOrchestrator
from gen.data.segment_record_store import SegmentRecordStore


def get_plot_sentences_generator(plot_record_list, byte_reader):
    for plot_record in plot_record_list:
        text = byte_reader.read_bytes(plot_record.offset, plot_record.byte_length)
        sentences = split_plot_text(text)
        yield sentences


@staticmethod
def split_plot_text(text: bytes) -> List[bytes]:
    """
    Split text into sentences, ensuring "".join(sentences) == text.
    """
    delimiter = b'\n'
    sentences = text.split(delimiter)
    sentences = [sentence + delimiter for sentence in sentences if sentence]
    return sentences


def parse_args() -> argparse.Namespace:
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

    return args


def main():
    args = parse_args()

    text_file_path = args.plots_dir / "plots"
    text_byte_reader = ByteReader(text_file_path)

    plot_store = PlotStore(args.plots_dir)
    plot_record_list = plot_store.load_plot_record_list()

    max_len = args.max_len
    plot_sentences_generator = get_plot_sentences_generator(plot_record_list, text_byte_reader)
    document_offsets = [plot_record.offset for plot_record in plot_record_list]
    segment_record_store = SegmentRecordStore(args.plots_dir / "plots", max_len)
    segment_dump_path = args.plots_dir / f"segments_{max_len}.json" if args.dump_segments else None
    plot_count = len(plot_record_list)

    SegmentOrchestrator.build_segments(
        max_len,
        plot_sentences_generator,
        document_offsets,
        segment_record_store,
        text_byte_reader,
        segment_dump_path,
        plot_count
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()

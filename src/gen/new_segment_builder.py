import logging
from typing import List

from gen.plots.plot import PlotData

from xutils.iterator_deque import IteratorDeque
from xutils.sentence_utils import SentenceUtils

logger = logging.getLogger(__name__)


class SegmentBuilder:

    @staticmethod
    def segmentize_plots(
        max_length: int,
        plot_data_list: List[PlotData],
        plot_reader: callable,
    ) -> List[List[bytes]]:
        plot_segment_bytes_list_list = []
        base_length = int(0.8 * max_length)

        for plot_data in plot_data_list:
            plot_segments = SegmentBuilder.segmentize_plot(base_length, plot_data, plot_reader)
            plot_segment_bytes_list_list.append(plot_segments)

            if len(plot_segment_bytes_list_list) % 5000 == 0:
                msg = f"processed {len(plot_segment_bytes_list_list)} / {len(plot_data_list)} plots"
                logger.debug(msg)

        return plot_segment_bytes_list_list

    @staticmethod
    def segmentize_plot(
        base_length: int,
        plot_data: PlotData,
        plot_reader: callable,
    ) -> List[bytes]:

        balanced_length = SegmentBuilder.get_balanced_seg_length(plot_data.byte_length, base_length)
        plot_bytes = plot_reader(plot_data)
        sentences = SegmentBuilder.get_plot_sentences(plot_bytes)
        sentence_deque = IteratorDeque(iter(sentences))
        segments = []
        segment = b''

        for sentence in sentence_deque:
            if len(sentence) > base_length:
                SegmentBuilder.handle_sentence_split(sentence, base_length, sentence_deque)
            elif SegmentBuilder.can_add_sentence(base_length, balanced_length, segment, sentence):
                segment += sentence
            else:
                segments.append(segment)
                segment = sentence

        if segment:  # Add the last segment
            segments.append(segment)

        return segments

    @staticmethod
    def get_balanced_seg_length(byte_length: int, base_length: int) -> int:
        """Calculate the length of evenly divided segments."""
        segment_count = (byte_length + base_length - 1) // base_length
        balanced_length = byte_length // segment_count if segment_count else base_length
        return balanced_length

    @staticmethod
    def get_plot_sentences(plot_bytes: bytes) -> List[bytes]:
        """Split plot bytes into sentences."""
        delimiter = b'\n'
        sentences = plot_bytes.split(delimiter)
        sentences = [sentence + delimiter for sentence in sentences if sentence]
        return sentences

    @staticmethod
    def handle_sentence_split(
        sentence: bytes,
        base_length: int,
        sentence_deque: IteratorDeque
    ) -> None:
        """Split the sentence if it is too long."""
        assert len(sentence) > base_length
        fragments = SentenceUtils.split_sentence(sentence, base_length)
        sentence_deque.extendleft(fragments)
        return fragments[0]

    @staticmethod
    def is_sentence_too_long(base_length: int, sentence: str) -> bool:
        result = len(sentence) > base_length
        return result

    @staticmethod
    def can_add_sentence(
        base_length: int,
        balanced_length: int,
        segment: str,
        sentence: str
    ) -> bool:
        is_short = len(segment) <= 0.6 * base_length
        max_length = base_length if is_short else balanced_length
        result = len(segment) + len(sentence) <= max_length
        return result

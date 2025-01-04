import logging
from typing import List, Optional

from xutils.iterator_deque import IteratorDeque
from xutils.sentence_utils import SentenceUtils

logger = logging.getLogger(__name__)


class SegmentBuilder:

    @staticmethod
    def segmentize_text_list(
        max_length: int,
        text_generator: List[bytes],
        text_count: Optional[int] = None,
    ) -> List[List[bytes]]:
        segments_per_text = []
        base_length = int(0.8 * max_length)

        count_part = f" of {text_count}" if text_count else " of unknown"

        for text in text_generator:
            text_segments = SegmentBuilder.segmentize_text(base_length, text)
            segments_per_text.append(text_segments)

            if len(segments_per_text) % 5000 == 0:
                msg = f"processed {len(segments_per_text)}{count_part} texts"
                logger.debug(msg)

        return segments_per_text

    @staticmethod
    def segmentize_text(
        base_length: int,
        text: bytes,
    ) -> List[bytes]:

        text_length = len(text)
        balanced_length = SegmentBuilder.get_balanced_seg_length(text_length, base_length)
        sentences = SegmentBuilder.get_text_sentences(text)
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
    def get_text_sentences(text: bytes) -> List[bytes]:
        """Split text bytes into sentences."""
        delimiter = b'\n'
        sentences = text.split(delimiter)
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

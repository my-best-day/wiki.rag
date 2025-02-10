"""
This class responsible for the segmentization of documents.

Document's sentences are split into segments that match the max length, attempting to
balance the length of the segments, leaving room for overlaps.
Overlaps are not handled here.
"""
import math
import logging
from typing import List, Optional, Iterator

from xutils.iterator_deque import IteratorDeque
from xutils.sentence_utils import SentenceUtils

logger = logging.getLogger(__name__)


class SegmentBuilder:
    """
    This class responsible for the segmentization of documents.

    Document's sentences are split into segments that match the max length, attempting to
    balance the length of the segments, leaving room for overlaps.
    Overlaps are not handled here.
    """
    LOG_INTERVAL = 5000

    @staticmethod
    def segmentize_documents(
        max_length: int,
        sentences_per_document: Iterator[bytes],
        split_sentence: callable = None,
        document_count: Optional[int] = None,
    ) -> List[List[bytes]]:
        """
        Segments sentences from documents into chunks based on a maximum length.

        This method splits documents into segments that do not exceed the specified maximum length,
        aiming for balanced segment lengths while allowing for overlaps.

        Args:
            max_length (int): The maximum length of each segment.
            sentences_per_document (Iterator[bytes]): An iterator yielding lists of byte strings
                representing document sentences.
            split_sentence (callable, optional): Function to split long sentences. Defaults to a
                standard method if not provided.
            document_count (Optional[int]): The number of documents to process; None if unknown.

        Returns:
            List[List[bytes]]: A list of segments for each document.
        """
        segments_per_document = []
        base_length = int(0.8 * max_length)

        count_part = f" of {document_count}" if document_count else " of unknown"

        for sentences in sentences_per_document:
            text_segments = SegmentBuilder.segmentize_document(
                base_length,
                sentences,
                split_sentence
            )
            segments_per_document.append(text_segments)

            if len(segments_per_document) % SegmentBuilder.LOG_INTERVAL == 0:
                msg = f"processed {len(segments_per_document)}{count_part} texts"
                logger.debug(msg)

        return segments_per_document

    @staticmethod
    def segmentize_document(
        base_length: int,
        sentences: List[bytes],
        split_sentence: callable = None,
    ) -> List[bytes]:
        """
        Create segments for (sentences) of a single document.
        Gets the balanced length which based on the base length adjusted to the length of the text.
        Add sentences to a segment as long as they fit.
        If a sentence is too long, split it into fragments.
        """
        split_sentence = split_sentence or SegmentBuilder.split_sentence

        text_length = sum([len(sentence) for sentence in sentences])
        balanced_length = SegmentBuilder.get_balanced_seg_length(text_length, base_length)
        sentence_deque = IteratorDeque(iter(sentences))
        segments = []
        segment = b''

        for sentence in sentence_deque:
            if len(sentence) > base_length:
                fragments = split_sentence(sentence, base_length)
                sentence_deque.extendleft(fragments)
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
        balanced_length = math.ceil(byte_length / segment_count) if segment_count else base_length
        return balanced_length

    @staticmethod
    def split_sentence(
        sentence: bytes,
        base_length: int
    ) -> List[bytes]:
        """
        Split the sentence to (balanced) fragments fitting within base_length.
        Expecting "".join(fragments) == sentence
        """
        assert len(sentence) > base_length
        fragments = SentenceUtils.split_sentence(sentence, base_length)
        return fragments

    @staticmethod
    def is_sentence_too_long(base_length: int, sentence: str) -> bool:
        """Check if a sentence length is greater than base_length."""
        result = len(sentence) > base_length
        return result

    @staticmethod
    def can_add_sentence(
        base_length: int,
        balanced_length: int,
        segment: str,
        sentence: str
    ) -> bool:
        """Check if there is room in the segment for the sentence."""
        is_short = len(segment) <= 0.6 * base_length
        max_length = base_length if is_short else balanced_length
        result = len(segment) + len(sentence) <= max_length
        return result

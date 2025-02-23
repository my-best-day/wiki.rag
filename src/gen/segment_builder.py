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


class SegmentBuffer:
    def __init__(self, sentence: Optional[bytes] = None):
        self.sentences = []
        self.length = 0
        if sentence:
            self.append_sentence(sentence)

    def append_sentence(self, sentence: bytes):
        self.sentences.append(sentence)
        self.length += len(sentence)

    def prepend_sentence(self, sentence: bytes):
        self.sentences.insert(0, sentence)
        self.length += len(sentence)

    def __len__(self):
        return self.length

    def sentence_count(self) -> int:
        return len(self.sentences)

    def bytes(self) -> bytes:
        return b''.join(self.sentences)

    @classmethod
    def concat(cls, buffers: list['SegmentBuffer']) -> 'SegmentBuffer':
        new_buffer = cls()
        for buf in buffers:
            new_buffer.sentences.extend(buf.sentences)
            new_buffer.length += buf.length
        return new_buffer


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
    ) -> List[List[SegmentBuffer]]:
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
        segment_buffers_per_document: List[List[SegmentBuffer]] = []
        base_length = int(0.8 * max_length)

        count_part = f" of {document_count}" if document_count else " of unknown"

        for sentences in sentences_per_document:
            segment_buffers = SegmentBuilder.segmentize_document(
                base_length,
                sentences,
                split_sentence
            )
            segment_buffers_per_document.append(segment_buffers)

            if len(segment_buffers_per_document) % SegmentBuilder.LOG_INTERVAL == 0:
                msg = f"processed {len(segment_buffers_per_document)}{count_part} texts"
                logger.debug(msg)

        return segment_buffers_per_document

    @staticmethod
    def segmentize_document(
        base_length: int,
        sentences: List[bytes],
        split_sentence: callable = None,
    ) -> List[SegmentBuffer]:
        """
        Create segments for (sentences) of a single document.
        Gets the balanced length which based on the base length adjusted to the length of the text.
        Add sentences to a segment as long as they fit.
        If a sentence is too long, split it into fragments.

        Args:
            base_length (int): max length minus margin left for overlaps
            sentences (List[bytes]): sentences to segmentize
            split_sentence (callable, optional): The function to split long sentences. Defaults to a
                standard method if not provided.

        Returns:
            List[bytes]: segments
        """
        split_sentence = split_sentence or SegmentBuilder.split_sentence

        text_length = sum([len(sentence) for sentence in sentences])
        balanced_length = SegmentBuilder.get_balanced_seg_length(text_length, base_length)
        sentence_deque = IteratorDeque(iter(sentences))
        segment_buffer_list: List[SegmentBuffer] = []
        segment_buffer: SegmentBuffer = SegmentBuffer()

        for sentence in sentence_deque:
            if len(sentence) > base_length:
                fragments = split_sentence(sentence, base_length)
                sentence_deque.extendleft(fragments)
            elif SegmentBuilder.can_add_sentence(
                    base_length, balanced_length, segment_buffer, sentence):
                segment_buffer.append_sentence(sentence)
            else:
                segment_buffer_list.append(segment_buffer)
                segment_buffer = SegmentBuffer(sentence)

        if segment_buffer:  # Add the last segment
            segment_buffer_list.append(segment_buffer)

        return segment_buffer_list

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
        segment_buffer: SegmentBuffer,
        sentence: bytes
    ) -> bool:
        """Check if there is room in the segment for the sentence."""
        is_short = len(segment_buffer) <= 0.6 * base_length
        max_length = base_length if is_short else balanced_length
        result = len(segment_buffer) + len(sentence) <= max_length
        return result

import logging
from typing import List, Optional, Union
from gen.element.element import Element
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment
from xutils.iterator_deque import IteratorDeque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Document:
    uid: str
    title: str
    offset: int
    byte_length: int


@dataclass
class Section:
    uid: str
    plot_uid: str
    offset: int
    byte_length: int


class SegmentBuilder:
    """
    Build segments from a list of articles.
    A segment is a unit of text that can be processed by the sentence transformer and encoded
    as an embedding vector.
    A segment is a list of sections that fits within the max_len limit of the sentence transformer.
    We allocate no less than 10% and no more than 20% of the max_len for each of the overlaps.
    A segment does not cross the boundary of an article.

    """
    def __init__(self, max_len: int, documents: List[Document]) -> None:
        """
        Initialize the segment builder and initiate the build process.
        """
        self.max_len = max_len
        self.documents = documents

        # accumulated segments across all articles
        self.segments: List[ExtendedSegment] = []
        # segments for the current article
        self.document_segments: List[ExtendedSegment] = []
        # sections for the current article
        self.document_sections: Optional[IteratorDeque[Element]] = None
        # the current segment being built
        self.segment: ExtendedSegment = None

        # build the segments from the articles
        self._build()

    def _build(self) -> None:
        """
        Build segments from a list of articles.
        """
        for document in self.documents:
            self._segmentize_document(document)

    def _segmentize_document(self, document: Document) -> None:
        """
        Build segments from a single article.
        """
        self.document_segments.clear()
        self.segment = ExtendedSegment(Segment(document))

        max_len = self.max_len

        self.article_sections = IteratorDeque(article.elements)
        for section in self.article_sections:
            # if the first section is too long, split it
            if self._is_first_section():
                if self._split_section(section):
                    continue

            # if there is room for the section, add it to the segment
            if self.segment.segment.byte_length + section.byte_length <= 0.8 * max_len:
                # there is room for the section
                self.segment.append_element(section)
                continue

            # no room for the section, for now, we start a new segment
            # TODO: if the segment is (too) short, consider splitting the section
            self.close_segment_start_segment(article)
            # self.segment.append_element(section)
            self.article_sections.appendleft(section)

        self.close_last_segment()

        self.segments.extend(self.document_segments)

    def _is_first_section(self) -> bool:
        return self.segment.element_count == 0

    def _split_section(self, section: Section) -> bool:
        """
        If needed, split the section and add the parts to the segment queue.

        Args:
            section: The section to split.

        Returns:
            True if the section was split, False otherwise.
        """
        max_len = self.max_len

        result = True
        if section.byte_length <= 0.8 * max_len:
            result = False
        else:
            if section.byte_length > 1.6 * max_len:
                split_at = int(0.8 * max_len)
            elif section.byte_length > 0.8 * max_len:
                split_at = int(section.byte_length / 2)
            else:
                logger.warning("sec length: %d, max_len: %d",
                               section.byte_length, max_len)  # pragma: no cover
                assert False, "should never get here"         # pragma: no cover

            lead, remainder = section.split(split_at)
            self.article_sections.appendleft(remainder)
            self.article_sections.appendleft(lead)

            result = True

        return result

    def close_segment_start_segment(self, article: Article) -> None:
        """
        Close the current segment, set the overlaps or the previous segment, and start a new one.
        """
        # if the segment is empty, it does not count, ignore
        if self.segment.segment.byte_length == 0:
            return

        # add the segment to the list
        self.document_segments.append(self.segment)

        # overlaps - fix the previous segment
        self.set_overlaps_previous_segment()

        # start a new segment
        self.segment = ExtendedSegment(Segment(article))

    def close_last_segment(self) -> None:
        """
        Close the current and last segments, set the overlaps or the previous segment,
        and start a new one.
        """
        if self.segment.segment.byte_length > 0:
            self.document_segments.append(self.segment)
            self.set_overlaps_previous_segment()
            self.set_overlaps_last_segment()

    def set_overlaps_previous_segment(self) -> None:
        """
        Set the overlaps for the previous segment.
        """
        if len(self.document_segments) > 1:
            prev_segment = self.document_segments[-3] if len(self.document_segments) > 2 else None
            target_segment = self.document_segments[-2]
            next_segment = self.document_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, next_segment)

    def set_overlaps_last_segment(self) -> None:
        """
        Set the overlaps for the last segment.
        """
        if len(self.document_segments) > 1:
            prev_segment = self.document_segments[-2]
            target_segment = self.document_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, None)

    @staticmethod
    def set_overlaps(max_len: int,
                     prev_segment: Union[ExtendedSegment, None],
                     target_segment: ExtendedSegment,
                     next_segment: Union[ExtendedSegment, None]) -> None:
        """
        * we have three segments: previous, current, next
        * each segment is supposed to have at least 0.1 * max_len room for each overlap
        * overlap is limited to up to 0.2 * max-len
        * start by allocating equal overlap to before and after
        * if one of the ends doesn't uses the room allocated to it and the other end can use more,
        * add the unused room to the other end

        Dictionary:
        * allowed - maximum overlap allowed regardless of room / availability
        * room - available room divided equally between before and after
        * before_overlap, after_overlap - the lengths of the before and after overlaps
        * prev_seg_length, cur_seg_length, next_seg_length - the lengths of the before, current,
          and after segments
        * available_forward - room not used by before_overlap that can be added to after_overlap
        * available_backward - room not used by after_overlap that can be added to before_overlap

        Algorithm:
        1.  prev_seg_length = previous_segment.length if previous_segment else 0
        2.  next_seg_length = next_segment.length if next_segment else 0
        3.  allowed = 0.2 * max_len
        4.  initial_room = (max-len - cur_seg_length) / 2
        5.  before_overlap = min(allowed, initial_room, prev_seg_length)
        6.  after_overlap  = min(allowed, initial_room, next_seg_length)
        7.  available_forward = initial_room - before_overlap
        8.  if available_forward > 0:
                if after_overlap < allowed:
                    after_overlap = min(allowed, initial_room + available_forward, next_seg_length)
        9.  else:
                available_backward = initial_room - after_overlap
                if available_backward > 0:
                if before_overlap < allowed:
                before_overlap = min(allowed, initial_room + available_backward, prev_seg_length)
        """
        prev_seg_length = prev_segment.segment.byte_length if prev_segment else 0
        next_seg_length = next_segment.segment.byte_length if next_segment else 0
        allowed = int(0.2 * max_len)

        initial_room = max(0, int((max_len - target_segment.segment.byte_length) / 2))
        before_overlap = min(allowed, initial_room, prev_seg_length)
        after_overlap = min(allowed, initial_room, next_seg_length)

        available_forward = initial_room - before_overlap
        if available_forward > 0 and after_overlap < allowed:
            after_overlap = min(allowed, initial_room + available_forward, next_seg_length)
        else:
            available_backward = initial_room - after_overlap
            if available_backward > 0 and before_overlap < allowed:
                before_overlap = min(allowed, initial_room + available_backward, prev_seg_length)

        if before_overlap:
            # if prev_segment is None, we expect before_overlap to be 0
            assert prev_segment is not None
            _, before_overlap_fragment = prev_segment.segment.split(
                -before_overlap, after_char=True, include_first=False, include_remainder=True)
            target_segment.before_overlap = before_overlap_fragment

        if after_overlap:
            # if next_segment is None, we expect after_overlap to be 0
            assert next_segment is not None
            after_overlap_fragment, _ = next_segment.segment.split(
                after_overlap, after_char=False, include_first=True, include_remainder=False)
            target_segment.after_overlap = after_overlap_fragment

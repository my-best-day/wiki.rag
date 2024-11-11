import logging
from typing import List, Optional
from gen.element.element import Element
from gen.element.section import Section
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment
from xutils.iterator_deque import IteratorDeque

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SegmentBuilder:
    """
    Build segments from a list of articles.
    A segment is a unit of text that can be processed by the sentence transformer and encoded
    as an embedding vector.
    A segment is a list of sections that fits within the max_len limit of the sentence transformer.
    We allocate no less than 10% and no more than 20% of the max_len for each of the overlaps.
    A segment does not cross the boundary of an article.

    """
    def __init__(self, max_len: int, articles: List[Article]) -> None:
        """
        Initialize the segment builder and initiate the build process.
        """
        self.max_len = max_len
        self.articles = articles

        # accumulated segments across all articles
        self.segments: List[ExtendedSegment] = []
        # segments for the current article
        self.article_segments: List[ExtendedSegment] = []
        # sections for the current article
        self.article_sections: Optional[IteratorDeque[Element]] = None
        # the current segment being built
        self.segment: ExtendedSegment = ExtendedSegment(Segment())

        # build the segments from the articles
        self._build()

    def _reset_article(self) -> None:
        """
        Reset the article state for a new article.
        """
        self.article_segments.clear()
        self.article_sections = None
        self.segment = ExtendedSegment(Segment())

    def _build(self) -> None:
        """
        Build segments from a list of articles.
        """
        for article in self.articles:
            self._segmentize_article(article)
            # AI: do we want to reset_article after each article or before it?
            self._reset_article()

    def _segmentize_article(self, article: Article) -> None:
        """
        Build segments from a single article.
        """
        max_len = self.max_len

        self.article_sections = IteratorDeque(article.elements)
        for section in self.article_sections:
            logger.debug("--------------------------------")
            logger.debug("article_segments:")
            for seg in self.article_segments:
                logger.debug("    %s", seg.segment.bytes)
            logger.debug("segment status: %s", self.segment.segment.bytes)

            logger.debug("now looking at section: %s", section.bytes)

            # if the first section is too long, split it
            if self._is_first_section():
                logger.debug("first section, looking into splitting")
                if self._split_section(section):
                    logger.debug("first section, split")
                    continue
                else:
                    logger.debug("first section, not split")
            else:
                logger.debug("not first section")

            # if there is room for the section, add it to the segment
            if self.segment.segment.byte_length + section.byte_length <= 0.8 * max_len:
                logger.debug("there is room for the section")
                # there is room for the section
                self.segment.append_element(section)
                continue
            else:
                logger.debug("no room for the section")

            # no room for the section, for now, we start a new segment
            # TODO: if the segment is (too) short, consider splitting the section
            logger.debug("close/start segment")
            self.close_segment_start_segment()
            # self.segment.append_element(section)
            self.article_sections.appendleft(section)

        logger.debug("close last segment")
        self.close_last_segment()
        self.segments.extend(self.article_segments)

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
        if section.byte_length < 0.8 * max_len:
            logger.debug("section is short enough, not splitting")
            result = False
        else:
            if section.byte_length > 1.6 * max_len:
                split_at = int(0.8 * max_len)
                logger.debug("section is long, splitting at %d", split_at)
            elif section.byte_length > 0.8 * max_len:
                split_at = int(section.byte_length / 2)
                logger.debug("section is medium, splitting at %d", split_at)
            else:
                assert False, "should never get here"

            lead, remainder = section.split(split_at)
            logger.debug("split at %d into %s and %s", split_at, lead.bytes, remainder.bytes)
            self.article_sections.appendleft(remainder)
            self.article_sections.appendleft(lead)

            result = True

        return result

    def close_segment_start_segment(self) -> None:
        """
        Close the current segment, set the overlaps or the previous segment, and start a new one.
        """
        # if the segment is empty, it does not count, ignore
        if self.segment.segment.byte_length == 0:
            return

        # add the segment to the list
        self.article_segments.append(self.segment)

        # overlaps - fix the previous segment
        self.set_overlaps_previous_segment()

        # start a new segment
        self.segment = ExtendedSegment(Segment())

    def close_last_segment(self) -> None:
        """
        Close the current and last segments, set the overlaps or the previous segment,
        and start a new one.
        """
        if self.segment.segment.byte_length > 0:
            self.article_segments.append(self.segment)
            self.set_overlaps_previous_segment()
            self.set_overlaps_last_segment()

    def set_overlaps_previous_segment(self) -> None:
        """
        Set the overlaps for the previous segment.
        """
        if len(self.article_segments) > 1:
            logger.debug("setting overlaps for previous segment")
            prev_segment = self.article_segments[-3] if len(self.article_segments) > 2 else None
            target_segment = self.article_segments[-2]
            next_segment = self.article_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, next_segment)
        else:
            logger.debug("no previous segment to set overlaps for")

    def set_overlaps_last_segment(self) -> None:
        """
        Set the overlaps for the last segment.
        """
        if len(self.article_segments) > 1:
            prev_segment = self.article_segments[-2]
            target_segment = self.article_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, None)

    @staticmethod
    def set_overlaps(max_len: int, prev_segment: ExtendedSegment, target_segment: ExtendedSegment,
                     next_segment: ExtendedSegment) -> None:
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
        logger.debug("prev_seg_length: %d, next_seg_length: %d", prev_seg_length, next_seg_length)
        initial_room = max(0, int((max_len - target_segment.segment.byte_length) / 2))
        before_overlap = min(allowed, initial_room, prev_seg_length)
        after_overlap = min(allowed, initial_room, next_seg_length)
        logger.debug("initial_room: %d, before_overlap: %d, after_overlap: %d",
                     initial_room, before_overlap, after_overlap)

        available_forward = initial_room - before_overlap
        logger.debug("available_forward: %d", available_forward)
        if available_forward > 0 and after_overlap < allowed:
            after_overlap = min(allowed, initial_room + available_forward, next_seg_length)
        else:
            available_backward = initial_room - after_overlap
            logger.debug("available_backward: %d", available_backward)
            if available_backward > 0 and before_overlap < allowed:
                before_overlap = min(allowed, initial_room + available_backward, prev_seg_length)

        if before_overlap:
            # if prev_segment is None, we expect before_overlap to be 0
            assert prev_segment is not None
            logger.debug("before_overlap: %d", before_overlap)
            _, before_overlap_fragment = prev_segment.segment.split(
                -before_overlap, after_char=True, include_first=False, include_remainder=True)
            logger.debug("before_overlap_fragment: %s", before_overlap_fragment.bytes)
            target_segment.before_overlap = before_overlap_fragment
            logger.debug("target_segment: %s", target_segment.bytes)

        if after_overlap:
            # if next_segment is None, we expect after_overlap to be 0
            assert next_segment is not None
            logger.debug("after_overlap: %d", after_overlap)
            after_overlap_fragment, _ = next_segment.segment.split(
                after_overlap, after_char=False, include_first=True, include_remainder=False)
            logger.debug("after_overlap_fragment: %s", after_overlap_fragment.bytes)
            target_segment.after_overlap = after_overlap_fragment
            logger.debug("target_segment: %s", target_segment.bytes)

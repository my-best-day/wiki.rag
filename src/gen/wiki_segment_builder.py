import logging
from typing import List, Optional, Union
from gen.element.element import Element
from gen.element.section import Section
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.fragment import Fragment
from gen.element.extended_segment import ExtendedSegment
from xutils.iterator_deque import IteratorDeque
from xutils.overlap_setter import OverlapSetter

from gen.new_segment_builder import SegmentBuilder as NewSegmentBuilder

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

        def article_text_generator():
            for article in articles:
                yield article.bytes

        segment_builder = NewSegmentBuilder(max_len, article_text_generator, len(articles))

        # accumulated segments across all articles
        self.segments: List[ExtendedSegment] = []
        # segments for the current article
        self.article_segments: List[ExtendedSegment] = []
        # sections for the current article
        self.article_sections: Optional[IteratorDeque[Element]] = None
        # the current segment being built
        self.segment: ExtendedSegment = None

        # build the segments from the articles
        self._build()

    def _build(self) -> None:
        """
        Build segments from a list of articles.
        """
        for article in self.articles:
            self._segmentize_article(article)

        # # delete the last segment
        # last_extended_segment = self.segment
        # logger.warn("deleting segment %s", last_extended_segment.segment.uid)
        # del Element.instances[last_extended_segment.segment.uid]
        # del Element.instances[last_extended_segment.uid]

    def _segmentize_article(self, article: Article) -> None:
        """
        Build segments from a single article.
        """
        self.article_segments.clear()
        self.segment = ExtendedSegment(Segment(article))

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
        self.article_segments.append(self.segment)

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
            self.article_segments.append(self.segment)
            self.set_overlaps_previous_segment()
            self.set_overlaps_last_segment()

    def set_overlaps_previous_segment(self) -> None:
        """
        Set the overlaps for the previous segment.
        """
        if len(self.article_segments) > 1:
            prev_segment = self.article_segments[-3] if len(self.article_segments) > 2 else None
            target_segment = self.article_segments[-2]
            next_segment = self.article_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, next_segment)

    def set_overlaps_last_segment(self) -> None:
        """
        Set the overlaps for the last segment.
        """
        if len(self.article_segments) > 1:
            prev_segment = self.article_segments[-2]
            target_segment = self.article_segments[-1]
            self.set_overlaps(self.max_len, prev_segment, target_segment, None)

    @staticmethod
    def set_overlaps(
        max_len: int,
        prev_segment: Union[ExtendedSegment, None],
        target_segment: ExtendedSegment,
        next_segment: Union[ExtendedSegment, None]
    ) -> None:

        prev_segment_bytes = prev_segment.segment.bytes if prev_segment else None
        next_segment_bytes = next_segment.segment.bytes if next_segment else None

        before_overlap_text, after_overlap_text = OverlapSetter.get_overlaps(
            max_len,
            target_segment.bytes,
            prev_segment_bytes,
            next_segment_bytes
        )

        if before_overlap_text:
            before_offset = \
                prev_segment.offset + prev_segment.segment.byte_length - len(before_overlap_text)
            before_overlap = Fragment(prev_segment, before_offset, before_overlap_text)
            target_segment.before_overlap = before_overlap

        if after_overlap_text:
            after_offset = next_segment.offset
            after_overlap = Fragment(next_segment, after_offset, after_overlap_text)
            target_segment.after_overlap = after_overlap


#
# this class consumes a list of articles
# articles has sections
# it returns a list of extended segments
# extended segment has text and overlaps
# the output of the new implementation will be flat extended segments
# a flat extended segment is just a segment - it doesn't have information about the
# overlaps or the sections.
#
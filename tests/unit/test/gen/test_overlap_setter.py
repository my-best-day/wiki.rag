# cSpell:disable

import unittest
from gen.element.header import Header
from gen.element.article import Article
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.extended_segment import ExtendedSegment
from gen.segment_overlap_setter import SegmentOverlapSetter

marker = "no article"


# Tests here are identical to those in test_segment_builder_set_overlaps.py

class TestSegmentOverlapSetter(unittest.TestCase):
    def setUp(self):
        header = Header(0, b'')
        self.article = Article(header)

    def _create(self, byte_length: int, _bytes: bytes,
                article: Article = marker) -> ExtendedSegment:
        if article is marker:
            article = self.article
        return ExtendedSegment(Segment(article, Section(byte_length, _bytes)))

    def get_overlaps(self, max_len, before_element, target_element, after_element):
        return SegmentOverlapSetter.get_overlaps(
            max_len,
            target_element.bytes,
            before_element.bytes if before_element else None,
            after_element.bytes if after_element else None
        )

    def test_set_overlaps_enough_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'6789')
        self.assertEqual(after, b'ABCD')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'789')
        self.assertEqual(after, b'ABC')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(15, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'89')
        self.assertEqual(after, b'AB')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(14, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'89')
        self.assertEqual(after, b'AB')

    def test_set_overlaps_tight_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'9')
        self.assertEqual(after, b'A')

    def test_set_overlaps_before_is_short(self):
        prev_sec = self._create(0, b'01')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'01')
        self.assertEqual(after, b'ABCD')

    def test_set_overlaps_after_is_short(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'AB')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'6789')
        self.assertEqual(after, b'AB')

    def test_set_overlaps_before_is_short_bound_by_0_2(self):
        prev_sec = self._create(0, b'0')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'0')
        self.assertEqual(after, b'ABCD')

    def test_set_overlaps_after_is_short_bound_by_0_2(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'A')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'6789')
        self.assertEqual(after, b'A')

    def test_set_overlaps_before_is_shorter(self):
        prev_sec = self._create(0, b'01')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'1')
        self.assertEqual(after, b'A')

    def test_set_overlaps_after_is_shorter(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'AB')

        before, after = self.get_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'9')
        self.assertEqual(after, b'A')

    def test_set_overlaps_no_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(10, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

    def test_set_overlaps_first_segment(self):
        prev_sec = None
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'ABCD')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'ABC')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(15, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'ABC')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(14, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'AB')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'AB')

        curr_sec = self._create(10, b'abcdefghij')

        before, after = self.get_overlaps(10, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

    def test_set_overlaps_last_segment(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = None

        before, after = self.get_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'6789')
        self.assertEqual(after, b'')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'789')
        self.assertEqual(after, b'')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(15, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'789')
        self.assertEqual(after, b'')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(14, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'89')
        self.assertEqual(after, b'')

        curr_sec = self._create(10, b'abcdefghij')
        before, after = self.get_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'89')
        self.assertEqual(after, b'')

        curr_sec = self._create(10, b'abcdefghij')

        before, after = self.get_overlaps(10, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

    def test_too_long_for_overlap(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghijabcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

    def test_too_long_for_overlap_before(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghijabcdefghij')
        next_sec = None

        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

    def test_too_long_for_overlap_after(self):
        prev_sec = None
        curr_sec = self._create(10, b'abcdefghijabcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        before, after = self.get_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(before, b'')
        self.assertEqual(after, b'')

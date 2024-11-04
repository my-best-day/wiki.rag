# cSpell:disable

import unittest
from gen.segment_builder import SegmentBuilder
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.extended_segment import ExtendedSegment


class TestSegmentBuilder(unittest.TestCase):

    def _create(self, byte_length: int, _bytes: bytes) -> ExtendedSegment:
        return ExtendedSegment(Segment(Section(byte_length, _bytes)))

    def test_set_overlaps_enough_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'6789')
        self.assertEqual(curr_sec.after_overlap.bytes, b'ABCD')

        curr_sec = self._create(10, b'abcdefghij')
        SegmentBuilder.set_overlaps(18, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'789')
        self.assertEqual(curr_sec.after_overlap.bytes, b'ABC')

        curr_sec = self._create(10, b'abcdefghij')
        SegmentBuilder.set_overlaps(15, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'89')
        self.assertEqual(curr_sec.after_overlap.bytes, b'AB')

        curr_sec = self._create(10, b'abcdefghij')
        SegmentBuilder.set_overlaps(14, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'89')
        self.assertEqual(curr_sec.after_overlap.bytes, b'AB')

    def test_set_overlaps_tight_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'9')
        self.assertEqual(curr_sec.after_overlap.bytes, b'A')

    def test_set_overlaps_before_is_short(self):
        prev_sec = self._create(0, b'01')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'01')
        self.assertEqual(curr_sec.after_overlap.bytes, b'ABCD')

    def test_set_overlaps_after_is_short(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'AB')

        SegmentBuilder.set_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'6789')
        self.assertEqual(curr_sec.after_overlap.bytes, b'AB')

    def test_set_overlaps_before_is_short_bound_by_0_2(self):
        prev_sec = self._create(0, b'0')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'0')
        self.assertEqual(curr_sec.after_overlap.bytes, b'ABCD')

    def test_set_overlaps_after_is_short_bound_by_0_2(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'A')

        SegmentBuilder.set_overlaps(20, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'6789')
        self.assertEqual(curr_sec.after_overlap.bytes, b'A')

    def test_set_overlaps_before_is_shorter(self):
        prev_sec = self._create(0, b'01')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'1')
        self.assertEqual(curr_sec.after_overlap.bytes, b'A')

    def test_set_overlaps_after_is_shorter(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'AB')

        SegmentBuilder.set_overlaps(12, prev_sec, curr_sec, next_sec)
        self.assertEqual(curr_sec.before_overlap.bytes, b'9')
        self.assertEqual(curr_sec.after_overlap.bytes, b'A')

    def test_set_overlaps_no_room(self):
        prev_sec = self._create(0, b'0123456789')
        curr_sec = self._create(10, b'abcdefghij')
        next_sec = self._create(20, b'ABCDEFGHIJ')

        SegmentBuilder.set_overlaps(10, prev_sec, curr_sec, next_sec)
        self.assertIsNone(curr_sec.before_overlap)
        self.assertIsNone(curr_sec.after_overlap)

import unittest
from gen.element.element import Element
from gen.element.header import Header
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.article import Article
from gen.element.fragment import Fragment
from gen.element.extended_segment import ExtendedSegment
from gen.element.flat.flat_extended_segment import FlatExtendedSegment

from .common_container_tests import common_container_tests

from .byte_reader_tst import TestByteReader


class TestExtendedSegment(unittest.TestCase):
    def setUp(self):
        before_section = Section(offset=10, _bytes=b'ignore. end of previous segment. ')
        _, before_overlap = before_section.split(8)
        self.before_overlap = before_overlap
        self.section1 = Section(offset=42, _bytes=b'hello ')
        self.section2 = Section(offset=52, _bytes=b'world. ')
        after_section = Section(offset=59, _bytes=b'start of next segment. ignore.')
        after_overlap, _ = after_section.split(23)
        self.after_overlap = after_overlap

        header = Header(offset=0, _bytes=b'header')
        self.article = Article(header)

        self.ext_segment: ExtendedSegment = ExtendedSegment(Segment(self.article, self.section1))
        self.ext_segment.before_overlap = self.before_overlap
        self.ext_segment.append_element(self.section2)
        self.ext_segment.after_overlap = self.after_overlap

        self.elements = [self.before_overlap, self.section1, self.section2, self.after_overlap]

        self.ext_segment_no_before_overlap: ExtendedSegment = \
            ExtendedSegment(Segment(self.article, self.section1))
        self.ext_segment_no_before_overlap.append_element(self.section2)

    def test_common(self):
        for test_func in common_container_tests(self.ext_segment, self.elements):
            test_func()

    def test_article(self):
        self.assertEqual(self.ext_segment.article, self.article)

    def test_elements_with_overlaps(self):
        elements = list(self.ext_segment.elements)
        self.assertIsInstance(elements[0], Fragment)
        self.assertEqual(elements[0], self.before_overlap)
        self.assertIsInstance(elements[-1], Fragment)
        self.assertEqual(elements[-1], self.after_overlap)
        self.assertEqual(len(elements), 3)
        self.assertEqual(self.ext_segment.element_count, 3)

    def test_offset_with_before_overlap(self):
        self.assertEqual(self.ext_segment.offset, self.before_overlap.offset)

    def test_offset_without_before_overlap(self):
        self.assertEqual(self.ext_segment_no_before_overlap.offset, self.section1.offset)

    # synthetic test, not sure it is helpful
    def test_append_element(self):
        new_element = Section(offset=57, _bytes=b'new')
        self.ext_segment.append_element(new_element)
        self.assertEqual(new_element, list(self.ext_segment.segment.elements)[-1])
        self.assertEqual(self.ext_segment.bytes,
                         b'end of previous segment. hello world. newstart of next segment. ')

    def test_to_flat_extended_segment(self):
        byte_reader = TestByteReader.from_element(self.ext_segment)
        flat = self.ext_segment.to_flat_extended_segment()
        flat._byte_reader = byte_reader
        self.assertEqual(flat.uid, self.ext_segment.uid)
        self.assertEqual(flat.article_uid, self.article.uid)
        self.assertEqual(flat.offset, self.ext_segment.offset)
        self.assertEqual(flat.byte_length, self.ext_segment.byte_length)

        self.assertEqual(flat.text, self.ext_segment.text)
        self.assertEqual(flat.clean_text, self.ext_segment.clean_text)
        self.assertEqual(flat.byte_length, self.ext_segment.byte_length)
        self.assertEqual(flat.char_length, self.ext_segment.char_length)
        self.assertEqual(flat.clean_length, self.ext_segment.clean_length)

        xdata = flat.to_xdata()
        Element.instances.clear()
        flat2 = FlatExtendedSegment.from_xdata(xdata, byte_reader)
        self.assertEqual(flat2.uid, flat.uid)
        self.assertEqual(flat2.article_uid, flat.article_uid)
        self.assertEqual(flat2.offset, flat.offset)
        self.assertEqual(flat2.byte_length, flat.byte_length)

    # TODO: test with no after overlap


if __name__ == '__main__':
    unittest.main()

import unittest
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.extended_segment import ExtendedSegment
from .common_container_tests import common_container_tests


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

        self.ext_segment: ExtendedSegment = ExtendedSegment(Segment(self.section1))
        self.ext_segment.before_overlap = self.before_overlap
        self.ext_segment.append_element(self.section2)
        self.ext_segment.after_overlap = self.after_overlap

        self.elements = [self.before_overlap, self.section1, self.section2, self.after_overlap]

        self.ext_segment_no_before_overlap: ExtendedSegment = \
            ExtendedSegment(Segment(self.section1))
        self.ext_segment_no_before_overlap.append_element(self.section2)

    def test_common(self):
        for test_func in common_container_tests(self.ext_segment, self.elements):
            test_func()

    def test_elements_with_overlaps(self):
        elements = list(self.ext_segment.elements)
        self.assertEqual(elements[0], self.before_overlap)
        self.assertEqual(elements[-1], self.after_overlap)
        self.assertEqual(len(elements), 3)

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

    # TODO: test with no after overlap


if __name__ == '__main__':
    unittest.main()

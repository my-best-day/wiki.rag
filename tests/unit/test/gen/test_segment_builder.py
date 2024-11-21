# cSpell:disable

import unittest
from gen.segment_builder import SegmentBuilder
from gen.element.header import Header
from gen.element.segment import Segment
from gen.element.section import Section
from gen.element.article import Article
from gen.element.fragment import Fragment
from gen.element.paragraph import Paragraph
from gen.element.extended_segment import ExtendedSegment

# TODO: add test for section which is 0.8 of the max_len


class TestSegmentBuilder(unittest.TestCase):

    def _create(self, byte_length: int, _bytes: bytes) -> ExtendedSegment:
        return ExtendedSegment(Segment(Section(byte_length, _bytes)))

    def test_basic(self):
        """three short articles -> three segments"""

        article1 = Article(Header(0, b'Article 1'))
        Paragraph(article1.header.byte_length, b'Paragraph 1', article1)

        article2 = Article(Header(0, b'Article 2'))
        Paragraph(article2.header.byte_length, b'Paragraph 2', article2)

        article3 = Article(Header(0, b'Article 3'))
        Paragraph(article3.header.byte_length, b'Paragraph 3', article3)

        articles = [article1, article2, article3]

        builder = SegmentBuilder(max_len=30, articles=articles)

        self.assertEqual(len(builder.segments), 3)
        self.assertEqual(builder.segments[0].bytes, b'Article 1Paragraph 1')
        self.assertEqual(builder.segments[1].bytes, b'Article 2Paragraph 2')
        self.assertEqual(builder.segments[2].bytes, b'Article 3Paragraph 3')

    def test_long_first_section(self):
        """one long article -> two segments"""

        h = b'012345678901234567890123456789'
        p = b'abcdefghijklmnopqrstuvwxyzABCD'
        article = Article(Header(0, h))
        Paragraph(article.header.byte_length, p, article)

        max_len = int(len(h) / 1.8)  # 16 is 30 / 1.8
        builder = SegmentBuilder(max_len=max_len, articles=[article])

        # we start with the header '012345678901234567890123456789'
        # which we split into '012345678901' |12| and '234567890...9' |18|
        # first fragment becomes the first segment
        # there is no room for the next fragment, so we close the segment
        # second framgment becomes a first section and since it is long,
        # we split it into '234567890' |9| and '123456789' |9|
        # first section becomes a second segment
        # there is no room for the next section, so we close the segment
        # after that, we set overlaps for the first segment, take '234'
        # and 1st segment becomes '012345678901234'
        self.assertEqual(builder.segments[0].segment.bytes, b'012345678901')
        self.assertEqual(builder.segments[0].bytes, b'012345678901234')

        # now we have 1st segment '012345678901' + '234'
        # second segment is '234567890'
        # current segment section is '123456789'
        # current section is 'abc...BCD'
        # there is no room for it, we close the current segment
        # room is 3 -> before overlap is '901', after overlap is '123'
        self.assertEqual(builder.segments[1].segment.bytes, b'234567890')   # 9
        self.assertEqual(builder.segments[1].before_overlap.bytes, b'901')  # 3
        self.assertIsInstance(builder.segments[1].after_overlap, Fragment)
        self.assertEqual(builder.segments[1].before_overlap.offset,
                         builder.segments[0].segment.offset + 9)
        self.assertEqual(builder.segments[1].after_overlap.bytes, b'123')   # 3
        self.assertEqual(builder.segments[1].after_overlap.offset,
                         builder.segments[2].segment.offset)
        self.assertEqual(builder.segments[1].bytes, b'901234567890123')     # 15

        # now section is the first one. split it to 'abcd..jkl' and a reminder
        # it becomes the current segment. next we look at the reminder, there
        # is no room for it, we close the segment
        # previous segment '123456789' gets '890' and 'abc'
        self.assertEqual(builder.segments[2].segment.bytes, b'123456789')
        self.assertEqual(builder.segments[2].before_overlap.bytes, b'890')
        self.assertEqual(builder.segments[2].after_overlap.bytes, b'abc')
        self.assertEqual(builder.segments[2].bytes, b'890123456789abc')

        # current segment is 'abc...jkl'. next section is 'mno...BCD' it is the
        # first section and too long, we split it into
        # 'mno...stu' |9| and 'vwx...'BCD' |9|
        # 'mno...stu' becomes the current segment
        # there is no room for 'vwxyz...BCD', we close the segment
        # room now is 2 -> before overlap is 'kl' and after overlap is 'mn'
        self.assertEqual(builder.segments[3].segment.bytes, b'abcdefghijkl')  # 12
        self.assertEqual(builder.segments[3].before_overlap.bytes, b'89')     # 2
        self.assertEqual(builder.segments[3].after_overlap.bytes, b'mn')
        self.assertEqual(builder.segments[3].bytes, b'89abcdefghijklmn')

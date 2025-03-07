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
from xutils.sentence_utils import SentenceUtils
from gen.segment_orchestrator import SegmentOrchestrator

# TODO: add test for section which is 0.8 of the max_len

marker = "no article"


def get_article_sentences_generator(articles):
    for article in articles:
        text = article.bytes
        sentences = SentenceUtils.split_bytes_into_sentences(text)
        yield sentences


class TestSegmentBuilder(unittest.TestCase):

    def setUp(self):
        self.header = Header(0, b'')
        self.article = Article(self.header)
        return super().setUp()

    def _create(self, byte_length: int, _bytes: bytes,
                article: Article = marker) -> ExtendedSegment:
        if article is marker:
            article = self.article
        return ExtendedSegment(Segment(article, Section(byte_length, _bytes)))

    def test_basic(self):
        """three short articles -> three segments"""

        article1 = Article(Header(0, b'Article 1'))
        Paragraph(article1.header.byte_length, b'Paragraph 1', article1)

        article2 = Article(Header(0, b'Article 2'))
        Paragraph(article2.header.byte_length, b'Paragraph 2', article2)

        article3 = Article(Header(0, b'Article 3'))
        Paragraph(article3.header.byte_length, b'Paragraph 3', article3)

        articles = [article1, article2, article3]

        max_len = 30
        sentence_generator = get_article_sentences_generator(articles)
        document_offsets = [article.offset for article in articles]
        segment_file_path = f"{marker}_{max_len}_flat_segments.json"
        text_byte_reader = None
        segment_dump_path = None
        document_count = None

        builder = SegmentOrchestrator.build_segments(
            max_len,
            sentence_generator,
            document_offsets,
            segment_file_path,
            text_byte_reader,
            segment_dump_path,
            document_count
        )

        self.assertEqual(len(builder.segments), 3)
        self.assertEqual(builder.segments[0].bytes, b'Article 1Paragraph 1')
        self.assertEqual(builder.segments[1].bytes, b'Article 2Paragraph 2')
        self.assertEqual(builder.segments[2].bytes, b'Article 3Paragraph 3')

        # test empty segment is ignored
        segment = Segment(article1, Section(0, b''))
        extended_segment = ExtendedSegment(segment)
        builder.segment = extended_segment
        before_length = len(builder.segments)
        builder.close_segment_start_segment(article1)
        self.assertEqual(len(builder.segments), before_length)

        # test last empty segment is ignored
        segment = Segment(article1, Section(0, b''))
        extended_segment = ExtendedSegment(segment)
        builder.segment = extended_segment
        before_length = len(builder.segments)
        builder.close_last_segment()
        self.assertEqual(len(builder.segments), before_length)

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

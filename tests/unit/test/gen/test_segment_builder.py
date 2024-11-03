import unittest
from gen.element.header import Header
from gen.element.article import Article
from gen.element.paragraph import Paragraph
from gen.segment_builder import SegmentBuilder


class TestSegmentBuilder(unittest.TestCase):

    def setUp(self):
        # Set up test data for SegmentBuilder
        # self.max_len = 100
        # self.articles = [Article(paragraphs=[Section(byte_length=50), Section(byte_length=30)])]
        # self.segment_builder = SegmentBuilder(self.max_len, self.articles)
        pass

    def test_initialization_1(self):
        # Test if the SegmentBuilder initializes correctly
        header = Header(offset=0, _bytes=b'abcdefghijklmnopqrstuvwxyz')
        article = Article(header=header)
        articles = [article]
        max_len = 100
        segment_builder = SegmentBuilder(max_len=max_len, articles=articles)
        self.assertEqual(segment_builder.max_len, max_len)
        self.assertEqual(len(segment_builder.articles), len(articles))

    def test_initialization_2(self):
        header = Header(offset=0, _bytes=b'abcdefghijklmnopqrstuvwxyz')
        paragraph = Paragraph(offset=26, _bytes=b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        article = Article(header=header)
        article.append_paragraph(paragraph)

        articles = [article]
        max_len = 100

        segment_builder = SegmentBuilder(max_len=max_len, articles=articles)
        self.assertEqual(segment_builder.max_len, max_len)
        self.assertEqual(len(segment_builder.articles), len(articles))

    def test_initialization_3(self):
        header1 = Header(offset=0, _bytes=b'abcdefghijklmnopqrstuvwxyz')
        paragraph1 = Paragraph(offset=26, _bytes=b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        article1 = Article(header=header1)
        article1.append_paragraph(paragraph1)

        header2 = Header(offset=52, _bytes=b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        paragraph2 = Paragraph(offset=26, _bytes=b'abcdefghijklmnopqrstuvwxyz')
        article2 = Article(header=header2)
        article2.append_paragraph(paragraph2)

        articles = [article1, article2]
        max_len = 100
        segment_builder = SegmentBuilder(max_len=max_len, articles=articles)
        self.assertEqual(segment_builder.max_len, max_len)
        self.assertEqual(len(segment_builder.articles), len(articles))


    # def test_segment_creation(self):
    #     # Test if segments are created correctly
    #     self.segment_builder._build()
    #     self.assertGreater(len(self.segment_builder.segments), 0)

    # def test_close_segment(self):
    #     # Test the close_segment method
    #     self.segment_builder._build()
    #     initial_segment_count = len(self.segment_builder.segments)
    #     self.segment_builder.close_segment()
    #     self.assertEqual(len(self.segment_builder.segments), initial_segment_count)

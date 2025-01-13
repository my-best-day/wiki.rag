import unittest
from unittest.mock import Mock, patch, mock_open
from gen.element.header import Header
from gen.element.article import Article
from gen.index_builder_wiki import IndexBuilderWiki, Chunk


class TestIndexBuilderWiki(unittest.TestCase):
    def test_init(self):
        args = Mock()
        builder = IndexBuilderWiki(args)
        self.assertIs(builder.args, args)
        self.assertEqual(builder.articles, [])

    @patch('gen.index_builder_wiki.IndexBuilderWiki.process_chunk')
    @patch('gen.index_builder_wiki.IndexBuilderWiki.read_chunks')
    def test_build_index(self, mock_read_chunks, mock_process_chunk):
        # iterate over all chunks
        # remainder is passed from chunk to chunk
        # process chunk is called for each chunk

        chunk1 = Chunk(0, b'abcdefghij')
        chunk2 = Chunk(10, b'0123456789')
        chunk3 = Chunk(20, b'abcdefghij')
        mock_read_chunks.return_value = [chunk1, chunk2, chunk3]

        mock_process_chunk.side_effect = [b'hij', b'89', b'']

        builder = IndexBuilderWiki(Mock())
        builder.build_index()

        self.assertEqual(mock_process_chunk.call_count, 3)
        self.assertEqual(chunk2.offset, 7)
        self.assertEqual(chunk2.bytes, b'hij0123456789')
        self.assertEqual(chunk3.offset, 18)
        self.assertEqual(chunk3.bytes, b'89abcdefghij')

        mock_process_chunk.assert_any_call(chunk1)
        mock_process_chunk.assert_any_call(chunk2)
        mock_process_chunk.assert_any_call(chunk3)

    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_paragraph')
    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_header')
    def test_process_chunk(self, mock_handle_header, mock_handle_paragraph):
        # header, paragraph1, paragraph2 are processed, Para is returned as remainder
        # test offsets
        chunk = Chunk(0, b' = Header 1 =\nParagraph 1\nParagraph 2\nPara')
        # process chunk until the end of the chunk
        # return the remainder of the text that belongs to the next chunk

        builder = IndexBuilderWiki(Mock())
        out_remainder = builder.process_chunk(chunk)

        mock_handle_header.assert_called_once_with(0, b' = Header 1 =\n')
        mock_handle_paragraph.assert_any_call(14, b'Paragraph 1\n')
        mock_handle_paragraph.assert_any_call(26, b'Paragraph 2\n')
        self.assertEqual(out_remainder, b'Para')

    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_paragraph')
    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_header')
    def test_exhausted_bytes_in_chunk(self, mock_handle_header, mock_handle_paragraph):
        chunk = Chunk(0, b' = Header 1 =\n')
        builder = IndexBuilderWiki(Mock())
        out_remainder = builder.process_chunk(chunk)

        mock_handle_header.assert_called_once_with(0, b' = Header 1 =\n')
        mock_handle_paragraph.assert_not_called()
        self.assertEqual(out_remainder, b'')

    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_paragraph')
    @patch('gen.index_builder_wiki.IndexBuilderWiki.handle_header')
    def test_no_match(self, mock_handle_header, mock_handle_paragraph):
        chunk = Chunk(0, b'there is no complete paragraph here')
        builder = IndexBuilderWiki(Mock())
        out_remainder = builder.process_chunk(chunk)

        mock_handle_header.assert_not_called()
        mock_handle_paragraph.assert_not_called()
        self.assertEqual(out_remainder, chunk._bytes)

    def test_handle_header(self):
        # an article is created with the header
        # forward is called with the header
        builder = IndexBuilderWiki(Mock())
        builder.handle_header(12, b' = Header 1 =\n')
        self.assertEqual(len(builder.articles), 1)
        self.assertIsInstance(builder.articles[0], Article)
        self.assertEqual(builder.articles[0].header.offset, 12)
        self.assertIsInstance(builder.articles[0].header, Header)
        self.assertEqual(builder.articles[0].header.bytes, b' = Header 1 =\n')
        self.assertEqual(builder.articles[0].offset, 12)
        self.assertEqual(builder.articles[0].bytes, b' = Header 1 =\n')

    def test_handle_paragraph(self):
        # test that paragraph is created, associated with an article
        # for the article
        builder = IndexBuilderWiki(Mock())
        builder.articles.append(Article(Header(12, b' = Header 1 =\n')))
        builder.handle_paragraph(26, b'Paragraph X\n')
        article0 = builder.articles[0]
        self.assertEqual(article0.paragraph_count, 1)
        paragraph0 = list(article0.paragraphs)[0]
        self.assertEqual(paragraph0.offset, 26)
        self.assertEqual(paragraph0.bytes, b'Paragraph X\n')
        self.assertEqual(paragraph0.article, article0)

    @patch("builtins.open", new_callable=mock_open)
    def test_read_chunks(self, mock_open_func):
        # Last call returns EOF
        mock_open_func.return_value.read = Mock(side_effect=[b"chunk1", b"chunk2", b"chun", b""])
        mock_open_func.return_value.tell = Mock(side_effect=[0, 6, 12, 16])

        builder = IndexBuilderWiki(Mock())
        with patch.object(builder, 'CHUNK_SIZE_BYTES', 6):
            chunks = list(builder.read_chunks())
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].offset, 0)
        self.assertEqual(chunks[0].bytes, b"chunk1")
        self.assertEqual(chunks[1].offset, 6)
        self.assertEqual(chunks[1].bytes, b"chunk2")
        self.assertEqual(chunks[2].offset, 12)
        self.assertEqual(chunks[2].bytes, b"chun")

    @patch("builtins.open", new_callable=mock_open)
    def test_read_chunks_unicode(self, mock_open_func):
        # Last call returns EOF
        mock_open_func.return_value.read = \
            Mock(side_effect=[b"chunk\xE2", b"\x82\xACchk2", b"chun", b""])
        mock_open_func.return_value.tell = Mock(side_effect=[0, 6, 12, 16])

        builder = IndexBuilderWiki(Mock())
        with patch.object(builder, 'CHUNK_SIZE_BYTES', 6):
            chunks = list(builder.read_chunks())
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].offset, 0)
        self.assertEqual(chunks[0].bytes, b"chunk")
        self.assertEqual(chunks[1].offset, 5)
        self.assertEqual(chunks[1].bytes, b"\xE2\x82\xACchk2")
        self.assertEqual(chunks[2].offset, 12)
        self.assertEqual(chunks[2].bytes, b"chun")


if __name__ == '__main__':
    unittest.main()

"""
Build an index of articles and their paragraphs which includes the article/paragraph
offset in the file (in bytes, suitable for file_handle.seek()), and byte, text, and clean-text
lengths. Byte length is used to read the text from the file and clean-text length to calculate
segments for encoding / embedding

The implementation is more complicated than it should be because of some
experiments I did with the Chainable pattern and parallelization. This is
a learning exercise. The code could be much simpler.

Here we have
- IndexBuilder: builds the index (articles and paragraphs)
- IndexValidator: validates the offsets and byte lengths
- IndexDumper: dumps the index in a human readable format
"""
import re
import argparse
import logging
from typing import Generator, List

from gen.element.header import Header
from gen.element.section import Section
from gen.element.article import Article
from gen.element.paragraph import Paragraph
from xutils.encoding_utils import EncodingUtils

logger = logging.getLogger(__name__)


def is_non_negative_int(value: int) -> bool:
    return isinstance(value, int) and value >= 0


class Chunk:
    """
    A chunk is a block of bytes with an offset we read from the input text file.

    If the chunk cut off in the middle of a paragraph, we transfer the beginning
    of the paragraph to the next chunk.
    """
    def __init__(self, offset: int, _bytes: bytes) -> None:
        """
        Create a new chunk.
        """
        assert is_non_negative_int(offset), 'offset must be a positive integer'
        assert isinstance(_bytes, bytes), 'bytes must be bytes'

        self._offset: int = offset
        self._bytes: bytes = _bytes

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def bytes(self) -> bytes:
        return self._bytes

    def prepend_bytes(self, _bytes: bytes) -> None:
        assert isinstance(_bytes, bytes), 'bytes must be bytes'

        self._bytes = _bytes + self._bytes
        self._offset -= len(_bytes)

        assert self._offset >= 0, 'offset cannot be negative'


class IndexBuilder:
    CHUNK_SIZE_BYTES = 2 ** 15  # 32KB

    # looks for lines that looks like ' = Heading 1 = '
    ARTICLE_HEADER_PATTERN = br'^\s*=\s+[^=].*[^=]\s+=\s*\n'
    ARTICLE_HEADER_REGEX = re.compile(ARTICLE_HEADER_PATTERN)

    # looks for paragraphs that looks like 'Heading 1\nParagraph 1\nParagraph 2\n'
    PARAGRAPH_PATTERN = br'[\r\n]*[^\r\n]+[\r\n]+'
    PARAGRAPH_REGEX = re.compile(PARAGRAPH_PATTERN)

    def __init__(self, args):
        super().__init__()
        self.args: argparse.Namespace = args
        self.articles: List[Article] = []

    def build_index(self):
        """
        Build the index of articles and paragraphs.

        Read the text file in chunks and process each chunk to extract
        articles and paragraphs.

        Remainder - the text belongs to the next chunk is passed from chunk to the next.
        """
        remainder = b""
        for chunk in self.read_chunks():
            if remainder:
                chunk.prepend_bytes(remainder)
                remainder = b""
            remainder = self.process_chunk(chunk)

    def process_chunk(self, chunk: Chunk):
        """
        Process a chunk of text to extract articles and paragraphs.

        Capture headers and paragraphs until the end of the chunk.
        Return the remainder of the text that belongs to the next chunk.
        """
        remainder = b""
        offset = chunk.offset
        _bytes = chunk.bytes
        while _bytes:
            match = self.ARTICLE_HEADER_REGEX.match(_bytes)
            if match:
                matched = match.group(0)
                length = len(matched)
                self.handle_header(offset, matched)
            else:
                match = self.PARAGRAPH_REGEX.match(_bytes)
                if match:
                    matched = match.group(0)
                    length = len(matched)
                    self.handle_paragraph(offset, matched)
                else:
                    length = 0
                    remainder = _bytes
                    break
            assert length > 0, "length should never be zero ats this point"  # pragma: no cover
            _bytes = _bytes[length:]
            offset += length

        return remainder

    def handle_header(self, offset: int, matched_bytes: bytes) -> None:
        """
        Create a new Article.

        A new Header means a new Article.
        """
        header = Header(offset, matched_bytes)
        article = Article(header)
        self.articles.append(article)

    def handle_paragraph(self, offset, matched_bytes):
        """
        create a new paragraph.
        """
        Paragraph(offset, matched_bytes, self.articles[-1])

    def read_chunks(self) -> Generator[Section, None, None]:
        with open(self.args.text, "rb") as inp:
            # buffer holds the leading bytes of a multi-byte Unicode character that
            # was split between chunks and couldn't be decoded in the previous chunk
            buffer = b""
            while True:
                offset = inp.tell()
                chunk = inp.read(self.CHUNK_SIZE_BYTES)

                if not chunk:
                    break

                # prepend buffer (leading bytes of a multi-byte Unicode character from
                # previous chunk) to current chunk and adjust offset accordingly
                chunk = buffer + chunk
                offset -= len(buffer)

                # check if there is a split Unicode character in the end of chunk
                adjusted = EncodingUtils.adjust_split_point(chunk, len(chunk), after_char=False)
                if adjusted == len(chunk):
                    buffer = b''
                    text = chunk
                else:
                    text = chunk[:adjusted]
                    buffer = chunk[adjusted:]

                yield Chunk(offset, text)

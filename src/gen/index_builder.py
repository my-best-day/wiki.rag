"""
Build an index of articles and their paragraphs which includes the article/paragraph
offset in the file (in bytes, suitable for file_handle.seek()), and byte, text, and clean-text
lengths. Byte length is used to read the text from the file and clean-text length to calculate
segments for encoding / embedding

Here we have
- IndexBuilder: builds the index (articles and paragraphs)
- IndexValidator: validates the offsets and byte lengths
- IndexDumper: dumps the index in a human readable format
"""
import re
import argparse
import logging
from typing import Generator, List
from gen.element.chunk import Chunk
from gen.element.header import Header
from gen.element.article import Article
from gen.element.section import Section
from gen.element.paragraph import Paragraph
from plumbing.chainable import Chainable


logger = logging.getLogger(__name__)


class IndexBuilder(Chainable):
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

    def forward(self, element: Section):
        super().forward(element)

    def build(self):
        remainder = b""
        for chunk in self.read_chunks():
            if remainder:
                chunk.prepend_bytes(remainder)
                remainder = b""

            offset = chunk.offset
            text = chunk.bytes
            while text:
                match = self.ARTICLE_HEADER_REGEX.match(text)
                if match:
                    header = Header(offset, match.group(0))
                    article = Article(header)
                    self.articles.append(article)
                    length = header.byte_length
                    text = text[length:]
                    self.forward(header)

                else:
                    match = self.PARAGRAPH_REGEX.match(text)
                    if match:
                        paragraph = Paragraph(offset, match.group(0))
                        self.articles[-1].append_paragraph(paragraph)
                        length = paragraph.byte_length
                        text = text[length:]
                        self.forward(paragraph)

                    else:
                        remainder = text
                        text = b""
                offset += length

        self.forward(None)

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
                try:
                    chunk.decode('utf-8')
                    buffer = b""
                    text = chunk
                    # print(f"Unicode ok at {offset + len(chunk)}: {chunk[:20]}")
                except UnicodeDecodeError as e:
                    print(f"adjusting chunk at {offset + e.start} (offset: {offset})")
                    text = chunk[:e.start]
                    buffer = chunk[e.start:]

                yield Chunk(offset, text)

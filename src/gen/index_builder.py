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
import time
import logging
import argparse
from pathlib import Path
from typing import Generator, List
from gen.element.article import Article
from gen.element.section import Section
from gen.element.header import Header
from gen.element.paragraph import Paragraph
from gen.element.chunk import Chunk

logger = logging.getLogger(__name__)


class ByteReader:
    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")

    def read(self, offset: int, size: int) -> bytes:
        self.file.seek(offset)
        return self.file.read(size)


def format_text(bytes: bytes) -> str:
    text = bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text


class IndexBuilder:

    CHUNK_SIZE_BYTES = 2 ** 15  # 32KB

    # looks for lines that looks like ' = Heading 1 = '
    ARTICLE_HEADER_PATTERN = br'^\s*=\s+[^=].*[^=]\s+=\s*\n'
    ARTICLE_HEADER_REGEX = re.compile(ARTICLE_HEADER_PATTERN)

    # looks for paragraphs that looks like 'Heading 1\nParagraph 1\nParagraph 2\n'
    PARAGRAPH_PATTERN = br'[\r\n]*[^\r\n]+[\r\n]+'
    PARAGRAPH_REGEX = re.compile(PARAGRAPH_PATTERN)

    def __init__(self, args):
        self.args = args
        self.articles = []
        self.reader = ByteReader(args.text)

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
                else:
                    match = self.PARAGRAPH_REGEX.match(text)
                    if match:
                        paragraph = Paragraph(offset, match.group(0))
                        self.articles[-1].append_paragraph(paragraph)
                        length = paragraph.byte_length
                        text = text[length:]
                    else:
                        remainder = text
                        text = b""
                offset += length

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


class IndexValidator:

    def __init__(self, args):
        self.args = args
        self.reader = ByteReader(args.text)

    def validate(self, articles: List[Article]):
        for article in articles:
            for element in article.elements:
                snippet = self.reader.read(element.offset, len(element.bytes))
                if snippet != element.bytes:
                    caption = element.__class__.__name__

                    raise ValueError(f"snippet does not match section at offset {element.offset}:\n"
                                     f"{caption}: <<<{format_text(element.bytes)}>>>\n"
                                     f"Snippet: <<<{format_text(snippet)}>>>")


class IndexDumper:

    def __init__(self, args):
        self.args = args

    def dump(self, articles: List[Article]):
        print("Number of articles:", len(articles))
        for article in articles:
            print("." * 80)
            for element in article.elements:
                caption = element.__class__.__name__
                print(f"{caption}: <<<{format_text(element.bytes)}>>>")
            print("^" * 80)


def main(args):

    print("Building index...")
    builder = IndexBuilder(args)
    builder.build()

    print("Validating index...")
    validator = IndexValidator(args)
    validator.validate(builder.articles)

    print("Dumping index...")
    dumper = IndexDumper(args)
    dumper.dump(builder.articles)


if __name__ == '__main__':
    t0 = time.time()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.text is None:
        parser.error("Please provide the path to the text file")
    if args.text != "stdin":
        text = Path(args.text)
        if not text.exists():
            parser.error(f"File {args.text} not found")

    if args.path_prefix is None:
        parser.error("Please provide the path prefix")

    if args.max_len is None:
        parser.error("Please provide the maximum segment length")

    main(args)
    logger.debug(f"Elapsed time: {time.time() - t0:.2f} seconds")

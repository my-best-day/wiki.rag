import re
import time
import logging
import argparse
from pathlib import Path
from typing import Generator, List
from gen.element.article import Article
from gen.element.section import Section
from gen.element.segment import Segment
from gen.element.header import Header
from gen.element.paragraph import Paragraph
from gen.element.chunk import Chunk

logger = logging.getLogger(__name__)


class Segment(Section):
    def __init__(self, offset: int):
        super().__init__(offset, bytes)
        self.sections = []
        self._byte_len = 0

    @property
    def byte_length(self) -> int:
        return self._byte_len

    def append_sections(self, sections: List[Section], max_len: int, max_overlap: int) -> None:
        article_segments = []
        segment = Segment()
        article_segments.append(segment)

        while sections:
            section = sections.shift()

            if self.can_add_section_to_current_segment(segment, section, max_len):
                # simple case, just add section
                segment.append_section(section)
                continue

            if self.is_segment_empty(segment):
                # if first section is too long, split it
                first, remainder = section.split(max_len)
                segment.append(first)
                sections.unshift(remainder)
                continue

            # section is too long, add overlap to the end of the current segment
            overlap = min(max_overlap, max_len - segment.clean_length)
            segment.append_section(section[-overlap:])

            # create a new segment

            self.sections.append(section)
            self._byte_len += section.byte_len

    def can_add_section_to_current_segment(self, segment: Segment, section: Section, max_len: int):
        return segment.clean_length + section.clean_length <= max_len

    def is_segment_empty(self, segment: Segment):
        return segment.clean_length == 0


class ByteReader:
    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")

    def read(self, offset: int, size: int) -> bytes:
        self.file.seek(offset)
        return self.file.read(size)


# class Segmentizer:

#     def __init__(self, max_len: int, min_overlap: int, max_overlap: int):
#         self.max_len = max_len
#         self.min_overlap = min_overlap
#         self.max_overlap = max_overlap

#     def segmentize_article(self, article: Article):
#         self.segmentize_sections(article.sections)

#     def segmentize_sections(self, sections: List[Section]):
#         segments = []
#         segment_length = 0
#         for section in sections:
#             if segment_length + section.char_length <= self.max_len:
#                 segment_length += section.char_length
#                 segments.append(section)
#             else:
#                 break
#         return segments

#     def segmentize_article(self, article: Article):
#         segments = []
#     segment_length = 0
#     for section in article.sections:

#         if segment_length + section.char_len <= max_len:
#             segment_length += section.char_len
#             segments.append(section)
#         elif segment_length == 0:

#             break


class IndexBuilder:

    CHUNK_SIZE = 2 ** 15  # 32KB

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

    def dump(self):
        print("Number of articles:", len(self.articles))
        for article in self.articles:
            print("." * 80)
            for section in article.elements:
                self.say(section)
            print("<" * 80)

    # def build_segments(self):
    #     hard_max = self.args.max_len
    #     for article in self.articles:
    #         n = len(article.sections)
    #         for i, section in enumerate(article.sections):
    #             soft_factor = 0.9 if i == 0 or i == n - 1 else 0.8
    #             soft_max = hard_max * soft_factor

    #             if segment.byte_len + section.byte_len <= soft_max:
    #                 segment.append_section(section)
    #                 continue

    #             yield segment

    def say(self, section: Section):
        see = self.reader.read(section.offset, len(section.bytes))
        caption = section.__class__.__name__
        caption_length = len(caption)

        ok = see == section.bytes
        print(caption, ">>>", self.format_text(section.bytes), "<<<",
              "OK" if ok else "NOT OK")

        if not ok:
            see_caption = "SEE:"
            see_caption_length = len(see_caption)
            if see_caption_length < caption_length:
                see_caption = see_caption.ljust(caption_length)
            see_caption = see_caption[:caption_length]
            print(see_caption, ">>>", self.format_text(see), "<<<")
            raise ValueError("SEE does not match")

    @staticmethod
    def format_text(bytes: bytes) -> str:
        text = bytes.decode('utf-8')
        if len(text) > 200:
            m = 100
            return text[:m] + "...." + text[-m:]
        return text

    def read_chunks(self) -> Generator[Section, None, None]:
        with open(self.args.text, "rb") as inp:
            buffer = b""
            while True:
                offset = inp.tell()
                chunk = inp.read(self.CHUNK_SIZE)

                if not chunk:
                    break

                chunk = buffer + chunk

                try:
                    chunk.decode('utf-8')
                    buffer = b""
                    text = chunk
                except UnicodeDecodeError as e:
                    text = chunk[:e.start]
                    buffer = chunk[e.start:]

                yield Chunk(offset, text)


def main(args):

    builder = IndexBuilder(args)
    builder.build()
    builder.dump()


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

import re
import time
import logging
import argparse
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)


class Chunk:
    def __init__(self, offset: int, text: str):
        self.offset = offset
        self.text = text

    def __str__(self):
        return f"Chunk(offset={self.offset}, text={self.text})"


class IndexBuilder:

    CHUNK_SIZE = 2 ** 15  # 32KB

    # looks for lines that looks like ' = Heading 1 = '
    ARTICLE_HEADER_PATTERN = br'^\s*=\s+[^=].*[^=]\s+=\s*\n'
    ARTICLE_HEADER_REGEX = re.compile(ARTICLE_HEADER_PATTERN)

    # hold one: PARAGRAPH_PATTERN = br'^.+?\r?\n'
    PARAGRAPH_PATTERN = br'[\r\n]*[^\r\n]+[\r\n]*'
    PARAGRAPH_REGEX = re.compile(PARAGRAPH_PATTERN)

    def __init__(self, args):
        self.args = args
        self.collect = []

    def build(self):
        for chunk in self.read_chunks():
            start = 0
            text = chunk.text
            while text:
                match = self.ARTICLE_HEADER_REGEX.match(text)
                if match:
                    header = match.group(0)
                    self.collect.append([header])
                    start = len(header)
                    text = text[start:]
                else:
                    match = self.PARAGRAPH_REGEX.match(text)
                    if match:
                        paragraph = match.group(0)
                        self.collect[-1].append(paragraph)
                        start = len(paragraph)
                        text = text[start:]
                        # print("PARAGRAPH: <<<", paragraph.decode('utf-8')[:200], ".....",
                        #       paragraph.decode('utf-8')[-200:], ">>>")
                    else:
                        raise ValueError(f"No match found for {text}")

    def dump(self):
        print("Number of articles:", len(self.collect))
        for article in self.collect:
            header = article[0]
            print("." * 80)
            print("*** HEADER: <<<", header.decode('utf-8'), ">>>")
            for paragraph in article[1:]:
                if len(paragraph) < 200:
                    print("*** PARAGRAPH: sss", paragraph.decode('utf-8'), ">>>")
                else:
                    m = 100
                    print("*** PARAGRAPH: <<<", paragraph.decode('utf-8')[:m], "....",
                          paragraph.decode('utf-8')[-m:], ">>>")
            print("<" * 80)

    def read_chunks(self) -> Generator[Chunk, None, None]:
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

"""
Build segments for the wiki text 103 flat article data set.
"""
import logging
import argparse
from typing import List
from pathlib import Path

from xutils.byte_reader import ByteReader
from gen.element.flat.flat_article import FlatArticle
from gen.data.segment_record_store import SegmentRecordStore
from gen.element.flat.flat_article_store import FlatArticleStore
from xutils.sentence_utils import SentenceUtils
from gen.segment_orchestrator import SegmentOrchestrator


def read_flat_articles(text_file_path: Path, path_prefix: str) -> List[FlatArticle]:
    text_byte_reader = ByteReader(text_file_path)
    flat_article_store = FlatArticleStore(path_prefix, text_byte_reader)
    flat_articles = flat_article_store.load_flat_articles()
    return flat_articles


def get_article_sentences_generator(articles):
    for article in articles:
        text = article.bytes
        sentences = SentenceUtils.split_bytes_into_sentences(text)
        yield sentences


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("--dump-segments", default=False, action="store_true",
                        help="Dump segment bytes to a json file to be used by verify_segments.py")
    parser.add_argument("-d", "--debug", default=False, action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.text is None:
        parser.error("Please provide the path to the text file")
    text = Path(args.text)
    if not text.exists():
        parser.error(f"File {args.text} not found")

    if args.path_prefix is None:
        parser.error("Please provide the path prefix")

    if args.max_len is None:
        parser.error("Please provide the maximum segment length")

    return args


def main():
    args = parse_args()

    text_file_path = args.text
    path_prefix = args.path_prefix
    articles = read_flat_articles(text_file_path, path_prefix)
    sentences_generator = get_article_sentences_generator(articles)

    max_len = args.max_len
    text_byte_reader = ByteReader(text_file_path)
    document_offsets = [document.offset for document in articles]
    segment_record_store = SegmentRecordStore(args.path_prefix, max_len)
    if args.dump_segments:
        segment_dump_path = f"{args.path_prefix}_{max_len}_segments_dump.json"
    else:
        segment_dump_path = None
    document_count = len(articles)

    SegmentOrchestrator.build_segments(
        max_len,
        sentences_generator,
        document_offsets,
        segment_record_store,
        text_byte_reader,
        segment_dump_path,
        document_count
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()

# text -> plots -> sentences -> fragments
# at a later date consider having sub-documents that are non-split-able
# text -> articles -> sections -> paragraphs -> sentences -> fragments

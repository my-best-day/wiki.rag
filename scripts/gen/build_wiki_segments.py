"""
Build segments for the wiki text 103 flat article data set.
"""
import logging
import argparse
from typing import List
from pathlib import Path

from gen.element.store import Store
from gen.element.element import Element
from gen.element.flat.flat_article import FlatArticle


from xutils.sentence_utils import SentenceUtils
from gen.segment_orchestrator import SegmentOrchestrator


def load_flat_articles(
    text_path: Path,
    path_prefix: str
) -> List[FlatArticle]:
    flat_article_store_path = Path(f"{path_prefix}_flat_articles.json")
    store = Store()
    store.load_elements(Path(text_path), flat_article_store_path)

    flat_articles = [element for element in Element.instances.values()
                     if isinstance(element, FlatArticle)]
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
    articles = load_flat_articles(text_file_path, path_prefix)
    sentences_generator = get_article_sentences_generator(articles)

    max_len = args.max_len
    document_offsets = [document.offset for document in articles]
    segment_file_path = f"{args.path_prefix}_{max_len}_flat_segments.json"
    if args.dump_segments:
        segment_dump_path = f"{args.path_prefix}_{max_len}_flat_segments_dump.json"
    else:
        segment_dump_path = None
    document_count = len(articles)

    SegmentOrchestrator.build_segments(
        max_len,
        sentences_generator,
        document_offsets,
        segment_file_path,
        text_file_path,
        segment_dump_path,
        document_count
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()

# text -> plots -> sentences -> fragments
# at a later date consider having sub-documents that are non-split-able
# text -> articles -> sections -> paragraphs -> sentences -> fragments

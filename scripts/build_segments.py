import time
import logging
import argparse
from pathlib import Path
from typing import List
from gen.element.flat.flat_extended_segment import FlatExtendedSegment
from gen.element.store import Store
from gen.element.element import Element
from gen.element.article import Article
from gen.segment_builder import SegmentBuilder


logger = logging.getLogger(__name__)


def load_articles(text_path: str, path_prefix: str):
    store = Store()
    element_store_path = Path(f"{path_prefix}_elements.json")
    store.load_elements(Path(text_path), element_store_path)
    articles = [element for element in Element.instances.values() if isinstance(element, Article)]
    return articles


def main(args):
    articles = load_articles(args.text, args.path_prefix)
    print("found articles:", len(articles))

    max_len = args.max_len
    segment_builder = SegmentBuilder(max_len, articles)
    print(f"Built {len(segment_builder.segments)} segments")
    # segments created segments = segment_builder.segments

    segment_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")
    store = Store()
    store.store_elements(segment_path, Element.instances.values())

    flat_extended_segments: List[FlatExtendedSegment] = \
        [ext_seg.to_flat_extended_segment() for ext_seg in segment_builder.segments]
    flat_segment_path = Path(f"{args.path_prefix}_{args.max_len}_flat_segments.json")
    store.store_elements(flat_segment_path, flat_extended_segments)

    flat_article_list: List[Article] = \
        [article.to_flat_article() for article in Element.instances.values()
         if isinstance(article, Article)]
    flat_article_path = Path(f"{args.path_prefix}_flat_articles.json")
    store.store_elements(flat_article_path, flat_article_list)


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
    logger.info(f"Elapsed time: {time.time() - t0:.2f} seconds")

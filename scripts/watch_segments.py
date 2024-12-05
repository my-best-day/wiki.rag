import time
import logging
import argparse
from pathlib import Path
from gen.element.store import Store
from gen.element.article import Article
from gen.element.element import Element
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment
from gen.element.flat.flat_article import FlatArticle
from gen.element.flat.flat_extended_segment import FlatExtendedSegment

__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.fragment")
__import__("gen.element.list_container")


logger = logging.getLogger(__name__)


def main(args):
    if args.show_flat:
        watch_flat_extended_segments(args)
    else:
        watch_extended_segments(args)


def watch_extended_segments(args):
    load_elements(args)
    segments = [element for element in Element.instances.values()
                if isinstance(element, Segment)]

    extended_segments = [element for element in Element.instances.values()
                         if isinstance(element, ExtendedSegment)]

    print(f"FOUND {len(segments)} segments")
    print(f"FOUND {len(extended_segments)} extended segments")

    if args.to_flat:
        store = Store()
        flat_segment_path = Path(f"{args.path_prefix}_{args.max_len}_flat_segments.json")
        flat_extended_segments = \
            [ext_seg.to_flat_extended_segment() for ext_seg in extended_segments]
        store.store_elements(flat_segment_path, flat_extended_segments)

        articles = [element for element in Element.instances.values()
                    if isinstance(element, Article)]
        flat_articles = [article.to_flat_article() for article in articles]
        store.store_elements(Path(f"{args.path_prefix}_flat_articles.json"), flat_articles)

    show_samples(args, extended_segments)


def watch_flat_extended_segments(args):
    store = Store(single_store=False)
    load_flat_extended_segments(args, store)
    load_flat_articles(args, store)
    flat_extended_segments = [element for element in Element.instances.values()
                              if isinstance(element, FlatExtendedSegment)]
    flat_article_map = {element.uid: element for element in Element.instances.values()
                        if isinstance(element, FlatArticle)}
    print(f"FOUND {len(flat_extended_segments)} flat extended segments")

    if args.verbose:
        n = args.number
        m = n // 2
        if n < 0 or len(flat_extended_segments) <= n:
            show = flat_extended_segments
        else:
            show = flat_extended_segments[:m] + flat_extended_segments[-m:]

        last_article_uid = None
        for i, xseg in enumerate(show):
            if xseg.article_uid != last_article_uid:
                article = flat_article_map[xseg.article_uid]
                print(f"ARTICLE: {article.header.text.strip()} ({article.uid})")
                last_article_uid = xseg.article_uid
            sample = get_sample(xseg, 120)
            print(f"{i:2d}, {xseg.offset:8d}, {xseg.byte_length:4d}, {sample} ({xseg.uid})")


def show_samples(args, extended_segments):
    last_article_uid = None
    if args.verbose:
        n = args.number
        m = n // 2
        if n < 0 or len(extended_segments) <= n:
            show = extended_segments
        else:
            show = extended_segments[:m] + extended_segments[-m:]

        for i, xseg in enumerate(show):
            article = xseg.article
            if article.uid != last_article_uid:
                print(f"ARTICLE: {article.header.text.strip()} ({article.uid})")
                last_article_uid = article.uid

            sample = (
                f">{get_sample(xseg.before_overlap, 30).rjust(33)}<--"
                f"{get_sample(xseg.segment, 60).ljust(63)}--> "
                f"{get_sample(xseg.after_overlap, 30).ljust(33)}<"
            )
            print(f"{i:2d}, {xseg.offset:8d}, {xseg.byte_length:4d}, {sample}"
                  f" ({xseg.uid})")


def get_sample(element, room):
    if element is None:
        result = "NONE"
    else:
        text = element.text.replace("\n", "\\n")
        if len(text) <= room:
            result = text
        else:
            rom = room // 2
            result = f"{text[:rom]}...{text[-rom:]}"
    return result


def load_elements(args):
    store = Store()
    text_path = Path(args.text)
    segment_store_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")
    store.load_elements(Path(text_path), segment_store_path)


def load_flat_extended_segments(args: argparse.Namespace, store: Store):
    text_path = Path(args.text)
    flat_segment_store_path = Path(f"{args.path_prefix}_{args.max_len}_flat_segments.json")
    store.load_elements(Path(text_path), flat_segment_store_path)


def load_flat_articles(args: argparse.Namespace, store: Store):
    text_path = Path(args.text)
    flat_article_store_path = Path(f"{args.path_prefix}_flat_articles.json")
    store.load_elements(Path(text_path), flat_article_store_path)


if __name__ == '__main__':
    t0 = time.time()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("--show-flat", default=False, action="store_true",
                        help="Watch flat extended segments instead of extended segments")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="Verbose mode")
    parser.add_argument("-n", "--number", type=int, default=10, help="Number of samples to show")
    parser.add_argument("--to-flat", default=False, action="store_true",
                        help="Convert to flat segments")
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

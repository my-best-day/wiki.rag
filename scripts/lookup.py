import sys
import time
import logging
import argparse
from uuid import UUID
from pathlib import Path
from typing import List, Tuple
from gen.element.element import Element
from gen.search.stores_flat import StoresFlat as Stores
from gen.search.k_nearest_finder import KNearestFinder


class LookupCLI:
    def __init__(self, args):
        self.args = args
        self.stores = Stores(args.text, args.path_prefix, args.max_len)
        self.k_nearest_finder = KNearestFinder(self.stores)
        self.stores.background_load()
        self._extended_segment_map = None
        self._article_map = None

    def run(self):
        self.run_articles()

    def run_segments(self):
        while True:
            prompt = "Enter a query sentence (or 'exit' to quit): "
            print(prompt, " Press Cmd-D when done: ")
            query = sys.stdin.read().strip()
            print(".... ... .. .")
            if query.lower() in ("exit", "quit"):
                break

            t0 = time.time()
            nearest_segments: List[Tuple[UUID, float]] = \
                self.k_nearest_finder.find_k_nearest_segments(query, self.args.k)
            elapsed = time.time() - t0

            self.display_nearest_segments(query, nearest_segments, elapsed)

    def run_articles(self):
        while True:
            prompt = "Enter a query sentence (or 'exit' to quit): "
            print(prompt, " Press Cmd-D when done: ")
            query = sys.stdin.read().strip()
            print(".... ... .. .")
            if query.lower() in ("exit", "quit"):
                break

            t0 = time.time()
            top_k_article_similarities: List[Tuple[UUID, float]] = \
                self.k_nearest_finder.find_k_nearest_articles(query, self.args.k, 0.36, 10)
            elapsed = time.time() - t0

            self.display_nearest_articles(query, top_k_article_similarities, elapsed)

    def display_nearest_segments(self, query, nearest_segments, elapsed):

        print("\n\n\n\n")
        print("Nearest Segments ", ">>>> " * 10)
        print("Nearest Segments ", ">>>> " * 10)
        print("QUERY:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s" + "---- " * 10)
        for i, (uid, score) in enumerate(nearest_segments):
            segment = self.get_extended_segment(uid)

            text = segment.before_overlap.text if segment.before_overlap else ""
            text += "][" + segment.segment.text + "]["
            text += segment.after_overlap.text if segment.after_overlap else ""

            print(f"{i + 1}. Segment ID: {uid}, Score: {score:.4f}, "
                  f"(off: {segment.offset}, len: {len(segment.text)})")
            print(f"Article: {segment.article.header.text.strip()}")
            print(text)
            print("<--- " * 10, "\n")

    def display_nearest_articles(self, query, top_k_article_similarities, elapsed):
        print("\n\n\n\n")
        print("Nearest Articles ", ">>>> " * 10)
        print("Nearest Articles ", ">>>> " * 10)
        print("QUERY:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s" + "---- " * 10)
        for i, (uid, score) in enumerate(top_k_article_similarities):
            article = self.get_article(uid)
            print(f"{i + 1}. Article ID: {uid}, Score: {score:.4f}, "
                  f"(off: {article.offset}, len: {len(article.text)})")
            print(article.text)
            print("<--- " * 10, "\n")

    @property
    def extended_segment_map(self):
        if self._extended_segment_map is None:
            extended_segments = self.stores.extended_segments
            self._extended_segment_map = {ext_seg.uid: ext_seg for ext_seg in extended_segments}
        return self._extended_segment_map

    def get_extended_segment(self, uid):
        return self.extended_segment_map[uid]

    def get_article(self, uid):
        return Element.instances[uid]


def main(args):
    lookup_cli = LookupCLI(args)
    lookup_cli.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of the element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("-k", "--k", type=int, default=5, help="Number of nearest neighbors")
    args = parser.parse_args()

    if args.text is None:
        parser.error("Please provide the path to the text file")
    args.text = Path(args.text)
    if not args.text.exists():
        parser.error(f"File {args.text} not found")

    if args.path_prefix is None:
        parser.error("Please provide the path prefix")

    if args.max_len is None:
        parser.error("Please provide the maximum segment length")

    main(args)

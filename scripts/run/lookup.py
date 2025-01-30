#!/usr/bin/env python

import sys
import time
import logging
import argparse
import os

from search.stores import Stores
from xutils.app_config import AppConfig, load_app_config
from gen.element.element import Element
from search.k_nearest_finder import KNearestFinder
from search.services.combined_service import CombinedService, CombinedRequest, Kind
from search.services.combined_service import CombinedResponse


class LookupCLI:
    def __init__(
        self,
        logger: logging.Logger,
        app_config: AppConfig,
        k_nearest: int,
        threshold: float,
        max_documents: int,
    ) -> None:
        self.app_config = app_config
        self.k_nearest = k_nearest
        self.threshold = threshold
        self.max_documents = max_documents

        text_file_path = app_config.text_file_path
        embedding_config = app_config.embed_config

        stores = Stores.create_stores(text_file_path, embedding_config)
        stores.background_load()

        finder = KNearestFinder(stores, embedding_config)

        self.service = CombinedService(stores, embedding_config, finder)

        self._extended_segment_map = None
        self._article_map = None

    def run(self):
        # self.run_articles()
        self.run_segments()

    def run_segments(self):
        while True:
            query = self.get_query()
            if query.lower() in ("exit", "quit"):
                break

            t0 = time.time()
            response = self.get_response(query)
            elapsed = time.time() - t0

            results = response.results
            self.display_nearest_segments(query, results, elapsed)

    def get_query(self) -> str:
        prompt = "Enter a query sentence (or 'exit' to quit): "
        print(prompt, " Press Cmd-D when done: ")
        query = sys.stdin.read().strip()
        print(".... ... .. .")
        return query

    def get_response(self, query) -> CombinedResponse:
        k_nearest = self.k_nearest
        threshold = self.threshold
        max_documents = self.max_documents

        combined_request = CombinedRequest(
            action="search",
            kind=Kind.Segment,
            query=query,
            k=k_nearest,
            threshold=threshold,
            max=max_documents
        )
        combined_response = self.service.combined(combined_request)
        return combined_response

    def run_articles(self):
        while True:
            prompt = "Enter a query sentence (or 'exit' to quit): "
            print(prompt, " Press Cmd-D when done: ")
            query = sys.stdin.read().strip()
            print(".... ... .. .")
            if query.lower() in ("exit", "quit"):
                break

            t0 = time.time()
            # : List[Tuple[UUID, float]] = \
            top_k_article_similarities = \
                self.k_nearest_finder.find_k_nearest_articles(query, self.k_nearest, 0.75, 5)
            elapsed = time.time() - t0

            self.display_nearest_articles(query, top_k_article_similarities, elapsed)

    def display_nearest_segments(self, query, nearest_segments, elapsed):
        print('\n' * 5)
        print("Nearest Segments ", ">>>> " * 10)
        print("Nearest Segments ", ">>>> " * 10)
        print("QUERY:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s" + "---- " * 10)

        for i, result_element in enumerate(nearest_segments):
            score = result_element.similarity

            segment_record = result_element.record
            index = segment_record.segment_index
            offset = segment_record.offset
            length = segment_record.length

            caption = result_element.caption
            text = result_element.text

            print(f"{i + 1}. Segment Index: {index}, Score: {score:.4f}, "
                  f"(off: {offset}, len: {length})")
            print(f"Article: {caption}")
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


def get_app_config(logger) -> AppConfig:
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.debug(f"Using config file: {config_file}")

    app_config = load_app_config(config_file)
    logger.info(f"AppConfig: {app_config}")

    return app_config


def main():
    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-k", "--k-nearest", type=int, default=5,
                        help="Number of nearest neighbors")
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--max-documents", type=int, default=3)
    parser.add_argument("--log-level", type=str, default="INFO")
    args, _ = parser.parse_known_args()

    log_level_upper = args.log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    logging.basicConfig(level=numeric_level)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    app_config = get_app_config(logger)

    k_nearest = args.k_nearest
    threshold = args.threshold
    max_documents = args.max_documents

    lookup_cli = LookupCLI(logger, app_config, k_nearest, threshold, max_documents)
    lookup_cli.run()


if __name__ == "__main__":
    main()

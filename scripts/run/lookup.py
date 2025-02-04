#!/usr/bin/env python

import re
import sys
import time
import logging
import argparse

from search.stores import Stores
from xutils.app_config import AppConfig
from xutils.load_config import get_app_config
from gen.element.element import Element
from search.k_nearest_finder import KNearestFinder
from search.services.combined_service import (
    CombinedService,
    CombinedRequest,
    Kind,
    Action,
    parse_enum,
    CombinedResponse
)


class LookupCLI:
    def __init__(
        self,
        logger: logging.Logger,
        app_config: AppConfig,
        k_nearest: int,
        threshold: float,
        max_documents: int,
        action: Action
    ) -> None:
        self.app_config = app_config
        self.k_nearest = k_nearest
        self.threshold = threshold
        self.max_documents = max_documents
        self.action = action

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
            answer = response.answer
            elapsed = time.time() - t0

            results = response.results
            self.display_nearest_segments(query, results, answer, elapsed)

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

        kind = Kind.SEGMENT
        action = self.action

        if query.lower().startswith("search:"):
            action = Action.SEARCH
            query = query[len("search:"):].strip()
        elif query.lower().startswith("rag:"):
            action = Action.RAG
            query = query[len("rag:"):].strip()

        combined_request = CombinedRequest(
            action=action,
            kind=kind,
            query=query,
            k=k_nearest,
            threshold=threshold,
            max=max_documents
        )
        combined_response = self.service.combined(combined_request)
        return combined_response

    def run_articles(self):
        while True:
            print("Enter a query sentence (or 'exit' to quit):")
            print("Press Cmd-D when done. Use prefix 'search' or 'rag' to override action.")
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

    def display_nearest_segments(self, query, nearest_segments, answer, elapsed):
        print(">" * 100)
        print('\n' * 3)
        print("QUERY:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s, found: {len(nearest_segments)} "
              "results " + "---- " * 10)

        print("\n\nRAG Answer:")
        print(answer)
        print("-" * 50)
        print('\n' * 2)

        for i, result_element in enumerate(nearest_segments):
            score = result_element.similarity

            segment_record = result_element.record
            index = segment_record.segment_index
            offset = segment_record.offset
            length = segment_record.length

            caption = self.clean_header(result_element.caption)
            text = result_element.text

            print(f"\nResult {i + 1}: Segment Index: {index}, Score: {score:.4f}, "
                  f"(offset: {offset}, length: {length})")
            print(f"Article: {caption}")
            print("Text:")
            print(text)
            print('\n' * 2)

        print("-" * 100)
        print("query:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s, found: {len(nearest_segments)} "
              "results " + "---- " * 10)
        print("<" * 100)

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

    @staticmethod
    def clean_header(text):
        text = text.replace("\n", "")
        text = re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

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


def main():
    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-k", "--k-nearest", type=int, default=5,
                        help="Number of nearest neighbors")
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--max-documents", type=int, default=3)
    parser.add_argument("--log-level", type=str, default="INFO")
    parser.add_argument("--action", type=str, choices=["search", "rag"], default="search",
                        help="Specify the action: 'search' or 'rag'")
    args, _ = parser.parse_known_args()

    log_level_upper = args.log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    logging.basicConfig(level=numeric_level)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    app_config = get_app_config(logger)

    action = parse_enum(Action, args.action)

    k_nearest = args.k_nearest
    threshold = args.threshold
    max_documents = args.max_documents

    lookup_cli = LookupCLI(logger, app_config, k_nearest, threshold, max_documents, action)
    lookup_cli.run()


if __name__ == "__main__":
    main()

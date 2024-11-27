import sys
import time
import logging
import argparse
import numpy as np
import pandas as pd
from uuid import UUID
from pathlib import Path
from typing import List, Tuple
from typing import Optional as Opt
from numpy.typing import NDArray

from scipy.spatial.distance import cdist

from gen.encoder import Encoder
from gen.embedding_store import EmbeddingStore

from gen.element.store import Store
from gen.element.element import Element
from gen.element.article import Article
from gen.element.extended_segment import ExtendedSegment


__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.fragment")
__import__("gen.element.list_container")


class Stores:
    def __init__(self, args):
        self.args: argparse.Namespace = args

        self._segments_loaded = False

        self._uids: Opt[List[UUID]] = None
        self._embeddings: Opt[NDArray] = None

        self._extended_segments: Opt[List[ExtendedSegment]] = None
        self._articles: Opt[List[Article]] = None

    def _load_segments(self):
        if not self._segments_loaded:
            segment_file_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")
            text_file_path = Path(args.text)
            segment_store = Store()
            segment_store.load_elements(text_file_path, segment_file_path)
            self._segments_loaded = True

    @property
    def embeddings(self) -> Tuple[List[UUID], NDArray]:
        if self._embeddings is None:
            embedding_store_path = Path(f"{args.path_prefix}_{args.max_len}_embeddings.npz")
            embedding_store = EmbeddingStore(embedding_store_path)
            self._uids, self._embeddings = embedding_store.load_embeddings()
        return self._uids, self._embeddings

    @property
    def extended_segments(self) -> Store:
        if self._extended_segments is None:
            self._load_segments()
            extended_segments = [element for element in Element.instances.values()
                                 if isinstance(element, ExtendedSegment)]
            self._extended_segments = extended_segments
        return self._extended_segments

    @property
    def articles(self) -> List[Article]:
        if self._articles is None:
            self._load_segments()
            articles = [element for element in Element.instances.values()
                        if isinstance(element, Article)]
            self._articles = articles
        return self._articles

    def get_embeddings_article_ids(self) -> List[UUID]:
        extended_segments = self.extended_segments
        article_ids = [seg.article.uid for seg in extended_segments]
        return article_ids


class KNearestFinder:
    def __init__(self, args: argparse.Namespace, stores: Stores):
        self.args = args
        self.stores = stores
        self.encoder = Encoder(1)

        self._uids = None
        self._embedding_matrix = None

    @property
    def embedding_matrix(self):
        if self._embedding_matrix is None:
            uids, embeddings = self.stores.embeddings
            if len(embeddings) == 0:
                raise ValueError("No embeddings found in the store.")
            self._uids = uids
            self._embedding_matrix = np.stack(embeddings)
        return self._uids, self._embedding_matrix

    def find_k_nearest_segments(self, query: str, k: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest segments based on cosine similarity.
        :return: List of tuples (segment_id, similarity_score) for K-nearest neighbors.
        """
        uids, embedding_matrix = self.embedding_matrix

        # Encode the input sentence using the encoder
        query_embedding = self.encoder.encode([query])

        # Compute cosine similarity between the query and stored embeddings
        similarities = 1 - cdist(query_embedding, embedding_matrix, metric='cosine')
        similarities = similarities.flatten()

        # Find the top K most similar embeddings
        similarities_sorted = np.argsort(similarities)
        top_k_indices = similarities_sorted[-k:][::-1]

        top_k_segment_similarities = [(uids[i], similarities[i]) for i in top_k_indices]
        return top_k_segment_similarities

    def find_k_nearest_articles(self, query: str, k: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest articles based on cosine similarity.
        :return: List of tuples (article_id, similarity_score) for K-nearest neighbors.
        """
        uids, embedding_matrix = self.embedding_matrix

        # Encode the input sentence using the encoder
        query_embedding = self.encoder.encode([query])

        # Compute cosine similarity between the query and stored embeddings
        similarities = 1 - cdist(query_embedding, embedding_matrix, metric='cosine')
        similarities = similarities.flatten()

        article_ids = self.stores.get_embeddings_article_ids()

        # assuming that article_ids and similarities are in the same order
        df = pd.DataFrame({
            'seg_id': self._uids,
            'art_id': article_ids,
            'similarity': similarities
        })
        agg_df = df.groupby('art_id').agg({'similarity': 'max'}).reset_index()
        sorted_df = agg_df.sort_values(by='similarity', ascending=False)
        top_k_article_similarities = sorted_df.head(k)

        return top_k_article_similarities


class LookupCLI:
    def __init__(self, args):
        self.args = args
        self.stores = Stores(args)
        self.k_nearest_finder = KNearestFinder(args, self.stores)
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
            nearest_articles_df: List[Tuple[UUID, float]] = \
                self.k_nearest_finder.find_k_nearest_articles(query, self.args.k)
            elapsed = time.time() - t0

            self.display_nearest_articles(query, nearest_articles_df, elapsed)

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

    def display_nearest_articles(self, query, nearest_articles_df, elapsed):
        print("\n\n\n\n")
        print("Nearest Articles ", ">>>> " * 10)
        print("Nearest Articles ", ">>>> " * 10)
        print("QUERY:", query)
        print(f"query length: {len(query)}, {elapsed:.4f}s" + "---- " * 10)
        for i, (uid, score) in enumerate(nearest_articles_df[['art_id', 'similarity']].values):
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

    @property
    def article_map(self):
        if self._article_map is None:
            articles = self.stores.articles
            self._article_map = {article.uid: article for article in articles}
        return self._article_map

    def get_extended_segment(self, uid):
        return self.extended_segment_map[uid]

    def get_article(self, uid):
        return self.article_map[uid]


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

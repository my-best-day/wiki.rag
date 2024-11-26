import sys
import logging
import argparse
import numpy as np
from uuid import UUID
from pathlib import Path
from typing import List, Tuple

from scipy.spatial.distance import cdist

from gen.encoder import Encoder
from gen.embedding_store import EmbeddingStore

from gen.element.store import Store
from gen.element.element import Element
from gen.element.extended_segment import ExtendedSegment


__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.fragment")
__import__("gen.element.list_container")


class KNearestSegments:
    def __init__(self, args):
        self.args = args
        self.encoder = Encoder(1)
        self.uids, self.embedding_matrix = KNearestSegments.load_embedding_matrix(args)

    @staticmethod
    def load_embedding_matrix(args):
        embedding_store_path = Path(f"{args.path_prefix}_{args.max_len}_embeddings.npz")
        embedding_store = EmbeddingStore(embedding_store_path)
        uids, embeddings = embedding_store.load_embeddings()
        if len(embeddings) == 0:
            raise ValueError("No embeddings found in the store.")
        embedding_matrix = np.stack(embeddings)
        return uids, embedding_matrix

    def find_k_nearest_segments(self, query: str, k: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest segments based on cosine similarity.
        :return: List of tuples (segment_id, similarity_score) for K-nearest neighbors.
        """
        # Encode the input sentence using the encoder
        query_embedding = self.encoder.encode([query])

        # Compute cosine similarity between the query and stored embeddings
        similarities = 1 - cdist(query_embedding, self.embedding_matrix, metric='cosine')
        similarities = similarities.flatten()

        # Find the top K most similar embeddings
        similarities_sorted = np.argsort(similarities)
        top_k_indices = similarities_sorted[-k:][::-1]

        top_k_segment_similarities = [(self.uids[i], similarities[i]) for i in top_k_indices]
        return top_k_segment_similarities


class LookupCLI:
    def __init__(self, args):
        self.args = args
        self.k_nearest_segments = KNearestSegments(args)
        self._segment_map = None

    def run(self):
        while True:
            prompt = "Enter a query sentence (or 'exit' to quit): "
            print(prompt, " Press Cmd-D when done: ")
            query = sys.stdin.read().strip()
            print(".... ... .. .")
            if query.lower() in ("exit", "quit"):
                break

            # [(segment uid, similarity score),...]
            nearest_segments: List[Tuple[UUID, float]] = \
                self.k_nearest_segments.find_k_nearest_segments(query, self.args.k)

            self.display_nearest_segments(query, nearest_segments)

    def display_nearest_segments(self, query, nearest_segments):

        print("Nearest Segments ", ">>>> " * 10)
        print("QUERY: ", query)
        print("---- " * 10)
        for i, (uid, score) in enumerate(nearest_segments):
            segment = self.get_segment(uid)
            print(f"UID: {uid}, Score: {score}")
            print(segment.text)
            print(f"{i + 1}. Segment ID: {uid}, Score: {score:.4f}, "
                  f"(off: {segment.offset}, len: {len(segment.text)})")
            print(segment.text)
            print("<--- " * 10, "\n")

    @property
    def segment_map(self):
        if self._segment_map is None:
            args = self.args
            store = Store()
            text_file_path = Path(args.text)
            segment_file_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")

            store.load_elements(text_file_path, segment_file_path)
            extended_segments = [element for element in Element.instances.values()
                                 if isinstance(element, ExtendedSegment)]
            self._segment_map = {seg.uid: seg for seg in extended_segments}
        return self._segment_map

    def get_segment(self, uid):
        return self.segment_map[uid]


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

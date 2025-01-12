#!/usr/bin/env python
"""
Evaluates similarity preservation of the embeddings.
"""
import sys
import numpy as np
from scipy.spatial.distance import cosine


class CheckSimilarityPreservation:

    def __init__(self, sample_size, top_k):
        self.sample_size = sample_size
        self.top_k = top_k

    def similarity_preservation(self, orig_emb, trans_emb):
        return self.compute_similarity_preservation(
            orig_emb, trans_emb, self.sample_size, self.top_k)

    @staticmethod
    def compute_similarity_preservation(orig_emb, trans_emb, sample_size=1000, top_k=10):
        """
        Measure how well relative similarities are preserved after transformation

        Args:
        - original_embeddings: Original embedding matrix
        - transformed_embeddings: Transformed embedding matrix
        - top_k: Number of nearest neighbors to compare

        Returns:
        - Similarity preservation score (0-1, higher is better)
        """
        # Use the entire dataset if sample_size is not positive
        if sample_size <= 0 or sample_size > len(orig_emb):
            sample_size = len(orig_emb)

        # Randomly sample indices
        rng = np.random.default_rng(seed=42)
        sample_indices = rng.choice(len(orig_emb), size=sample_size, replace=False)

        # Compute preservation for sampled embeddings
        preservation_scores = []

        for idx in sample_indices:
            # Original nearest neighbors
            orig_dists = [cosine(orig_emb[idx], orig_emb[j])
                          for j in sample_indices if j != idx]
            orig_top_k = np.argsort(orig_dists)[:top_k]

            # Transformed nearest neighbors
            trans_dists = [cosine(trans_emb[idx], trans_emb[j])
                           for j in sample_indices if j != idx]
            trans_top_k = np.argsort(trans_dists)[:top_k]

            # Compute overlap
            overlap = len(set(orig_top_k) & set(trans_top_k))
            preservation_scores.append(overlap / top_k)

        return np.mean(preservation_scores)

    def compare_embeddings(self, orig_files, trans_files):
        """
        Compare embeddings from original and transformed files
        """
        for orig_file in orig_files:
            print("Original File:", orig_file)
            orig_emb = np.load(orig_file)["embeddings"]

            for trans_file in trans_files:
                if orig_file == trans_file:
                    print("\tSkipping self-comparison")
                    continue

                print("\tTransformed File:", trans_file)

                trans_emb = np.load(trans_file)["embeddings"]

                similarity = self.similarity_preservation(orig_emb, trans_emb)
                print(f"\tPreservation Score: {similarity:.3f}")


# Example usage
def compare_embedding_techniques(comparer):
    original_files = [
        "data/train_5000_768_embeddings.npz",
        "data/train_5000_512_embeddings.npz",
        "data/train_5000_256_embeddings.npz",
        "data/train_5000_128_embeddings.npz",
    ]

    transformed_files = [
        "data/train_5000_768_embeddings.npz",
        "data/train_5000_512_embeddings.npz",
        "data/train_5000_256_embeddings.npz",
        "data/train_5000_128_embeddings.npz",
    ]
    comparer.compare_embeddings(original_files, transformed_files)


def compare_embeddings_params(comparer):
    max_len = 5000

    originals = [
        [max_len, 768, "float32"],
    ]

    transformed = [
        [max_len, 768, "float32"],
        [max_len, 512, "float32"],
        [max_len, 256, "float32"],
        [max_len, 128, "float32"],
        [max_len, 768, "float16"],
        [max_len, 512, "float16"],
        [max_len, 256, "float16"],
        [max_len, 128, "float16"],
        [max_len, 768, "int8"],
        [max_len, 512, "int8"],
        [max_len, 256, "int8"],
        [max_len, 128, "int8"],
        [max_len, 768, "uint8"],
        [max_len, 512, "uint8"],
        [max_len, 256, "uint8"],
        [max_len, 128, "uint8"],
    ]

    original_files = [embed_store_path("data/train", *params) for params in originals]
    transformed_files = [embed_store_path("data/train", *params) for params in transformed]
    comparer.compare_embeddings(original_files, transformed_files)


def embed_store_path(prefix, max_len, dim, stype):
    """
    Generate a path based on the template and parameters
    Example: store_path("data/train_{max_len}_{dim}_{stype}.npz", 5000, 768, "float16")
    """
    type_part = f"_{stype}" if stype != "float32" else ""
    path = f"{prefix}_{max_len}_{dim}{type_part}_embeddings.npz"
    return path


if __name__ == "__main__":
    comparer = CheckSimilarityPreservation(sample_size=1000, top_k=10)
    # expect argv to be at least 3
    if len(sys.argv) == 2 and sys.argv[1] == "compare":
        compare_embedding_techniques(comparer)
    elif len(sys.argv) == 2 and sys.argv[1] == "params":
        compare_embeddings_params(comparer)
    elif len(sys.argv) != 3:
        print("Usage: python check_similarity_preservation.py <original_file> <transformed_file>")
        sys.exit(1)
    else:
        orig_file = sys.argv[1]
        trans_file = sys.argv[2]
        comparer.compare_embeddings(
            orig_files=[orig_file], trans_files=[trans_file])

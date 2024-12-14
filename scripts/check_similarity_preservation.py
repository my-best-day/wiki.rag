#!/usr/bin/env python
"""
Evaluates similarity preservation of the embeddings.
"""
import sys
import numpy as np
from scipy.spatial.distance import cosine


def similarity_preservation(orig_emb, trans_emb, sample_size=1000, top_k=10):
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


def compare_embeddings(original_files, transformed_files):
    for original_file in original_files:
        print("Original File:", original_file)
        original_embeddings = np.load(original_file)["embeddings"]

        for transformed_file in transformed_files:
            if original_file == transformed_file:
                print("\tSkipping self-comparison")
                continue

            print("\tTransformed File:", transformed_file)

            transformed_embeddings = np.load(transformed_file)["embeddings"]

            similarity = similarity_preservation(original_embeddings, transformed_embeddings)
            print(f"\tPreservation Score: {similarity:.3f}")


# Example usage
def compare_embedding_techniques():
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
    compare_embeddings(original_files, transformed_files)


def compare_embeddings_params():
    max_len = 5000

    originals = [
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

    transformed = originals

    original_files = [embed_store_path("data/train", *params) for params in originals]
    transformed_files = [embed_store_path("data/train", *params) for params in transformed]
    compare_embeddings(original_files, transformed_files)


def embed_store_path(prefix, max_len, dim, stype):
    """
    Generate a path based on the template and parameters
    Example: store_path("data/train_{max_len}_{dim}_{stype}.npz", 5000, 768, "float16")
    """
    type_part = f"_{stype}" if stype != "float32" else ""
    path = f"{prefix}_{max_len}_{dim}{type_part}_embeddings.npz"
    return path


if __name__ == "__main__":
    # expect argv to be at least 3
    if len(sys.argv) == 2 and sys.argv[1] == "compare":
        compare_embedding_techniques()
    elif len(sys.argv) == 2 and sys.argv[1] == "params":
        compare_embeddings_params()
    elif len(sys.argv) != 3:
        print("Usage: python check_similarity_preservation.py <original_file> <transformed_file>")
        sys.exit(1)
    else:
        original_file = sys.argv[1]
        transformed_file = sys.argv[2]
        compare_embeddings(original_files=[original_file], transformed_files=[transformed_file])

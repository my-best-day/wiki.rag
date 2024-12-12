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


if __name__ == "__main__":
    # expect argv to be at least 3
    if len(sys.argv) == 2 and sys.argv[1] == "compare":
        compare_embedding_techniques()
    elif len(sys.argv) != 3:
        print("Usage: python check_similarity_preservation.py <original_file> <transformed_file>")
        sys.exit(1)
    else:
        original_file = sys.argv[1]
        transformed_file = sys.argv[2]
        compare_embeddings(original_files=[original_file], transformed_files=[transformed_file])

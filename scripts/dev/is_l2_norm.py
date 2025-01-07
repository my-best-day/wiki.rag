#!/usr/bin/env python

import sys
import numpy as np
from pathlib import Path
from gen.embedding_utils import EmbeddingUtils


def are_l2_normalized(store_path):
    data = np.load(store_path)
    embeddings = data["embeddings"]
    are_l2_norm = EmbeddingUtils.are_l2_normalized(embeddings)
    print(f"{'Yes' if are_l2_norm else 'No'}, embeddings "
          f"{'ARE L2' if are_l2_norm else 'are NOT L2'} normalized.")
    return are_l2_norm


if __name__ == "__main__":
    # $0 <embeddings-store>

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <embeddings-store>")
        sys.exit(2)

    if not Path(sys.argv[1]).exists():
        print(f"Embeddings store {sys.argv[1]} does not exist")
        sys.exit(2)

    embeddings_store = sys.argv[1]
    if are_l2_normalized(embeddings_store):
        sys.exit(1)
    else:
        sys.exit(0)

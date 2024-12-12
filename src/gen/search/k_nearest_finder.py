import numpy as np
import polars as pl
from uuid import UUID
from typing import List, Tuple, Optional
from xutils.timer import Timer

from gen.encoder import Encoder

from gen.search.stores import Stores


class KNearestFinder:
    def __init__(
            self, stores: Stores,
            target_dim: Optional[int] = None,
            l2_normalize: bool = True):
        self.stores = stores
        self.encoder = Encoder(1, target_dim, l2_normalize)

        self._uids = None
        self._embeddings = None
        self._normalized_embeddings = None

    @property
    def uids_and_embeddings(self):
        if self._uids is None or self._embeddings is None:
            self._uids, self._embeddings = self.stores.uids_and_embeddings
        return self._uids, self._embeddings

    @property
    def uids_and_normalized_embeddings(self):
        if self._normalized_embeddings is None:
            uids, embeddings = self.uids_and_embeddings
            self._normalized_embeddings = \
                embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return self._uids, self._normalized_embeddings

    def find_k_nearest_articles(
            self,
            query: str,
            k: int,
            threshold: float,
            max_results: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest articles based on cosine similarity.
        """
        # Step 1: Get precomputed embeddings, uids, and article IDs
        with Timer("uids and embeddings"):
            uids, normalized_embeddings = self.uids_and_normalized_embeddings
        with Timer("get article ids"):
            article_ids = self.stores.get_embeddings_article_ids()

        # Step 2: Encode, reduced-dim, and normalize the query
        with Timer("encode query"):
            reduced_normalized_query = self.encoder.encode([f"search_query: {query}"])

        # Step 3: Compute cosine similarities
        with Timer("compute similarities"):
            similarities = np.dot(normalized_embeddings, reduced_normalized_query.T)
            similarities = similarities.flatten()

        # Step 4: Create a DataFrame for aggregation
        similarity_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pl.DataFrame(similarity_data)

        # Step 5: Aggregate similarities
        with Timer("aggregate similarities"):
            aggregated_df = df.group_by('art_id').agg(
                pl.col('similarity').mean().alias('mean_similarity')
            )

        # Step 6: Filter based on threshold
        with Timer("filter based on threshold"):
            filtered_df = aggregated_df.filter(pl.col('mean_similarity') > threshold)

        # Step 7: Select results based on the threshold and size of the filtered set
        with Timer("select results"):
            if len(filtered_df) >= k:
                # Case 1: Enough elements above threshold, return at most `max` results
                max_results = max(max_results, k)
                top_k_results = filtered_df.sort('mean_similarity', descending=True) \
                    .head(max_results).to_numpy()
            else:
                # Case 2: Not enough above threshold, return top `k` elements
                top_k_results = aggregated_df.sort('mean_similarity', descending=True) \
                    .head(k).to_numpy()

        # Convert to list of tuples
        top_k_results = [(row[0], row[1]) for row in top_k_results]
        return top_k_results

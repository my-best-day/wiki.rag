import copy
import numpy as np
import polars as pl
from uuid import UUID
from typing import List, Tuple
from xutils.embedding_config import EmbeddingConfig

from gen.encoder import Encoder
from gen.embedding_utils import EmbeddingUtils

from gen.search.stores import Stores


class KNearestFinder:
    def __init__(
            self, stores: Stores,
            embedding_config: EmbeddingConfig):

        self.stores = stores
        self.embed_config = copy.copy(embedding_config)
        self.embed_config.l2_normalize = True

        # no need to do a detour,
        if self.embed_config.norm_type is not None:
            self.embed_config.stype = self.embed_config.norm_type

        self.encoder = Encoder(1)

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
            _, embeddings = self.uids_and_embeddings

            self._normalized_embeddings = \
                EmbeddingUtils.morph_embeddings(embeddings, self.embed_config)

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
        uids, normalized_embeddings = self.uids_and_normalized_embeddings
        article_ids = self.stores.get_embeddings_article_ids()

        adjusted_query_embeddings = self.encode_query(query)

        # Step 3: Compute cosine similarities
        similarities = np.dot(normalized_embeddings, adjusted_query_embeddings.T)
        similarities = similarities.flatten()

        # Step 4: Create a DataFrame for aggregation
        similarity_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pl.DataFrame(similarity_data)

        # Step 5: Aggregate similarities
        aggregated_df = df.group_by('art_id').agg(
            pl.col('similarity').mean().alias('mean_similarity')
        )

        # Step 6: Filter based on threshold
        filtered_df = aggregated_df.filter(pl.col('mean_similarity') > threshold)

        # Step 7: Select results based on the threshold and size of the filtered set
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

    def encode_query(self, query: str) -> np.ndarray:
        # Step 2: Encode, reduced-dim, and normalize the query
        query_embeddings = self.encoder.encode([f"search_query: {query}"])

        # TODO: add support for norm-type
        reduced_normalized_query_embeddings = \
            EmbeddingUtils.morph_embeddings(
                query_embeddings, self.embed_config)

        return reduced_normalized_query_embeddings

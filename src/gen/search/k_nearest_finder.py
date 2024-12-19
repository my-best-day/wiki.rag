import copy
import torch
import logging
import numpy as np
import polars as pl
from uuid import UUID
from typing import List, Tuple
from xutils.embedding_config import EmbeddingConfig

from gen.encoder import Encoder
from gen.embedding_utils import EmbeddingUtils

from gen.search.stores import Stores
from xutils.timer import LoggingTimer, log_timeit

logger = logging.getLogger(__name__)


class KNearestFinder:
    def __init__(
            self, stores: Stores,
            embed_config: EmbeddingConfig):

        self.stores = stores
        self.input_embed_config = embed_config
        self.query_embed_config = copy.copy(embed_config)
        self.query_embed_config.l2_normalize = True

        # no need to do a detour,
        # if self.query_embed_config.norm_type is not None:
        #     self.query_embed_config.stype = self.query_embed_config.norm_type

        self.encoder = Encoder(1)

        self._uids = None
        self._embeddings = None
        self._normalized_embeddings = None

    @property
    def uids_and_embeddings(self):
        if self._uids is None or self._embeddings is None:
            self._uids, self._embeddings = self.stores.uids_and_embeddings
        return self._uids, self._embeddings

    # def uids_and_normalized_embeddings(self):
    #     return self._uids_and_normalized_embeddings()

    @property
    @log_timeit(logger=logger)
    def uids_and_normalized_embeddings(self):
        if self._normalized_embeddings is None:
            _, embeddings = self.uids_and_embeddings
            self._normalized_embeddings = \
                EmbeddingUtils.morph_embeddings(embeddings, self.input_embed_config)
        return self._uids, self._normalized_embeddings

    def find_k_nearest_articles(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.3,
        max_results: int = 10
    ) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest articles based on cosine similarity.
        """
        # Step 1: Get precomputed embeddings, uids, and article IDs
        uids, normalized_embeddings = self.uids_and_normalized_embeddings
        article_ids = self.stores.get_embeddings_article_ids()
        query_embeddings = self.encode_query(query)

        # Step 3: Compute cosine similarities
        similarities = self.torch_batched_similarity(
            normalized_embeddings,
            query_embeddings,
        )
        similarities = similarities.flatten()

        # Step 4: Create a DataFrame for aggregation
        timer = LoggingTimer('find_k_nearest_articles', logger=logger, level="DEBUG")
        df_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pl.DataFrame(df_data)
        timer.restart("created df")

        # Step 5: Aggregate similarities by article
        agg_df = df.group_by('art_id').agg(
            pl.col('similarity').mean().alias('mean_similarity')
        )
        timer.restart("aggregated df")

        # Step 6: Filter and sort results
        filtered_df = agg_df.filter(pl.col('mean_similarity') > threshold)
        timer.restart("filtered df")

        # Step 7: Select results based on threshold and filtered set size
        if len(filtered_df) >= k:
            # Case 1: Enough elements above threshold
            max_k = max(max_results, k)
            results_df = filtered_df.sort('mean_similarity', descending=True) \
                .head(max_k)
        else:
            # Case 2: Not enough above threshold, return top k elements
            results_df = agg_df.sort('mean_similarity', descending=True) \
                .head(k)

        top_k_results = results_df.to_numpy()
        timer.restart("selected results")

        return top_k_results

    @staticmethod
    @log_timeit(logger=logger)
    def torch_batched_similarity(normalized_embeddings, query_embedding, batch_size=100000):
        similarities = []
        for i in range(0, len(normalized_embeddings), batch_size):
            batch = normalized_embeddings[i:i + batch_size]
            batch_similarities = torch.matmul(
                torch.from_numpy(batch),
                torch.from_numpy(query_embedding.T)
            )
            similarities.append(batch_similarities.numpy())
        return np.concatenate(similarities, axis=0)

    @log_timeit(logger=logger)
    def encode_query(self, query: str) -> np.ndarray:
        # Step 1: Get embeddings
        query_embeddings = self.encoder.encode([query])

        # Step 2: Morph embeddings if needed
        adjusted_embeddings = EmbeddingUtils.morph_embeddings(
            query_embeddings,
            self.input_embed_config
        )

        return adjusted_embeddings

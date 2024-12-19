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

    @property
    @log_timeit(logger=logger)
    def uids_and_normalized_embeddings(self):
        if self._normalized_embeddings is None:
            _, embeddings = self.uids_and_embeddings
            self._normalized_embeddings = \
                EmbeddingUtils.morph_embeddings(embeddings, self.input_embed_config)
        return self._uids, self._normalized_embeddings

    def find_k_nearest_segments(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.3,
        max_results: int = 10
    ) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest segments based on cosine similarity.
        """
        uids, similarities = self.get_similarities(query)

        # Create a DataFrame for aggregation
        timer = LoggingTimer('find_k_nearest_articles', logger=logger, level="DEBUG")
        df_data = {
            'seg_id': uids,
            'similarity': similarities
        }
        df = pl.DataFrame(df_data)
        timer.restart("created df")

        result_tuples = self.pick_results(k, threshold, max_results, df, by='similarity')

        return result_tuples

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
        # Get cosine similarities
        uids, similarities = self.get_similarities(query)

        # Get article ids - for aggregation by article
        article_ids = self.stores.get_embeddings_article_ids()

        # Create a DataFrame for aggregation
        timer = LoggingTimer('find_k_nearest_articles', logger=logger, level="DEBUG")
        df_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pl.DataFrame(df_data)
        timer.restart("created df")

        # Aggregate similarities by article
        agg_df = df.group_by('art_id').agg(
            pl.col('similarity').mean().alias('mean_similarity')
        )
        timer.restart("aggregated df")

        result_tuples = self.pick_results(k, threshold, max_results, agg_df, by='mean_similarity')

        return result_tuples

    def get_similarities(self, query: str):
        """
        Get cosine similarities for a given query.
        """
        uids, normalized_embeddings = self.uids_and_normalized_embeddings
        query_embeddings = self.encode_query(query)

        similarities = self.torch_batched_similarity(
            normalized_embeddings,
            query_embeddings,
        )
        similarities = similarities.flatten()

        return uids, similarities

    def pick_results(self, k, threshold, max_results, df, by):
        timer = LoggingTimer('pick_results', logger=logger, level="DEBUG")

        q = max(k, max_results)
        top_q = df.top_k(q, by=by)
        timer.restart("top k")

        filtered_top_q = top_q.filter(pl.col(by) > threshold)
        timer.restart("filtered top k")

        if len(filtered_top_q) >= k:
            # if filtered results has enough elements, use them
            result_df = filtered_top_q.head(q)
        else:
            # otherwise, use unfiltered top k
            result_df = top_q.head(k)
        timer.restart("picked results")

        result_tuples = result_df.to_numpy()
        timer.restart("selected results")

        return result_tuples

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
            self.query_embed_config
        )

        return adjusted_embeddings

"""
Find the K-nearest segments or articles based on cosine similarity.
"""
import copy
import logging
from uuid import UUID
from typing import List, Tuple
from numpy.typing import NDArray
import torch
import numpy as np
import polars as pl

from gen.encoder import Encoder
from gen.embedding_utils import EmbeddingUtils
from search.stores import Stores
from xutils.timer import LoggingTimer, log_timeit
from xutils.embedding_config import EmbeddingConfig

logger = logging.getLogger(__name__)


class KNearestFinder:
    """
    Encode the query and find the K-nearest segments or articles based on cosine similarity.
    """

    def __init__(
        self,
        stores: Stores,
        embed_config: EmbeddingConfig
    ):
        """
        Initialize the K-nearest finder.
        Args:
            stores: Source of the embeddings and segment/document mapping.
            embed_config: The embedding config - used to encode the query.
        """
        self.stores = stores
        self.input_embed_config = embed_config
        self.query_embed_config = copy.copy(embed_config)
        self.query_embed_config.l2_normalize = True

        self.encoder = Encoder(1)

        # lazy loaded
        self._uids = None
        self._embeddings = None
        self._normalized_embeddings = None

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        """
        A list of the segments' uids and their embeddings.
        """
        if self._uids is None or self._embeddings is None:
            self._uids, self._embeddings = self.stores.uids_and_embeddings
        return self._uids, self._embeddings

    @property
    @log_timeit(logger=logger)
    def uids_and_normalized_embeddings(self) -> Tuple[List[UUID], NDArray]:
        """
        A list of the segments' uids and their normalized embeddings.
        """
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
        Returns a minimum of k of the most similar segments, along with up to
        max_results results that meet or exceed the threshold.
        Args:
            query: The query to find the nearest segments to.
            k: The number of nearest segments to find (not filtered by threshold).
            threshold: The threshold for the similarity score.
            max_results: The maximum number of above-threshold results to return.
        Returns:
            A list of tuples, each containing a segment id and a similarity score.
        """
        uids, similarities = self.get_similarities(query)

        # Create a DataFrame for aggregation
        timer = LoggingTimer('find_k_nearest_articles', logger=logger, level="DEBUG")
        df_data = {
            'seg_id': uids,
            'similarity': similarities
        }
        polars_df = pl.DataFrame(df_data)
        timer.restart("created df")

        result_tuples = self.pick_results(k, threshold, max_results, polars_df, by='similarity')

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
        Returns a minimum of k of the most similar articles, along with up to
        max_results results that meet or exceed the threshold.
        Args:
            query: The query to find the nearest articles to.
            k: The number of nearest articles to find (not filtered by threshold).
            threshold: The threshold for the similarity score.
            max_results: The maximum number of above-threshold results to return.
        """
        uids, similarities = self.get_similarities(query)

        # Get article ids - for aggregation by article
        article_indexes = self.stores.get_embeddings_article_indexes()

        # Create a DataFrame for aggregation
        timer = LoggingTimer('find_k_nearest_articles', logger=logger, level="DEBUG")
        df_data = {
            'seg_id': uids,
            'art_id': article_indexes,
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

    def get_similarities(self, query: str) -> Tuple[List[UUID], NDArray]:
        """
        Get cosine similarities for a given query.
        Encode the query and get the similarities.
        """
        uids, normalized_embeddings = self.uids_and_normalized_embeddings
        query_embeddings = self.encode_query(query)

        similarities = self.torch_batched_similarity(
            normalized_embeddings,
            query_embeddings,
        )
        similarities = similarities.flatten()

        return uids, similarities

    def pick_results(
        self,
        k: int,
        threshold: float,
        max_results: int,
        polars_df: pl.DataFrame,
        by: str
    ) -> List[Tuple[UUID, float]]:
        """
        Pick the results from the (Polars)DataFrame filtered by k, threshold, and max_results.
        Args:
            k: The minimum number of results to pick.
            threshold: The threshold for the similarity score.
            max_results: The maximum number of results that meet or exceed the threshold.
            polars_df: The DataFrame to pick the results from.
            by: The column to pick the results by.
        Returns:
            A list of tuples, each containing a segment id and a similarity score.
        """
        timer = LoggingTimer('pick_results', logger=logger, level="DEBUG")

        q = max(k, max_results)
        top_q = polars_df.top_k(q, by=by)
        timer.restart("top k")

        filtered_top_q = top_q.filter(pl.col(by) > threshold)
        timer.restart("filtered top k")

        if len(filtered_top_q) >= k:
            # if filtered results has enough elements, use them
            polars_result_df = filtered_top_q.head(q)
        else:
            # otherwise, use unfiltered top k
            polars_result_df = top_q.head(k)
        timer.restart("picked results")

        result_tuples = polars_result_df.rows()
        timer.restart("selected results")

        return result_tuples

    @staticmethod
    @log_timeit(logger=logger)
    def torch_batched_similarity(
        normalized_embeddings: NDArray,
        query_embedding: NDArray,
        batch_size: int = 100000
    ) -> NDArray:
        """
        Get the cosine similarities for a given query.
        Args:
            normalized_embeddings: The normalized embeddings to compare to the query.
            query_embedding: The query embedding to compare to the normalized embeddings.
            batch_size: The batch size for the similarity calculation.
        Returns:
            A numpy array of the cosine similarities.
        """
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
        """
        Encode the query and morph the embeddings if needed.
        Args:
            query: The query to encode.
        Returns:
            A numpy array of the encoded query.
        """
        # Step 1: Get embeddings
        query_embeddings = self.encoder.encode([query])

        # Step 2: Morph embeddings if needed
        adjusted_embeddings = EmbeddingUtils.morph_embeddings(
            query_embeddings,
            self.query_embed_config
        )

        return adjusted_embeddings

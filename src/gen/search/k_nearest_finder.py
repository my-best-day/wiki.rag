import numpy as np
import pandas as pd
import polars as pl
from uuid import UUID
from typing import List, Tuple
from xutils.timer import Timer
from scipy.spatial.distance import cdist

from gen.encoder import Encoder

from gen.search.stores import Stores


class KNearestFinder:
    def __init__(self, stores: Stores):
        self.stores = stores
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
            uids, embeddings = self.uids_and_embeddings
            self._normalized_embeddings = \
                embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return self._uids, self._normalized_embeddings

    # TODO: add threshold ... include k results, m results with
    # similarity greater than threshold
    def find_k_nearest_segments(self, query: str, k: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest segments based on cosine similarity.
        :return: List of tuples (segment_id, similarity_score) for K-nearest neighbors.
        """
        uids, embeddings = self.uids_and_embeddings

        # Encode the input sentence using the encoder
        query = f"search_query: {query}"
        query_embedding = self.encoder.encode([query])

        # Compute cosine similarity between the query and stored embeddings
        similarities = 1 - cdist(query_embedding, embeddings, metric='cosine')
        similarities = similarities.flatten()

        # Find the top K most similar embeddings
        similarities_sorted = np.argsort(similarities)
        top_k_indices = similarities_sorted[-k:][::-1]

        top_k_segment_similarities = [(uids[i], similarities[i]) for i in top_k_indices]
        return top_k_segment_similarities

    def find_k_nearest_articles(self, query: str, k: int, threshold: float,
                                max: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest articles based on cosine similarity.
        :return: List of tuples (article_id, similarity_score) for K-nearest neighbors.
        """
        with Timer("uids and embeddings"):
            uids, embeddings = self.uids_and_embeddings

        with Timer("encode"):
            # Encode the input sentence using the encoder
            query = f"search_query: {query}"
            query_embedding = self.encoder.encode([query])

        with Timer("cosine similarity"):
            # Compute cosine similarity between the query and stored embeddings
            similarities = 1 - cdist(query_embedding, embeddings, metric='cosine')

        with Timer("flatten"):
            similarities = similarities.flatten()

        with Timer("get article ids"):
            article_ids = self.stores.get_embeddings_article_ids()
        print("article id 0: ", article_ids[0])

        # assuming that article_ids and similarities are in the same order
        df = pd.DataFrame({
            'seg_id': self._uids,
            'art_id': article_ids,
            'similarity': similarities
        })

        with Timer("epilogue"):
            agg_df = df.groupby('art_id').agg({'similarity': 'max'}).reset_index()
            sorted_df = agg_df.sort_values(by='similarity', ascending=False)
            passing_df = sorted_df[sorted_df['similarity'] > threshold]
            if len(passing_df) > k:
                top_k_article_similarities = passing_df.head(max).values.tolist()
            else:
                top_k_article_similarities = sorted_df.head(k).values.tolist()

        return top_k_article_similarities

    def find_k_nearest_articles2(
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

        # Step 2: Encode and normalize the query
        with Timer("encode query"):
            encoded_query = self.encoder.encode([f"search_query: {query}"])
        with Timer("normalize query"):
            normalized_query = encoded_query / np.linalg.norm(encoded_query)  # Normalize query

        # Step 3: Compute cosine similarities
        with Timer("compute similarities"):
            similarities = np.dot(normalized_embeddings, normalized_query.T)
            similarities = similarities.flatten()

        # Step 4: Create a DataFrame for aggregation
        similarity_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pd.DataFrame(similarity_data)

        # Step 5: Aggregate similarities
        with Timer("aggregate similarities"):
            aggregated_df = df.groupby('art_id', as_index=False).agg({'similarity': 'mean'})

        # Step 6: Filter based on threshold
        with Timer("filter based on threshold"):
            filtered_df = aggregated_df[aggregated_df['similarity'] > threshold]

        # Step 7: Select results based on the threshold and size of the filtered set
        with Timer("select results"):
            if len(filtered_df) >= k:
                # Case 1: Enough elements above threshold, return at most `max` results
                max_results = max(max_results, k)
                top_k_results = filtered_df.nlargest(max_results, 'similarity').values.tolist()
            else:
                # Case 2: Not enough above threshold, return top `k` elements
                top_k_results = aggregated_df.nlargest(k, 'similarity').values.tolist()

        return top_k_results

    def find_k_nearest_articles2_pl(
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

        # Step 2: Encode and normalize the query
        with Timer("encode query"):
            encoded_query = self.encoder.encode([f"search_query: {query}"])
        with Timer("normalize query"):
            normalized_query = encoded_query / np.linalg.norm(encoded_query)  # Normalize query

        # Step 3: Compute cosine similarities
        with Timer("compute similarities"):
            similarities = np.dot(normalized_embeddings, normalized_query.T)
            similarities = similarities.flatten()

        # Step 4: Create a DataFrame for aggregation
        similarity_data = {
            'seg_id': uids,
            'art_id': article_ids,
            'similarity': similarities
        }
        df = pl.DataFrame(similarity_data)
        print("COLUMN NAMES: ", df.columns)
        print("DF HEAD: ", df.head())

        # Step 5: Aggregate similarities
        with Timer("aggregate similarities"):
            aggregated_df = df.groupby('art_id').agg(
                pl.col('similarity').mean().alias('mean_similarity'))

        # Step 6: Filter based on threshold
        with Timer("filter based on threshold"):
            filtered_df = aggregated_df.filter(pl.col('mean_similarity') > threshold)

        # Step 7: Select results based on the threshold and size of the filtered set
        with Timer("select results"):
            if len(filtered_df) >= k:
                # Case 1: Enough elements above threshold, return at most `max` results
                max_results = max(max_results, k)
                top_k_results = filtered_df.sort('mean_similarity', reverse=True) \
                    .head(max_results).to_numpy()
            else:
                # Case 2: Not enough above threshold, return top `k` elements
                top_k_results = aggregated_df.sort('mean_similarity', reverse=True) \
                    .head(k).to_numpy()

        top_k_results = top_k_results.to_list()
        return top_k_results

    def find_k_nearest_articles2_plx(
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

        # Step 2: Encode and normalize the query
        with Timer("encode query"):
            encoded_query = self.encoder.encode([f"search_query: {query}"])
        with Timer("normalize query"):
            normalized_query = encoded_query / np.linalg.norm(encoded_query)  # Normalize query

        # Step 3: Compute cosine similarities
        with Timer("compute similarities"):
            similarities = np.dot(normalized_embeddings, normalized_query.T)
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
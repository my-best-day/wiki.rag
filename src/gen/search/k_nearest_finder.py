import numpy as np
import pandas as pd
from uuid import UUID
from typing import List, Tuple

from scipy.spatial.distance import cdist

from gen.encoder import Encoder

from gen.search.stores import Stores


class KNearestFinder:
    def __init__(self, stores: Stores):
        self.stores = stores
        self.encoder = Encoder(1)

        self._uids = None
        self._embeddings = None

    @property
    def uids_and_embeddings(self):
        if self._uids is None or self._embeddings is None:
            self._uids, self._embeddings = self.stores.uids_and_embeddings
        return self._uids, self._embeddings

    # TODO: add threshold ... include k results, m results with
    # similarity greater than threshold
    def find_k_nearest_segments(self, query: str, k: int) -> List[Tuple[UUID, float]]:
        """
        Find the K-nearest segments based on cosine similarity.
        :return: List of tuples (segment_id, similarity_score) for K-nearest neighbors.
        """
        uids, embeddings = self.uids_and_embeddings

        # Encode the input sentence using the encoder
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
        uids, embeddings = self.uids_and_embeddings

        # Encode the input sentence using the encoder
        query_embedding = self.encoder.encode([query])

        # Compute cosine similarity between the query and stored embeddings
        similarities = 1 - cdist(query_embedding, embeddings, metric='cosine')
        similarities = similarities.flatten()

        article_ids = self.stores.get_embeddings_article_ids()

        # assuming that article_ids and similarities are in the same order
        df = pd.DataFrame({
            'seg_id': self._uids,
            'art_id': article_ids,
            'similarity': similarities
        })
        agg_df = df.groupby('art_id').agg({'similarity': 'max'}).reset_index()
        sorted_df = agg_df.sort_values(by='similarity', ascending=False)
        passing_df = sorted_df[sorted_df['similarity'] > threshold]
        if len(passing_df) > k:
            top_k_article_similarities = passing_df.head(max).values.tolist()
        else:
            top_k_article_similarities = sorted_df.head(k).values.tolist()

        return top_k_article_similarities

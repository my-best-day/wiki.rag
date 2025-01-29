import os
import logging
from uuid import UUID
from openai import OpenAI
from typing import List, Tuple
from dataclasses import dataclass

from xutils.timer import LoggingTimer
from gen.data.segment_record import SegmentRecord
from xutils.embedding_config import EmbeddingConfig
from search.stores import Stores
from search.k_nearest_finder import KNearestFinder

logger = logging.getLogger(__name__)


@dataclass
class ResultElement:
    similarity: float
    record: SegmentRecord
    caption: str
    text: str


class Kind:
    _instances = {}

    def __init__(self, name: str):
        self.name = name
        Kind._instances[name] = self

    @classmethod
    def parse(cls, str):
        kind = Kind._instances.get(str, None)
        if kind is None:
            raise ValueError(f"Invalid kind: {str}")
        return kind

    def __str__(self):
        return self.name


Kind.Article = Kind("article")
Kind.Segment = Kind("segment")


@dataclass
class CombinedRequest:
    action: str
    kind: Kind
    query: str
    k: int
    threshold: float
    max: int

    def __str__(self):
        return f"CombinedRequest(action={self.action}, kind={self.kind}, " \
               f"query={self.query}, k={self.k}, threshold={self.threshold}, max={self.max})"


@dataclass
class CombinedResponse:
    prompt: str
    results: List[ResultElement]
    answer: str
    total_length: int


class CombinedService:

    def __init__(
        self,
        stores: Stores,
        embed_config: EmbeddingConfig,
        finder: KNearestFinder
    ) -> None:
        self.stores = stores
        self.embed_config = embed_config
        self.finder = finder

        self._client = None

    @property
    def openai_client(self):
        PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
        if PROJECT_ID is None:
            raise ValueError("OPENAI_PROJECT_ID is not set")
        if self._client is None:
            self._client = OpenAI(project=PROJECT_ID)
        return self._client

    def combined(
        self,
        combined_request: CombinedRequest
    ) -> CombinedResponse:

        timer = LoggingTimer('combined', logger=logger, level="INFO")

        element_id_similarity_tuple_list = self.find_nearest_elements(combined_request)

        timer.restart(f"Found {len(element_id_similarity_tuple_list)} results")

        element_results = self.get_element_results(
            combined_request.kind, element_id_similarity_tuple_list)
        timer.restart(f"got element results (len: {len(element_results)})")

        total_length = 0
        for element_result in element_results:
            total_length += len(element_result.text)
        timer.restart(f"total length: {total_length}")

        if combined_request.action == "rag":
            prompt, answer = self.do_rag(combined_request.query, element_results)
        else:
            prompt, answer = "na", "na"
        timer.restart(f"did rag (prompt len: {len(prompt)}, answer len: {len(answer)})")

        total_elapsed = timer.total_time()
        timer.total(total_elapsed)

        combined_response = CombinedResponse(
            prompt=prompt,
            results=element_results,
            answer=answer,
            total_length=total_length
        )

        return combined_response

    def do_rag(self, query: str, element_results: List[ResultElement]):
        timer = LoggingTimer('do_rag', logger=logger, level="INFO")
        elements_text = self.get_elements_text(element_results)

        prompt = (
            f"question: {query}\n"
            "the following information has been retrieved to assist in the answering "
            f"of the question:\n{elements_text}"
        )

        if not query.startswith("what, are you doing? this is not right!"):
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. "
                        "You will answer the question based on the information provided. "
                        "If the information is not enough to answer the question, "
                        "you will say that you don't know. "
                        "If the information is too much to answer the question, "
                        "you will say that you are overwhelmed."
                    )
                },
                {
                    "role": "user",
                    "content": prompt}
                # {
                #     "role": "user",
                #     "content": "Say this is a test"
                # }
            ]
            # logger.info("prompt: %s", prompt)

            timer.restart("calling openai")
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.4,
                max_completion_tokens=1000
            )
            timer.restart("completion created")
            logger.info("completion: %s", completion)
            answer = completion.choices[0].message.content
        else:
            prompt, answer = "na", "na"

        return prompt, answer

    def find_nearest_elements(
        self,
        combined_request: CombinedRequest
    ) -> List[Tuple[UUID, float]]:

        kind = combined_request.kind
        query = combined_request.query
        k = combined_request.k
        threshold = combined_request.threshold
        max_results = combined_request.max

        if kind is Kind.Article:
            element_id_similarity_tuple_list = self.finder.find_k_nearest_articles(
                query, k=k, threshold=threshold, max_results=max_results)
        elif kind is Kind.Segment:
            element_id_similarity_tuple_list = self.finder.find_k_nearest_segments(
                query, k=k, threshold=threshold, max_results=max_results)

        return element_id_similarity_tuple_list

    def get_element_results(
        self,
        kind: Kind,
        element_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:

        if kind is Kind.Article:
            element_results = self.get_article_results(element_id_similarity_tuple_list)
        elif kind is Kind.Segment:
            element_results = self.get_segment_results(element_id_similarity_tuple_list)

        return element_results

    def get_article_results(
        self,
        article_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:
        results = []
        for article_id, similarity in article_id_similarity_tuple_list:
            article = self.stores.get_article(article_id)
            header_text = article.header.text
            caption_text = header_text
            results.append(ResultElement(similarity, article, caption_text))
        return results

    def get_segment_results(
        self,
        segment_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:
        results = []
        for segment_ind, similarity in segment_id_similarity_tuple_list:
            segment_record = self.stores.get_segment_record_by_index(segment_ind)
            segment_text = self.stores.get_segment_text(segment_record)
            article_index = segment_record.document_index
            article = self.stores.get_article_by_index(article_index)
            header_text = article.header.text
            caption_text = (
                f"{header_text} : "
                f"{segment_text[:60]}{'...' if len(segment_text) > 60 else ''}"
            )
            results.append(ResultElement(similarity, segment_record, caption_text, segment_text))
        return results

    def get_elements_text(self, element_results: List[ResultElement]) -> str:
        element_texts = []
        for i, (element_result) in enumerate(element_results):
            element_texts.append(f"Context document {i}: {element_result.record.text[:15000]}")
        elements_text = "\n\n".join(element_texts)
        return elements_text

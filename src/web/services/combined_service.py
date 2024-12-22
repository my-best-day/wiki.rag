import os
import logging
from uuid import UUID
from openai import OpenAI
from typing import List, Tuple
from dataclasses import dataclass

from xutils.timer import LoggingTimer
from gen.element.element import Element


logger = logging.getLogger(__name__)


@dataclass
class ElementResult:
    similarity: float
    element: Element
    caption: str


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
    results: List[ElementResult]
    answer: str
    total_length: int


class CombinedService:

    def __init__(self, state):
        self.state = state
        self.stores = state.stores
        self.embed_config = state.config.embed_config
        self.finder = state.finder
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
            total_length += element_result.element.char_length
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

    def do_rag(self, query: str, element_results: List[ElementResult]):
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
    ) -> List[ElementResult]:

        if kind is Kind.Article:
            element_results = self.get_article_results(element_id_similarity_tuple_list)
        elif kind is Kind.Segment:
            element_results = self.get_segment_results(element_id_similarity_tuple_list)

        return element_results

    def get_article_results(
        self,
        article_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ElementResult]:
        results = []
        for article_id, similarity in article_id_similarity_tuple_list:
            article = self.stores.get_article(article_id)
            header_text = article.header.text
            caption_text = header_text
            results.append(ElementResult(similarity, article, caption_text))
        return results

    def get_segment_results(
        self,
        segment_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ElementResult]:
        results = []
        for segment_id, similarity in segment_id_similarity_tuple_list:
            flat_segment = self.stores.get_segment(segment_id)
            article_uid = flat_segment.article_uid
            article = self.stores.get_article(article_uid)
            header_text = article.header.text
            caption_text = (
                f"{header_text} : "
                f"{flat_segment.text[:60]}{'...' if len(flat_segment.text) > 60 else ''}"
            )
            results.append(ElementResult(similarity, flat_segment, caption_text))
        return results

    def get_elements_text(self, element_results: List[ElementResult]) -> str:
        element_texts = []
        for i, (element_result) in enumerate(element_results):
            element_texts.append(f"Context document {i}: {element_result.element.text[:15000]}")
        elements_text = "\n\n".join(element_texts)
        return elements_text

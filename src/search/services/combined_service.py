"""
Combined service abstracts the access to the search and RAG services.
"""
import os
import logging
from enum import Enum
from uuid import UUID
from typing import List, Tuple
from openai import OpenAI
from pydantic.dataclasses import dataclass
from gen.data.segment_record import SegmentRecord
from xutils.timer import LoggingTimer
from xutils.embedding_config import EmbeddingConfig
from search.stores import Stores
from search.k_nearest_finder import KNearestFinder

logger = logging.getLogger(__name__)


class Kind(Enum):
    """
    The kind of the target element to search for.
    """
    ARTICLE = "article"
    SEGMENT = "segment"


class Action(Enum):
    """
    The action to perform.
    """
    SEARCH = "search"
    RAG = "rag"


def parse_enum(enum_class, value):
    """
    Parse an enum value.
    """
    assert issubclass(enum_class, Enum)
    assert isinstance(value, str)
    try:
        return enum_class[value.upper()]
    except KeyError:
        logger.exception("Invalid kind: %s", value)
        raise


@dataclass
class ResultElement:
    """a single search result"""
    similarity: float
    record: SegmentRecord
    caption: str
    text: str


@dataclass
class CombinedRequest:
    """
    The request for the combined service.
    """
    id: str
    action: Action
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
    """
    The response from the combined service.
    """
    id: str
    action: Action
    prompt: str
    results: List[ResultElement]
    answer: str
    total_length: int


class CombinedService:
    """
    The combined service.
    Abstracts the access to the search and RAG services.
    """

    def __init__(
        self,
        stores: Stores,
        embed_config: EmbeddingConfig,
        finder: KNearestFinder
    ) -> None:
        """
        Initialize the CombinedService.

        Args:
            stores (Stores): The stores for accessing data.
            embed_config (EmbeddingConfig): The configuration for embeddings.
            finder (KNearestFinder): The K-nearest finder for searching elements.
        """
        self.stores = stores
        self.embed_config = embed_config
        self.finder = finder

        self._client = None

    @property
    def openai_client(self):
        """Get the OpenAI client."""
        project_id = os.getenv("OPENAI_PROJECT_ID")
        if project_id is None:
            raise ValueError("OPENAI_PROJECT_ID is not set")
        if self._client is None:
            self._client = OpenAI(project=project_id)
        return self._client

    def combined(
        self,
        combined_request: CombinedRequest
    ) -> CombinedResponse:
        """Process the combined request."""
        request_id = combined_request.id
        action = combined_request.action

        timer = LoggingTimer('combined', logger=logger, level="INFO")

        element_id_similarity_tuple_list = self.find_nearest_elements(combined_request)
        timer.restart(f"Found {len(element_id_similarity_tuple_list)} results")

        element_results = self.get_element_results(
            combined_request.kind, element_id_similarity_tuple_list)
        timer.restart(f"got element results (len: {len(element_results)})")

        # TODO: remove, let the client handle this
        total_length = 0
        for element_result in element_results:
            total_length += len(element_result.text)
        timer.restart(f"total length: {total_length}")

        if combined_request.action == Action.RAG:
            prompt, answer = self.do_rag(combined_request.query, element_results)
        elif combined_request.action == Action.SEARCH:
            prompt, answer = "na", "na"
        else:
            raise ValueError(f"Invalid action: {combined_request.action}")
        timer.restart(f"did rag (prompt len: {len(prompt)}, answer len: {len(answer)})")

        total_elapsed = timer.total_time()
        timer.total(total_elapsed)

        combined_response = CombinedResponse(
            id=request_id,
            action=action,
            prompt=prompt,
            results=element_results,
            answer=answer,
            total_length=total_length
        )

        return combined_response

    def do_rag(self, query: str, element_results: List[ResultElement]) -> Tuple[str, str]:
        """
        Process a retrieval-augmented generation (RAG) request.

        This method constructs a prompt based on the provided query and the results
        retrieved from the document store. It then interacts with the OpenAI API to
        generate a response based on the prompt.

        Args:
            query (str): The user's query to be answered.
            element_results (List[ResultElement]): The results retrieved to assist
                in answering the query.

        Returns:
            Tuple[str, str]: A tuple containing the constructed prompt and the generated answer.
        """
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
            ]

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
        """
        Find the nearest elements to the query by using the KNearestFinder.
        """
        kind = combined_request.kind
        query = combined_request.query
        k = combined_request.k
        threshold = combined_request.threshold
        max_results = combined_request.max

        if kind is Kind.ARTICLE:
            element_id_similarity_tuple_list = self.finder.find_k_nearest_articles(
                query, k=k, threshold=threshold, max_results=max_results)
        elif kind is Kind.SEGMENT:
            element_id_similarity_tuple_list = self.finder.find_k_nearest_segments(
                query, k=k, threshold=threshold, max_results=max_results)
        else:
            raise ValueError(f"Invalid kind: {kind}")

        return element_id_similarity_tuple_list

    def get_element_results(
        self,
        kind: Kind,
        element_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:
        """
        Get the element results based on the kind.
        """
        if kind is Kind.ARTICLE:
            element_results = self.get_article_results(element_id_similarity_tuple_list)
        elif kind is Kind.SEGMENT:
            element_results = self.get_segment_results(element_id_similarity_tuple_list)
        else:
            raise ValueError(f"Invalid kind: {kind}")

        return element_results

    def get_article_results(
        self,
        article_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:
        """
        Get the article results.
        """
        results = []
        for article_id, similarity in article_id_similarity_tuple_list:
            article = self.stores.get_article(article_id)
            header_text = article.header.text
            caption_text = header_text
            article_text = article.text
            results.append(ResultElement(similarity, article, caption_text, article_text))
        return results

    def get_segment_results(
        self,
        segment_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ResultElement]:
        """
        Get the segment results.
        """
        results = []
        for segment_ind, similarity in segment_id_similarity_tuple_list:
            segment_record = self.stores.get_segment_record_by_index(segment_ind)
            segment_text = self.stores.get_segment_text(segment_record)
            document_index = segment_record.document_index
            article = self.stores.get_document_by_index(document_index)
            header_text = article.header.text
            caption_text = header_text
            results.append(ResultElement(similarity, segment_record, caption_text, segment_text))
        return results

    def get_elements_text(self, element_results: List[ResultElement]) -> str:
        """
        Get the elements text.
        """
        element_texts = []
        for i, (element_result) in enumerate(element_results):
            text = element_result.text
            element_texts.append(f"Context document {i}: {text[:15000]}")
        elements_text = "\n\n".join(element_texts)
        return elements_text

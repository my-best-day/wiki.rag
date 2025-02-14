import unittest
import logging
from unittest.mock import patch, MagicMock
from enum import Enum
import os
from dataclasses import dataclass
from search.services.combined_service import (
    Kind,
    Action,
    parse_enum,
    ResultElement,
    CombinedRequest,
    CombinedResponse,
    CombinedService
)
from ...xutils.byte_reader_tst import TestByteReader
from gen.element.flat.flat_article import FlatArticle
from gen.data.segment_record import SegmentRecord


class InvalidAction(Enum):
    INVALID = "invalid"


class InvalidKind(Enum):
    INVALID = "invalid"


# CombinedRequest verifies that action is an Action, so we need to create
# a new class that uses a different enum.
@dataclass
class InvalidCombinedRequest:
    """
    The request for the combined service.
    """
    id: str
    action: InvalidAction
    kind: InvalidKind
    query: str
    k: int
    threshold: float
    max: int


class TestCombinedService(unittest.TestCase):
    def setUp(self):
        self.segment_record_0 = SegmentRecord(
            segment_index=0,
            document_index=0,
            relative_segment_index=0,
            offset=0,
            length=13
        )
        self.segment_record_1 = SegmentRecord(
            segment_index=1,
            document_index=1,
            relative_segment_index=0,
            offset=13,
            length=15
        )
        self.result_element_0 = ResultElement(
            similarity=0.9,
            record=self.segment_record_0,
            caption="= header =\n",
            text="body of evidence\n"
        )
        self.result_element_1 = ResultElement(
            similarity=0.8,
            record=self.segment_record_1,
            caption="= header2 =\n",
            text="proof of evidence\n"
        )
        self.result_elements = [self.result_element_0, self.result_element_1]

        self.byte_reader = TestByteReader(
            b'= header =\nbody of evidence\n= header2 =\nproof of evidence\n'
        )
        self.flat_article0 = FlatArticle(0, 0, 11, 11, 17, self.byte_reader)
        self.flat_article1 = FlatArticle(1, 28, 12, 40, 18, self.byte_reader)
        self.flat_articles = [self.flat_article0, self.flat_article1]

        logging.disable(logging.CRITICAL)  # Disable all logging

    def tearDown(self):
        logging.disable(logging.NOTSET)  # Re-enable logging

    def test_kind_enum(self):
        self.assertEqual(Kind.ARTICLE.value, "article")
        self.assertEqual(Kind.SEGMENT.value, "segment")

    def test_action_enum(self):
        self.assertEqual(Action.SEARCH.value, "search")
        self.assertEqual(Action.RAG.value, "rag")

    def test_parse_enum(self):
        self.assertEqual(parse_enum(Kind, "article"), Kind.ARTICLE)
        self.assertEqual(parse_enum(Kind, "segment"), Kind.SEGMENT)
        self.assertEqual(parse_enum(Action, "search"), Action.SEARCH)
        self.assertEqual(parse_enum(Action, "rag"), Action.RAG)

    def test_parse_enum_invalid(self):
        with self.assertRaises(ValueError):
            parse_enum(Kind, "invalid")
        with self.assertRaises(ValueError):
            parse_enum(Action, "invalid")

    def test_result_element_class(self):
        segment_record = SegmentRecord(
            segment_index=0,
            document_index=0,
            relative_segment_index=0,
            offset=0,
            length=0
        )
        result_element = ResultElement(
            similarity=0.9,
            record=segment_record,
            caption="caption",
            text="text"
        )
        self.assertEqual(result_element.similarity, 0.9)
        self.assertEqual(result_element.record, segment_record)
        self.assertEqual(result_element.caption, "caption")
        self.assertEqual(result_element.text, "text")

    def test_combined_request_class(self):
        combined_request = CombinedRequest(
            id="123",
            action=Action.SEARCH,
            kind=Kind.ARTICLE,
            query="query",
            k=10,
            threshold=0.5,
            max=100
        )
        self.assertEqual(combined_request.id, "123")
        self.assertEqual(combined_request.action, Action.SEARCH)
        self.assertEqual(combined_request.kind, Kind.ARTICLE)
        self.assertEqual(combined_request.query, "query")
        self.assertEqual(combined_request.k, 10)
        self.assertEqual(combined_request.threshold, 0.5)
        self.assertEqual(combined_request.max, 100)

    def test_combined_request_str(self):
        combined_request = CombinedRequest(
            id="123",
            action=Action.SEARCH,
            kind=Kind.SEGMENT,
            query="query",
            k=10,
            threshold=0.5,
            max=100
        )

        self.assertEqual(
            str(combined_request),
            (
                "CombinedRequest(action=Action.SEARCH, kind=Kind.SEGMENT, "
                "query=query, k=10, threshold=0.5, max=100)"
            )
        )

    def test_combined_response_class(self):
        combined_response = CombinedResponse(
            id="123",
            action=Action.SEARCH,
            prompt="prompt",
            results=[],
            answer="answer",
            total_length=100
        )
        self.assertEqual(combined_response.id, "123")
        self.assertEqual(combined_response.action, Action.SEARCH)
        self.assertEqual(combined_response.prompt, "prompt")
        self.assertEqual(combined_response.results, [])
        self.assertEqual(combined_response.answer, "answer")
        self.assertEqual(combined_response.total_length, 100)

    def test_init(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        self.assertIsNotNone(combined_service)

    @patch.dict(os.environ, {"OPENAI_PROJECT_ID": "test_project_id"})
    @patch("search.services.combined_service.OpenAI")
    def test_get_openai_client(self, mock_openai):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        client = combined_service.get_openai_client()
        self.assertIsNotNone(client)
        mock_openai.assert_called_once_with(project="test_project_id")
        self.assertEqual(client, mock_openai.return_value)

    @patch.dict(os.environ, {}, clear={"OPENAI_PROJECT_ID"})
    @patch("search.services.combined_service.OpenAI")
    def test_get_openai_client_no_project_id(self, mock_openai):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        with self.assertRaises(ValueError):
            combined_service.get_openai_client()

    @patch.dict(os.environ, {"OPENAI_PROJECT_ID": "test_project_id"})
    @patch("search.services.combined_service.OpenAI")
    def test_get_openai_client_already_set(self, mock_openai):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        combined_service._client = MagicMock()
        client = combined_service.get_openai_client()
        self.assertEqual(client, combined_service._client)
        mock_openai.assert_not_called()

    def test_combined_search(self):
        # add function test_combined_search. create a mocked CombinedRequest, mock
        # find_nearest_element and have it return something like ((0, 0.7), (1, 0.6)).
        # mock get_element_results to return self.result_elements; then verify that
        # the result is as expected.
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        combined_service.find_nearest_elements = lambda req: [(0, 0.7), (1, 0.6)]
        combined_service.get_element_results = lambda kind, tuple_list: self.result_elements

        combined_request = CombinedRequest(
            id="test_id",
            action=Action.SEARCH,
            kind=Kind.ARTICLE,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )
        response = combined_service.combined(combined_request)

        expected_total_length = sum(len(el.text) for el in self.result_elements)

        self.assertEqual(response.id, "test_id")
        self.assertEqual(response.action, Action.SEARCH)
        self.assertEqual(response.prompt, "na")
        self.assertEqual(response.answer, "na")
        self.assertEqual(response.results, self.result_elements)
        self.assertEqual(response.total_length, expected_total_length)

    def test_combined_rag(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        combined_service.find_nearest_elements = lambda req: [(0, 0.7), (1, 0.6)]
        combined_service.get_element_results = lambda kind, tuple_list: self.result_elements
        combined_service.do_rag = lambda query, element_results: ("prompt", "answer")

        combined_request = CombinedRequest(
            id="test_id",
            action=Action.RAG,
            kind=Kind.SEGMENT,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )
        response = combined_service.combined(combined_request)

        expected_total_length = sum(len(el.text) for el in self.result_elements)

        self.assertEqual(response.id, "test_id")
        self.assertEqual(response.action, Action.RAG)
        self.assertEqual(response.prompt, "prompt")
        self.assertEqual(response.answer, "answer")
        self.assertEqual(response.results, self.result_elements)
        self.assertEqual(response.total_length, expected_total_length)

    def test_combined_invalid_action(self):
        """
        Test that an invalid action raises a ValueError.
        """

        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        combined_service.find_nearest_elements = lambda req: [(0, 0.7), (1, 0.6)]
        combined_service.get_element_results = lambda kind, tuple_list: self.result_elements
        combined_service.do_rag = lambda query, element_results: ("prompt", "answer")

        combined_request = InvalidCombinedRequest(
            id="test_id",
            action=InvalidAction.INVALID,
            kind=Kind.SEGMENT,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )
        with self.assertRaises(ValueError):
            combined_service.combined(combined_request)

    def test_do_rag(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        mock_openai = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "answer"
        mock_openai.chat.completions.create.return_value = mock_completion

        combined_service.find_nearest_elements = lambda req: [(0, 0.7), (1, 0.6)]
        combined_service.get_element_results = lambda kind, tuple_list: self.result_elements
        combined_service.get_openai_client = lambda: mock_openai

        query = "dummy query"
        prompt, answer = combined_service.do_rag(query, self.result_elements)
        self.assertTrue(prompt.startswith(f"question: {query}"))
        self.assertEqual(answer, "answer")

    def test_find_nearest_elements_article(self):
        finder = MagicMock()
        finder.find_k_nearest_articles.return_value = [(0, 0.7), (1, 0.6)]
        finder.find_k_nearest_segments.return_value = [(0, 0.7), (1, 0.6)]

        combined_request = CombinedRequest(
            id="test_id",
            action=Action.SEARCH,
            kind=Kind.ARTICLE,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )

        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=finder
        )

        result = combined_service.find_nearest_elements(combined_request)
        self.assertEqual(result, [(0, 0.7), (1, 0.6)])

    def test_find_nearest_elements_segment(self):
        finder = MagicMock()
        finder.find_k_nearest_articles.return_value = [(0, 0.7), (1, 0.6)]
        finder.find_k_nearest_segments.return_value = [(0, 0.7), (1, 0.6)]

        combined_request = CombinedRequest(
            id="test_id",
            action=Action.SEARCH,
            kind=Kind.SEGMENT,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )

        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=finder
        )

        result = combined_service.find_nearest_elements(combined_request)
        self.assertEqual(result, [(0, 0.7), (1, 0.6)])

    def test_find_nearest_elements_invalid_kind(self):
        finder = MagicMock()
        finder.find_k_nearest_articles.return_value = [(0, 0.7), (1, 0.6)]
        finder.find_k_nearest_segments.return_value = [(0, 0.7), (1, 0.6)]

        combined_request = InvalidCombinedRequest(
            id="test_id",
            action=Action.SEARCH,
            kind=InvalidKind.INVALID,
            query="dummy query",
            k=10,
            threshold=0.5,
            max=100
        )

        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=finder
        )

        with self.assertRaises(ValueError):
            combined_service.find_nearest_elements(combined_request)

    # def test_get_element_results_article(self):
    #     combined_service = CombinedService(
    #         stores=None,
    #         embed_config=None,
    #         finder=None
    #     )
    #     combined_service.get_article_results = lambda tuple_list: self.result_elements

    #     result = combined_service.get_element_results(Kind.ARTICLE, [(0, 0.7), (1, 0.6)])
    #     self.assertEqual(result, self.result_elements)

    def test_get_element_results_segment(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        combined_service.get_segment_results = lambda tuple_list: self.result_elements

        result = combined_service.get_element_results(Kind.SEGMENT, [(0, 0.7), (1, 0.6)])
        self.assertEqual(result, self.result_elements)

    def test_get_element_results_invalid_kind(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )

        with self.assertRaises(ValueError):
            combined_service.get_element_results(InvalidKind.INVALID, [(0, 0.7), (1, 0.6)])

    def test_get_segment_results(self):
        def get_segment_record_by_index(index):
            if index == 0:
                return self.segment_record_0
            elif index == 1:
                return self.segment_record_1
            else:
                raise ValueError(f"Invalid index: {index}")

        def get_segment_text(segment_record):
            index = segment_record.segment_index
            if index == 0:
                result_element = self.result_element_0
            elif index == 1:
                result_element = self.result_element_1
            else:
                raise ValueError(f"Invalid index: {index}")
            text = result_element.text
            return text

        def get_document_by_index(index):
            if index == 0:
                return self.flat_article0
            elif index == 1:
                return self.flat_article1
            else:
                raise ValueError(f"Invalid index: {index}")

        stores = MagicMock()
        stores.get_segment_record_by_index = get_segment_record_by_index
        stores.get_segment_text = get_segment_text
        stores.get_document_by_index = get_document_by_index

        combined_service = CombinedService(
            stores=stores,
            embed_config=None,
            finder=None
        )

        segment_id_similarity_tuple_list = [
            (0, self.result_element_0.similarity),
            (1, self.result_element_1.similarity)
        ]
        result = combined_service.get_segment_results(segment_id_similarity_tuple_list)
        self.assertEqual(result, self.result_elements)

    def test_get_elements_text(self):
        combined_service = CombinedService(
            stores=None,
            embed_config=None,
            finder=None
        )
        result = combined_service.get_elements_text(self.result_elements)
        expected_text = (
            "Context document 0: body of evidence\n\n\n"
            "Context document 1: proof of evidence\n"
        )
        self.assertEqual(result, expected_text)

    if __name__ == "__main__":
        unittest.main()

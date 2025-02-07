"""
A CLI interface to interact with the combined service.

Usage:
    python scripts/run/combined.py my query
"""
import re
import json
import httpx
import datetime
import logging

from xutils.app_config import CombinedConfig
from search.services.combined_service import Action, Kind
from web.combined_router import CombinedRequestModel
from xutils.load_config import get_app_config_and_query


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def lookup(config: CombinedConfig, query: str, action: Action) -> None:
    """
    Send the query to the combined service and print the results.
    """
    response = get_results(config, query, action)
    if query == ".":
        print(json.dumps(response, indent=4))

    print(">" * 100)
    print("\n\n\n")
    print_env(response)
    print_stats(response, query)
    print_answer(response)
    print_results(response)
    print("<" * 100)


def print_env(response: dict) -> None:
    print(f"env: {response['meta']['text_file']}, {response['meta']['max_len']}")


def print_stats(response: dict, query: str) -> None:
    received_str = response['meta']['received']
    completed_str = response['meta']['completed']
    received = datetime.datetime.fromisoformat(received_str)
    completed = datetime.datetime.fromisoformat(completed_str)
    duration = completed - received
    seconds = duration.total_seconds()
    result_count = len(response['data']['results'])
    in_tokens = len(response['data']['prompt']) / 4.5
    in_cents = in_tokens * (15 / 1e6)
    out_tokens = len(response['data']['answer']) / 4.5
    out_cents = out_tokens * (60 / 1e6)
    results_length = response['data']['total_length']
    result_tokens = results_length / 4.5
    result_cents = result_tokens * (15 / 1e6)
    parts = (
        f"Duration: {seconds:.3f}",
        f"{result_count} results",
        f"in: {in_tokens:.3f} tokens, {in_cents:.4f} cents",
        f"out: {out_tokens:.3f} tokens, {out_cents:.4f} cents",
        f"results: {results_length} chars, {result_tokens:.3f} tokens, {result_cents:.4f} cents",
    )
    text = " | ".join(parts)
    print(text)
    print(f"Query: {query}")


def print_answer(response: dict) -> None:
    print("Answer:")
    print(response['data']['answer'])


def print_results(response: dict) -> None:
    results = response['data']['results']
    for i, result in enumerate(results):
        print_result(i, result)


def print_result(i: int, result: dict) -> None:
    clean_caption = clean_header(result['caption'])
    print(f"{i}.Caption: {clean_caption}")
    parts = (
        f"Offset: {result['record'][3]}",
        f"Length: {result['record'][4]}",
        f"Similarity: {result['similarity']:.3f}",
    )
    text = " | ".join(parts)
    print(text)
    print(result['text'])
    print("\n\n")


def get_results(config: CombinedConfig, query: str, action: Action) -> list[str]:
    """
    Send the query to the combined service and return the results.
    """
    k = config.k
    threshold = config.threshold
    max_documents = config.max_documents

    request = CombinedRequestModel(
        id="12",
        action=action,
        kind=Kind.SEGMENT,
        query=query,
        k=k,
        threshold=threshold,
        max=max_documents,
    )

    hostname = config.run_config.hostname
    port = config.run_config.port
    url = f"http://{hostname}:{port}/api/combined"

    model_dump = request.model_dump()
    response = httpx.post(url, json=model_dump, timeout=45.0)
    app_response = response.json()
    return app_response


def main():
    logger = logging.getLogger(__name__)

    app_config, query, action = get_app_config_and_query(logger)
    run_config = app_config.run_config

    log_level = run_config.log_level
    log_level_upper = log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    logging.basicConfig(level=numeric_level)

    # grab again logger = logging.getLogger(__name__)

    lookup(app_config, query, action)


if __name__ == "__main__":
    main()

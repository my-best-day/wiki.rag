import os
import logging
import argparse
import configparser

from xutils.app_config import CombinedConfig, AppConfig, RunConfig, EmbeddingConfig
from search.services.combined_service import Action


def get_app_config_and_query(logger: logging.Logger) -> tuple[AppConfig, str, Action]:
    app_config, args = _get_app_config(logger, True)
    query = args.query
    action = args.action
    return app_config, query, action


def get_app_config(logger: logging.Logger) -> AppConfig:
    app_config, _ = _get_app_config(logger, False)
    return app_config


def _get_app_config(
    logger: logging.Logger,
    expect_query: bool
) -> tuple[AppConfig, argparse.Namespace]:
    """
    loads the config from a file, gets the command line arguments,
    and combine the two by having the command line arguments overriding
    the config file.
    """
    app_config = load_app_config(logger)
    args = parse_args(expect_query)

    # run config
    if args.hostname is not None:
        app_config.run_config.hostname = args.hostname

    if args.port is not None:
        app_config.run_config.port = args.port

    if args.log_level is not None:
        app_config.run_config.log_level = args.log_level

    # app config
    if args.k is not None:
        app_config.k = args.k

    if args.threshold is not None:
        app_config.threshold = args.threshold

    if args.max_documents is not None:
        app_config.max_documents = args.max_documents

    return app_config, args


def load_app_config(logger) -> AppConfig:
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.debug(f"Using config file: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    embed_config = load_embed_config(config)
    run_config = load_run_config(config)

    search_sec = config["SEARCH-APP"]
    text_file_path = search_sec.get("text-file-path")
    k = search_sec.getint("k")
    threshold = search_sec.getfloat("threshold")
    max_documents = search_sec.getint("max-documents")

    combined_config = CombinedConfig(
        text_file_path=text_file_path,
        k=k,
        threshold=threshold,
        max_documents=max_documents,
        embed_config=embed_config,
        run_config=run_config,
    )

    return combined_config


def load_embed_config(config: configparser.ConfigParser) -> EmbeddingConfig:
    embed_sec = config["SEARCH-APP.EMBEDDINGS"]
    prefix = embed_sec.get("prefix")
    max_len = embed_sec.getint("max-len")
    dim = embed_sec.getint("dim", None)
    stype = embed_sec.get("stype", "float32")
    norm_type = embed_sec.get("norm-type", None)
    l2_normalize = embed_sec.getboolean("l2-normalize", None)

    embed_config = EmbeddingConfig(
        prefix=prefix,
        max_len=max_len,
        dim=dim,
        stype=stype,
        norm_type=norm_type,
        l2_normalize=l2_normalize,
    )

    return embed_config


def load_run_config(config: configparser.ConfigParser) -> RunConfig:
    run_sec = config["SEARCH-APP.RUN"]
    hostname = run_sec.get("hostname")
    port = run_sec.getint("port")
    log_level = run_sec.get("log-level")

    run_config = RunConfig(
        hostname=hostname,
        port=port,
        log_level=log_level,
    )

    return run_config


def parse_args(expect_query: bool) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    parser.add_argument("-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--max-documents", type=int, default=None)
    parser.add_argument("--action", type=str, default=None)
    parser.add_argument('query_parts', nargs=argparse.REMAINDER, help='Search query')
    args = parser.parse_args()

    if expect_query and not args.query_parts:
        parser.error("No query provided")

    query = " ".join(args.query_parts)

    if query.endswith(":search"):
        args.action = Action.SEARCH
        query = query[:-len(":search")]
    elif query.endswith(":rag"):
        args.action = Action.RAG
        query = query[:-len(":rag")]

    if args.action is None:
        args.action = Action.SEARCH

    args.query = query

    return args

#

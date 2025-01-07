import os
import uvicorn
import logging
import argparse
import configparser

from xutils.app_config import AppConfig
from xutils.embedding_config import EmbeddingConfig


def get_search_app(logger):
    from web.search_app import create_search_app
    app_config = load_app_config(logger)
    search_app = create_search_app(app_config)
    return search_app


def get_rag_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.rag_app import create_rag_app
    app_config = load_app_config(logger)
    rag_app = create_rag_app(app_config)
    return rag_app


def get_combined_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.combined_app import create_combined_app
    app_config = load_app_config(logger)
    combined_app = create_combined_app(app_config)
    return combined_app


def load_app_config(logger) -> AppConfig:
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.debug(f"Using config file: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

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

    search_sec = config["SEARCH-APP"]
    text_file_path = search_sec.get("text-file-path")
    app_config = AppConfig(
        text_file_path=text_file_path,
        embed_config=embed_config,
    )

    logger.info(f"AppConfig: {app_config}")

    return app_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    args, _ = parser.parse_known_args()

    log_level_upper = args.log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    logging.basicConfig(level=numeric_level)

    logger = logging.getLogger(__name__)

    if args.app is None:
        parser.error("Please provide --app")

    app_arg = args.app.upper()
    if app_arg == "SEARCH":
        app = get_search_app(logger)
    elif app_arg == "RAG":
        app = get_rag_app(logger)
    elif app_arg == "COMBINED":
        app = get_combined_app(logger)
    else:
        parser.error(f"Unknown app: {app_arg}")

    host = "127.0.0.1"
    port = args.port
    log_level = numeric_level
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )


if __name__ == "__main__":
    main()

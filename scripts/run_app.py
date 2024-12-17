import os
import uvicorn
import logging
import argparse
import configparser
from xutils.app_config import AppConfig
from xutils.embedding_config import EmbeddingConfig
from web.search_app import create_search_app
from web.rag_app import create_rag_app


# Create a logger for your module
logger = logging.getLogger(__name__)


def get_search_app():
    setup()
    app_config = load_app_config()
    search_app = create_search_app(app_config)
    return search_app


def get_rag_app():
    setup()
    app_config = load_app_config()
    rag_app = create_rag_app(app_config)
    return rag_app


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", type=str)
    args, _ = parser.parse_known_args()

    if args.log_level is not None:
        setup_logging(args.log_level)


def setup_logging(log_level: str = "INFO"):
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Set up root logger for global config
    logging.basicConfig(level=numeric_level)


def load_app_config() -> AppConfig:
    # if there is an env variable CONFIG_FILE, use it
    # otherwise, use the default config file
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.info(f"Using config file: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    # tell us your CWD:
    embed_sec = config["SEARCH-APP.EMBEDDINGS"]
    embed_config = EmbeddingConfig(
        prefix=embed_sec.get("prefix"),
        max_len=embed_sec.getint("max-len"),
        dim=embed_sec.getint("dim", None),
        stype=embed_sec.get("stype", "float32"),
        norm_type=embed_sec.get("norm-type", None),
        l2_normalize=embed_sec.getboolean("l2-normalize", None),
    )
    search_sec = config["SEARCH-APP"]
    app_config = AppConfig(
        text_file_path=search_sec.get("text-file-path"),
        embed_config=embed_config,
    )

    logger.info(f"AppConfig: {app_config}")

    return app_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    args, _ = parser.parse_known_args()

    if args.app is None:
        parser.error("Please provide --app")

    app_arg = args.app.upper()
    if app_arg == "SEARCH":
        app = get_search_app()
    elif app_arg == "RAG":
        app = get_rag_app()
    else:
        parser.error(f"Unknown app: {app_arg}")

    uvicorn.run(app, host="127.0.0.1", port=args.port)  # , reload=True


if __name__ == "__main__":
    main()

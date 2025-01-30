import os
import uvicorn
import logging
import argparse

from xutils.app_config import AppConfig, load_app_config


def get_search_app(logger):
    from web.search_app import create_search_app
    app_config = get_app_config(logger)
    search_app = create_search_app(app_config)
    return search_app


def get_rag_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.rag_app import create_rag_app
    app_config = get_app_config(logger)
    rag_app = create_rag_app(app_config)
    return rag_app


def get_combined_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.combined_app import create_combined_app
    app_config = get_app_config(logger)
    combined_app = create_combined_app(app_config)
    return combined_app


def get_app_config(logger) -> AppConfig:
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.debug(f"Using config file: {config_file}")

    app_config = load_app_config(config_file)
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

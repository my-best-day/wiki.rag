import os
import uvicorn
import logging
import argparse

from xutils.app_config import AppConfig, load_app_config as _load_app_config


def get_combined_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.combined_app import create_combined_app
    app_config = get_app_config(logger)

    combined_app = create_combined_app(app_config)
    return combined_app


def load_app_config(logger) -> AppConfig:
    config_file = "config.ini"
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    logger.debug(f"Using config file: {config_file}")

    app_config = _load_app_config(config_file)
    logger.info(f"AppConfig: {app_config}")

    return app_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    parser.add_argument("-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--max-documents", type=int, default=None)
    args, _ = parser.parse_known_args()
    return args


def get_app_config(logger) -> AppConfig:
    app_config = load_app_config(logger)
    args = parse_args()

    # run config
    if args.log_level is not None:
        app_config.run_config.log_level = args.log_level

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

    return app_config


def main():
    logger = logging.getLogger(__name__)

    app_config = get_app_config(logger)
    run_config = app_config.run_config

    log_level = run_config.log_level
    log_level_upper = log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    logging.basicConfig(level=numeric_level)

    logger = logging.getLogger(__name__)

    app = get_combined_app(logger)

    host = run_config.hostname
    port = run_config.port
    log_level = numeric_level
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )


if __name__ == "__main__":
    main()

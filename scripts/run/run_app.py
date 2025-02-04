import os
import uvicorn
import logging

from xutils.load_config import get_app_config


def get_combined_app(logger):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")

    from web.combined_app import create_combined_app
    app_config = get_app_config(logger)

    combined_app = create_combined_app(app_config)
    return combined_app


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

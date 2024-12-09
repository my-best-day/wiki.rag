import os
import logging
import uvicorn
import configparser
from web.app_config import AppConfig
from web.search_app import create_search_app


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # Set the default logging level
    )
    # Optional: Adjust specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)  # Control uvicorn logs
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # Access logs


def load_app_config(config_file: str = "config.ini") -> AppConfig:
    config = configparser.ConfigParser()
    config.read(config_file)

    # tell us your CWD:
    print(f"*** **** ***** CWD: {os.getcwd()}")
    sec = config["SEARCH-APP"]
    app_config = AppConfig(
        text_file_path=sec.get("text-file-path"),
        path_prefix=sec.get("path-prefix"),
        max_len=sec.getint("max-len")
    )
    return app_config


def get_search_app() -> uvicorn.Server:
    app_config = load_app_config()
    search_app = create_search_app(app_config)
    return search_app


def main():
    search_app = create_search_app()
    uvicorn.run(search_app, host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    setup_logging()
    main()

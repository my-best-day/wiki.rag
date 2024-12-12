import os
import logging
import uvicorn
import configparser
from xutils.app_config import AppConfig
from web.search_app import create_search_app
from web.rag_app import create_rag_app


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
        max_len=sec.getint("max-len"),
        target_dim=sec.getint("target-dim"),
        l2_normalize=sec.getboolean("l2-normalize"),
    )
    return app_config


def get_search_app() -> uvicorn.Server:
    app_config = load_app_config()
    search_app = create_search_app(app_config)
    return search_app


def get_rag_app() -> uvicorn.Server:
    app_config = load_app_config()
    rag_app = create_rag_app(app_config)
    return rag_app


# def main():
#     app = create_rag_app()
#     uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)


# if __name__ == "__main__":
#     setup_logging()
#     main()

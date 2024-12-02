import logging
import uvicorn


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # Set the default logging level
        # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Optional: Adjust specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)  # Control uvicorn logs
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # Access logs


def main():
    setup_logging()
    # Replace "src.web.app:app" with your actual app import path
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()

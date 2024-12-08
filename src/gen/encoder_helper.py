import os
import time
import logging
import threading

logger = logging.getLogger(__name__)


def background_load():
    logging.basicConfig(level=logging.INFO)
    try:
        t0 = time.time()
        from sentence_transformers import SentenceTransformer  # noqa
        logger.info("Loaded sentence transformer in the background. (%.3f secs)", time.time() - t0)
    except Exception as e:
        # Log the exception or handle it as needed
        logger.warning(f"*** *** *** *** *** Background load failed: {e}")


if not os.getenv("UNIT_TESTING"):
    load_thread = threading.Thread(target=background_load, daemon=True)
    load_thread.start()

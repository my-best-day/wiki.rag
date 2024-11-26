import os
import threading


def background_load():
    try:
        from sentence_transformers import SentenceTransformer  # noqa
        # Perform any additional operations if needed
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"*** *** *** *** *** Background load failed: {e}")


if not os.getenv("UNIT_TESTING"):
    load_thread = threading.Thread(target=background_load, daemon=True)
    load_thread.start()

import logging
import threading
import torch

from xutils.utils import Utils
from xutils.timer import LoggingTimer

logger = logging.getLogger(__name__)

if Utils.is_env_var_truthy("UNIT_TESTING"):
    def background_load():
        """
        Load the SentenceTransformer model in the background.
        This function runs in a separate thread and initializes the model for later use.
        """
        logger.debug("Starting background load")
        timer = LoggingTimer('background_load', logger=logger, level="DEBUG")
        try:
            from sentence_transformers import SentenceTransformer
            timer.restart("Loaded sentence transformer package")

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_id = "nomic-ai/nomic-embed-text-v1.5"
            model = SentenceTransformer(
                model_name_or_path=model_id,
                device=device,
                trust_remote_code=True,
            )
            timer.restart("Loaded model")

            model.encode(["Hello, world!"], batch_size=1)
            timer.restart("Encoded test string")

        except Exception as e:
            logger.warning(f"Load failed: {e}")

        timer.total("Background load complete")

    load_thread = threading.Thread(target=background_load, daemon=True)
    load_thread.start()

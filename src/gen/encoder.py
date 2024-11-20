import torch
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CONFIG_1 = {"id": "nomic-ai/nomic-embed-text-v1.5", "max_len": 8192, "default": True}
CONFIG_2 = {"id": "all-MiniLM-L6-v2", "max_len": 256}
CONFIG = CONFIG_2


class Encoder:
    def __init__(self, batch_size):
        self.batch_size = batch_size
        self.model, self.max_len = self.get_model()

    def encode(self, sentences):
        return self.model.encode(sentences, batch_size=self.batch_size)

    @staticmethod
    def get_model():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("*** device: %s", device)

        if not getattr(CONFIG, "default", False):
            logger.warning("*** *** *** Using non-default encoder: %s *** *** ***", CONFIG["id"])

        embedding_model_id = CONFIG["id"]
        max_len = CONFIG["max_len"]

        embedding_model = SentenceTransformer(
            model_name_or_path=embedding_model_id,
            device=device,
            trust_remote_code=True,
        )
        return embedding_model, max_len

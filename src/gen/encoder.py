import torch
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

encoder_configs = {
    # max-token * raw2cln * tok2char * char2byte -> max-byte
    # 8192 tokens -> 256 * 1.05 * 3.9 * 1.05 ~> 35223
    "big": {"model_id": "nomic-ai/nomic-embed-text-v1.5", "max_len": 8192},

    # max-token * raw2cln * tok2char * char2byte -> max-byte
    # 256 tokens -> 256 * 1.05 * 3.9 * 1.05 -> 1100
    "small": {"model_id": "all-MiniLM-L6-v2", "max_len": 256}
}


class Encoder:
    def __init__(self, batch_size: int, config_id: str = "small"):
        self.config = encoder_configs[config_id]
        self.batch_size = batch_size
        self._model = None

    def encode(self, sentences):
        return self.model.encode(sentences, batch_size=self.batch_size)

    @property
    def model(self):
        if self._model is None:
            self._model = self.get_model()
        return self._model

    def get_model(self):
        device = self.get_device()
        model_id = self.config["model_id"]

        model = self._get_model(model_id, device)

        return model

    def _get_model(self, model_id, device):
        model = SentenceTransformer(
            model_name_or_path=model_id,
            device=device,
            trust_remote_code=True,
        )
        return model

    @staticmethod
    def get_device():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return device

from dataclasses import dataclass
from typing import Optional
from xutils.embedding_config import EmbeddingConfig


@dataclass
class AppConfig:
    text_file_path: str
    embed_config: Optional[EmbeddingConfig]

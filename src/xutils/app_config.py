from typing import Optional
from dataclasses import dataclass
from enum import Enum
from xutils.embedding_config import EmbeddingConfig


class Domain(Enum):
    WIKI = "wiki"
    PLOTS = "plots"


@dataclass
class AppConfig:
    domain: Domain
    text_file_path: str
    embed_config: Optional[EmbeddingConfig]


@dataclass
class RunConfig:
    hostname: str
    port: int
    log_level: str


@dataclass
class CombinedConfig(AppConfig):
    k: int
    threshold: float
    max_documents: int

    run_config: RunConfig

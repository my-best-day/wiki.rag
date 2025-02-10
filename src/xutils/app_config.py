"""
Application configuration.
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum
from xutils.embedding_config import EmbeddingConfig


class Domain(Enum):
    """
    The domain of the application.
    """
    WIKI = "wiki"
    PLOTS = "plots"


@dataclass
class AppConfig:
    """
    The application configuration.
    """
    domain: Domain
    text_file_path: str
    embed_config: Optional[EmbeddingConfig]


@dataclass
class RunConfig:
    """
    The run configuration.
    """
    hostname: str
    port: int
    log_level: str


@dataclass
class CombinedConfig(AppConfig):
    """
    The combined configuration: app config + run config +
    nearest-k parameters
    """
    k: int
    threshold: float
    max_documents: int

    run_config: RunConfig

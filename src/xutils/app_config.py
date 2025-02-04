import configparser
from typing import Optional
from dataclasses import dataclass

from xutils.embedding_config import EmbeddingConfig


@dataclass
class AppConfig:
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


def load_app_config(config_file) -> AppConfig:
    config = configparser.ConfigParser()
    config.read(config_file)

    embed_config = load_embed_config(config)
    run_config = load_run_config(config)

    search_sec = config["SEARCH-APP"]
    text_file_path = search_sec.get("text-file-path")
    k = search_sec.getint("k")
    threshold = search_sec.getfloat("threshold")
    max_documents = search_sec.getint("max-documents")

    combined_config = CombinedConfig(
        text_file_path=text_file_path,
        k=k,
        threshold=threshold,
        max_documents=max_documents,
        embed_config=embed_config,
        run_config=run_config,
    )

    return combined_config


def load_embed_config(config: configparser.ConfigParser) -> EmbeddingConfig:
    embed_sec = config["SEARCH-APP.EMBEDDINGS"]
    prefix = embed_sec.get("prefix")
    max_len = embed_sec.getint("max-len")
    dim = embed_sec.getint("dim", None)
    stype = embed_sec.get("stype", "float32")
    norm_type = embed_sec.get("norm-type", None)
    l2_normalize = embed_sec.getboolean("l2-normalize", None)

    embed_config = EmbeddingConfig(
        prefix=prefix,
        max_len=max_len,
        dim=dim,
        stype=stype,
        norm_type=norm_type,
        l2_normalize=l2_normalize,
    )

    return embed_config


def load_run_config(config: configparser.ConfigParser) -> RunConfig:
    run_sec = config["SEARCH-APP.RUN"]
    hostname = run_sec.get("hostname")
    port = run_sec.getint("port")
    log_level = run_sec.get("log-level")

    run_config = RunConfig(
        hostname=hostname,
        port=port,
        log_level=log_level,
    )

    return run_config

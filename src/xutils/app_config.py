import configparser
from typing import Optional
from dataclasses import dataclass

from xutils.embedding_config import EmbeddingConfig


@dataclass
class AppConfig:
    text_file_path: str
    embed_config: Optional[EmbeddingConfig]


def load_app_config(config_file) -> AppConfig:
    config = configparser.ConfigParser()
    config.read(config_file)

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

    search_sec = config["SEARCH-APP"]
    text_file_path = search_sec.get("text-file-path")
    app_config = AppConfig(
        text_file_path=text_file_path,
        embed_config=embed_config,
    )

    return app_config

from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    prefix: str
    max_len: int
    dim: Optional[int] = None
    stype: str = "float32"
    norm_type: Optional[str] = None

    l2_normalize: Optional[bool] = None

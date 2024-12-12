from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    text_file_path: str
    path_prefix: str
    max_len: int
    target_dim: Optional[int] = None
    l2_normalize: bool = True

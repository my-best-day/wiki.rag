from dataclasses import dataclass


@dataclass
class AppConfig:
    text_file_path: str
    path_prefix: str
    max_len: int

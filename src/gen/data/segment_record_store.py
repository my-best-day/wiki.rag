import logging
import pandas as pd
from typing import List
from pathlib import Path

from xutils.embedding_config import EmbeddingConfig
from gen.data.segment_record import SegmentRecord

logger = logging.getLogger(__name__)


class SegmentRecordStore:

    @classmethod
    def from_embed_config(cls, embed_config: EmbeddingConfig):
        return cls(embed_config.prefix, embed_config.max_len)

    def __init__(self, path_prefix: str, max_len: int):
        self.path_prefix = path_prefix
        self.max_len = max_len

    def load_segment_records(self) -> List[SegmentRecord]:
        segment_records_path = self.get_segment_record_store_path()
        segment_records = self.load_segment_records_from_path(segment_records_path)
        return segment_records

    def load_segment_records_from_path(self, segment_records_path: Path) -> List[SegmentRecord]:
        segment_record_df = self.read_segment_record_df(segment_records_path)
        segment_records = list(segment_record_df.itertuples(index=False, name="SegmentRecord"))
        return segment_records

    @staticmethod
    def read_segment_record_df(path_or_buffer) -> List[SegmentRecord]:
        segment_df = pd.read_csv(path_or_buffer, index_col=False)
        return segment_df

    def save_segment_records(self, segment_records: List[SegmentRecord]) -> None:
        segment_records_path = self.get_segment_record_store_path()
        segment_record_df = pd.DataFrame(
            segment_records,
            columns=SegmentRecord._fields
        )
        self.write_segment_records(segment_records_path, segment_record_df)

    @staticmethod
    def write_segment_records(path_or_buffer, segment_record_df: pd.DataFrame) -> None:
        segment_record_df.to_csv(path_or_buffer, index=False)

    def get_segment_record_store_path(self) -> Path:
        path_prefix = self.path_prefix
        max_len = self.max_len
        segment_records_path_str = f"{path_prefix}_{max_len}_segment_records.csv"
        segment_records_path = Path(segment_records_path_str)
        return segment_records_path

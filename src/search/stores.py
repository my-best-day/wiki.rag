import logging
from uuid import UUID
from pathlib import Path
from numpy.typing import NDArray
from threading import RLock, Thread
from typing import List, Tuple, Optional


from xutils.utils import Utils
from xutils.timer import LoggingTimer
from gen.embedding_store import EmbeddingStore, StoreMode
from xutils.byte_reader import ByteReader
from xutils.embedding_config import EmbeddingConfig
from gen.element.flat.flat_article import FlatArticle
from gen.data.segment_record import SegmentRecord
from gen.data.segment_record_store import SegmentRecordStore
from gen.element.flat.flat_article_store import FlatArticleStore

logger = logging.getLogger(__name__)


class Stores:

    @classmethod
    def create_stores(
        cls,
        text_file_path: Path,
        embed_config: EmbeddingConfig
    ) -> 'Stores':
        text_byte_reader = ByteReader(text_file_path)

        path_prefix = embed_config.prefix
        flat_article_store = FlatArticleStore(path_prefix, text_byte_reader)

        segment_record_store = SegmentRecordStore.from_embed_config(embed_config)

        embedding_store_path_str = EmbeddingStore.get_store_path(embed_config)
        embedding_store_path = Path(embedding_store_path_str)
        embedding_store = EmbeddingStore(
            path=embedding_store_path,
            mode=StoreMode.READ,
            allow_empty=False
        )

        stores = cls(
            text_byte_reader,
            flat_article_store,
            segment_record_store,
            embedding_store,
        )
        return stores

    def __init__(
        self,
        text_byte_reader: ByteReader,
        flat_article_store: FlatArticleStore,
        segment_record_store: SegmentRecordStore,
        embedding_store: EmbeddingStore
    ) -> None:

        self.text_byte_reader = text_byte_reader
        self.flat_article_store = flat_article_store
        self.segment_record_store = segment_record_store
        self.embedding_store = embedding_store

        self._lock = RLock()
        self._articles: Optional[List[FlatArticle]] = None
        self._segment_records: Optional[List[SegmentRecord]] = None
        self._uids_and_embeddings: Optional[Tuple[List[UUID], NDArray]] = None

    def background_load(self):
        if Utils.is_env_var_truthy("UNIT_TESTING"):
            return

        def load():
            logger.info("background_load starts")
            with self._lock:
                timer = LoggingTimer('background_load', logger=logger, level="DEBUG")
                # non-flat articles are loaded along with the segments
                self._load_flat_articles()
                timer.restart("flat articles loaded")

                self._load_segment_records()
                timer.restart("segment records loaded")

                self._load_uids_and_embeddings()
                timer.restart("embeddings loaded")

            logger.info("background_load done")

        thread = Thread(target=load, daemon=True)
        thread.start()

    def get_segment_text(self, segment_record: SegmentRecord) -> str:
        _bytes = self.text_byte_reader.read_bytes(
            segment_record.offset,
            segment_record.length)
        text = _bytes.decode("utf-8")
        return text

    def get_article_by_index(self, article_index: int) -> FlatArticle:
        articles = self.articles
        article = articles[article_index]
        return article

    def get_segment_record_by_index(self, segment_index: int) -> SegmentRecord:
        segment_records = self.segment_records
        segment_record = segment_records[segment_index]
        return segment_record

    def get_embeddings_article_indexes(self) -> List[int]:
        segment_records = self.segment_records
        article_indexes = [record.document_index for record in segment_records]
        return article_indexes

    @property
    def articles(self) -> List[FlatArticle]:
        if self._articles is None:
            with self._lock:
                if self._articles is None:
                    self._load_flat_articles()
        return self._articles

    @property
    def segment_records(self) -> List[SegmentRecord]:
        if self._segment_records is None:
            with self._lock:
                if self._segment_records is None:
                    self._load_segment_records()
        return self._segment_records

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        if self._uids_and_embeddings is None:
            with self._lock:
                if self._uids_and_embeddings is None:
                    self._load_uids_and_embeddings()
        return self._uids_and_embeddings

    def _load_flat_articles(self) -> None:
        flat_article_store = self.flat_article_store
        flat_articles = flat_article_store.load_flat_articles()
        self._articles = flat_articles

    def _load_segment_records(self) -> None:
        """reads segment records from a csv file"""
        segment_record_store = self.segment_record_store
        segment_records = segment_record_store.load_segment_records()
        self._segment_records = segment_records

    def _load_uids_and_embeddings(self) -> None:
        embedding_store = self.embedding_store
        uids_and_embeddings = embedding_store.load_embeddings()
        self._uids_and_embeddings = uids_and_embeddings

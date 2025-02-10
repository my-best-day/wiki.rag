"""
A collection of stores for a search.
"""
import logging
from uuid import UUID
from threading import RLock, Thread
from typing import List, Tuple, Optional
from numpy.typing import NDArray


from xutils.utils import Utils
from xutils.timer import LoggingTimer
from xutils.byte_reader import ByteReader
from gen.data.segment_record import SegmentRecord
from gen.data.segment_record_store import SegmentRecordStore
from gen.data.document import Document
from gen.data.document_store import DocumentStore
from gen.embedding_store import EmbeddingStore
logger = logging.getLogger(__name__)


class Stores:
    """
    A collection of stores for a search.
    """

    def __init__(
        self,
        text_byte_reader: ByteReader,
        document_store: DocumentStore,
        segment_record_store: SegmentRecordStore,
        embedding_store: EmbeddingStore
    ) -> None:
        """
        Initialize the stores.
        Args:
            text_byte_reader: A byte reader for the text, used in conjunction with the
                segment records to get segment text.
            document_store: A store for the documents (articles, plots, etc.)
            segment_record_store: A store for the segment records.
            embedding_store: A store for the embeddings.
        """
        self.text_byte_reader = text_byte_reader
        self.document_store = document_store
        self.segment_record_store = segment_record_store
        self.embedding_store = embedding_store

        self._lock = RLock()

        # lazy loaded
        self._documents: Optional[List[Document]] = None
        self._segment_records: Optional[List[SegmentRecord]] = None
        self._uids_and_embeddings: Optional[Tuple[List[UUID], NDArray]] = None

    def background_load(self):
        """
        Pre-load the documents, segment records, and embeddings in the background.
        """
        if Utils.is_env_var_truthy("UNIT_TESTING"):
            return

        def load():
            logger.info("background_load starts")
            with self._lock:
                timer = LoggingTimer('background_load', logger=logger, level="DEBUG")
                self._load_documents()
                timer.restart("documents loaded")

                self._load_segment_records()
                timer.restart("segment records loaded")

                self._load_uids_and_embeddings()
                timer.restart("embeddings loaded")

            logger.info("background_load done")

        thread = Thread(target=load, daemon=True)
        thread.start()

    def get_segment_text(self, segment_record: SegmentRecord) -> str:
        """Get the text of a segment."""
        _bytes = self.text_byte_reader.read_bytes(
            segment_record.offset,
            segment_record.length)
        text = _bytes.decode("utf-8")
        return text

    def get_document_by_index(self, document_index: int) -> Document:
        """Get a document by index."""
        documents = self.documents
        document = documents[document_index]
        return document

    def get_segment_record_by_index(self, segment_index: int) -> SegmentRecord:
        """Get a segment record by index."""
        segment_records = self.segment_records
        segment_record = segment_records[segment_index]
        return segment_record

    def get_embeddings_article_indexes(self) -> List[int]:
        """Get the article indexes of the embeddings."""
        segment_records = self.segment_records
        document_indexes = [record.document_index for record in segment_records]
        return document_indexes

    @property
    def documents(self) -> List[Document]:
        """Get the documents."""
        if self._documents is None:
            with self._lock:
                if self._documents is None:
                    self._load_documents()
        return self._documents

    @property
    def segment_records(self) -> List[SegmentRecord]:
        """Get the segment records."""
        if self._segment_records is None:
            with self._lock:
                if self._segment_records is None:
                    self._load_segment_records()
        return self._segment_records

    @property
    def uids_and_embeddings(self) -> Tuple[List[UUID], NDArray]:
        """Get the uids and embeddings."""
        if self._uids_and_embeddings is None:
            with self._lock:
                if self._uids_and_embeddings is None:
                    self._load_uids_and_embeddings()
        return self._uids_and_embeddings

    def _load_documents(self) -> None:
        """Load the documents."""
        document_store = self.document_store
        documents = document_store.load_documents()
        self._documents = documents

    def _load_segment_records(self) -> None:
        """Load the segment records from a csv file."""
        segment_record_store = self.segment_record_store
        segment_records = segment_record_store.load_segment_records()
        self._segment_records = segment_records

    def _load_uids_and_embeddings(self) -> None:
        """Load the uids and embeddings."""
        embedding_store = self.embedding_store
        uids_and_embeddings = embedding_store.load_embeddings()
        self._uids_and_embeddings = uids_and_embeddings

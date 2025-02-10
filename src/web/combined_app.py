"""
Creates the Combined (Search + RAG) FastAPI app.
Creates a CombinedService and CombinedRouter.
CombinedService provides the core logic for the combined search and RAG service.
CombinedRouter provides the routes for the combined search and RAG service.
"""
import re
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from xutils.app_config import AppConfig
from xutils.byte_reader import ByteReader
from xutils.app_config import Domain
from search.stores import Stores
from search.k_nearest_finder import KNearestFinder
from search.services.combined_service import CombinedService
from search.stores import DocumentStore
from web.combined_router import create_combined_router
from gen.embedding_store import EmbeddingStore, StoreMode
from gen.element.flat.flat_article_store import FlatArticleStore
from gen.data.plot_store import PlotStore
from gen.data.segment_record_store import SegmentRecordStore

logger = logging.getLogger(__name__)


def clean_header(text):
    """attempt to make article headers more readable and one line"""
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_app(app_config: AppConfig) -> FastAPI:
    """Creates the FastAPI app for the combined search and RAG service."""

    app = FastAPI()

    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    embed_config = app_config.embed_config

    text_byte_reader = ByteReader(app_config.text_file_path)
    path_prefix = embed_config.prefix

    document_store = create_document_store(app_config, text_byte_reader)
    embedding_store = EmbeddingStore(
        embedding_config=embed_config,
        mode=StoreMode.READ,
        allow_empty=False
    )

    max_len = embed_config.max_len
    segment_record_store = SegmentRecordStore(path_prefix, max_len)

    stores = Stores(text_byte_reader, document_store, segment_record_store, embedding_store)
    stores.background_load()

    finder = KNearestFinder(stores, embed_config)
    service = CombinedService(stores, embed_config, finder)

    combined_router = create_combined_router(app_config, service)
    app.include_router(combined_router)

    return app


def create_document_store(app_config: AppConfig, text_byte_reader: ByteReader) -> DocumentStore:
    """Creates the document store for the target domain."""
    path_prefix = app_config.embed_config.prefix
    domain = app_config.domain
    if domain == Domain.WIKI:
        document_store = FlatArticleStore(path_prefix, text_byte_reader)
    elif domain == Domain.PLOTS:
        plots_dir = Path(path_prefix).parent
        document_store = PlotStore(plots_dir)
    else:
        raise ValueError(f"Invalid domain: {domain}")

    return document_store

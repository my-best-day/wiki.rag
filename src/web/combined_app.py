import re
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from search.stores import Stores
from xutils.app_config import AppConfig
from xutils.byte_reader import ByteReader
from search.k_nearest_finder import KNearestFinder
from web.combined_router import create_combined_router
from gen.embedding_store import EmbeddingStore, StoreMode
from search.services.combined_service import CombinedService
from gen.element.flat.flat_article_store import FlatArticleStore
from gen.data.plot_store import PlotStore
from gen.data.segment_record_store import SegmentRecordStore
from xutils.app_config import Domain

logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_app(app_config: AppConfig) -> FastAPI:
    app = FastAPI()

    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    embed_config = app_config.embed_config
    text_file_path = app_config.text_file_path

    text_byte_reader = ByteReader(text_file_path)
    path_prefix = embed_config.prefix
    domain = app_config.domain
    if domain == Domain.WIKI:
        document_store = FlatArticleStore(path_prefix, text_byte_reader)
    elif domain == Domain.PLOTS:
        plots_dir = Path(path_prefix).parent
        document_store = PlotStore(plots_dir)
    else:
        raise ValueError(f"Invalid domain: {domain}")

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

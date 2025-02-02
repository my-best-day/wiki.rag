import re
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from xutils.app_config import AppConfig
from search.k_nearest_finder import KNearestFinder
from search.stores import Stores
from web.combined_router import create_combined_router
from search.services.combined_service import CombinedService

logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_app(app_config: AppConfig) -> FastAPI:
    app = FastAPI()

    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    embed_config = app_config.embed_config
    text_file_path = app_config.text_file_path
    stores = Stores.create_stores(text_file_path, embed_config)
    stores.background_load()

    finder = KNearestFinder(stores, embed_config)
    service = CombinedService(stores, embed_config, finder)

    combined_router = create_combined_router(app_config, service)
    app.include_router(combined_router)

    return app

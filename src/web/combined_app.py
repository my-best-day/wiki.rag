import re
import os
import logging
import datetime

from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from xutils.app_config import AppConfig
from gen.search.stores_flat import StoresFlat as Stores
from gen.search.k_nearest_finder import KNearestFinder

from .services.combined_service import CombinedService, CombinedRequest, Kind

logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_app(app_config: AppConfig) -> FastAPI:
    app = FastAPI()

    templates = Jinja2Templates(directory="web-ui/templates")
    templates.env.filters['clean_header'] = clean_header
    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    embed_config = app_config.embed_config
    stores = Stores(app_config.text_file_path, embed_config)
    stores.background_load()
    finder = KNearestFinder(stores, embed_config)

    app.state.config = app_config
    app.state.templates = templates
    app.state.stores = stores
    app.state.finder = finder

    service = CombinedService(app.state)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        template_vars = {
            "request": request,
            "Kind": Kind
        }
        return templates.TemplateResponse("combined.html", template_vars)

    @app.get("/combined", response_class=HTMLResponse)
    async def combined_get(request: Request):
        return await index(request)

    @app.post("/combined", response_class=HTMLResponse)
    async def combined(
        request: Request,
        action: str = Form(...),
        query: str = Form(...), k: int = Form(5),
        threshold: float = Form(0.3),
        max: int = Form(10),
        kind: str = Form(...),
    ) -> HTMLResponse:

        received = datetime.datetime.now()

        logger.info(f"Received query: action: {action}, kind: {kind}, "
                    f"({k}, {threshold}, {max}, received: {received.isoformat()}"
                    f"\nquery: {query})")

        kind_str = kind
        kind = Kind.parse(kind_str)

        combined_request = CombinedRequest(
            action=action,
            kind=kind,
            query=query,
            k=k,
            threshold=threshold,
            max=max,
        )

        combined_response = service.combined(combined_request)

        text_file_name = os.path.basename(app_config.text_file_path)

        completed = datetime.datetime.now()

        template_vars = {
            "request": request,
            "app_request": combined_request,
            "app_response": combined_response,

            "text_file": text_file_name,
            "max_len": app_config.embed_config.max_len,
            "received": received,
            "completed": completed,

            'Kind': Kind
        }
        return templates.TemplateResponse("combined.html", template_vars)

    return app

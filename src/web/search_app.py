import re
import os
import time
import logging
import datetime
from dataclasses import dataclass
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from xutils.app_config import AppConfig

from gen.element.article import Article
from gen.search.stores_flat import StoresFlat as Stores

from gen.search.k_nearest_finder import KNearestFinder
from xutils.timer import Timer

logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


@dataclass
class ArticleResult:
    similarity: float
    article: Article


def create_search_app(app_config: AppConfig) -> FastAPI:
    app = FastAPI()

    templates = Jinja2Templates(directory="web-ui/templates")
    templates.env.filters['clean_header'] = clean_header
    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    stores = Stores(app_config.text_file_path, app_config.path_prefix, app_config.max_len)
    stores.background_load()
    finder = KNearestFinder(stores, app_config.target_dim, app_config.l2_normalize)

    app.state.config = app_config
    app.state.templates = templates
    app.state.stores = stores
    app.state.finder = finder

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/search", response_class=HTMLResponse)
    async def search_get(request: Request):
        return await index(request)

    @app.post("/search", response_class=HTMLResponse)
    async def search(
        request: Request,
        query: str = Form(...), k:
        int = Form(5),
        threshold: float = Form(0.3),
        max: int = Form(10),
    ):
        logger.info(f"Received query: {query}, ({k}, {threshold}, {max})")
        logger.warning("*** --- *** --- *** MY CWD: %s" % os.getcwd())

        t0 = time.time()
        article_id_similarity_tuple_list = \
            finder.find_k_nearest_articles(query, k=k, threshold=threshold, max_results=max)
        elapsed = time.time() - t0
        logger.info(f"Found {len(article_id_similarity_tuple_list)} results")

        async with Timer("get articles"):
            results = []
            for article_id, similarity in article_id_similarity_tuple_list:
                article = stores.get_article(article_id)
                results.append(ArticleResult(similarity, article))

        text_file_name = os.path.basename(app_config.text_file_path)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request, "query": query, "results": results,
                "elapsed": elapsed, "k": k, "threshold": threshold, "max": max,
                "text_file": text_file_name,
                "max_len": app_config.max_len,
                "now": datetime.datetime.now(),
            },
        )

    return app

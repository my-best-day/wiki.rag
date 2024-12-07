import re
import time
import logging
import datetime
from dataclasses import dataclass
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from gen.element.article import Article
from gen.search.stores import Stores
from gen.search.k_nearest_finder import KNearestFinder


logger = logging.getLogger(__name__)


# TODO - load config from a config file
@dataclass
class Config:
    text_file_path: str
    path_prefix: str
    max_len: int


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


# config = Config('ignore/wiki.test.tokens', 'data/test', 1100)  # NOSONAR
# config = Config('ignore/wiki.train.tokens', 'data/train', 35200)  # NOSONAR
config = Config('ignore/wiki.test.tokens', 'data/test', 5000)  # NOSONAR

stores = Stores(config.text_file_path, config.path_prefix, config.max_len)
finder = KNearestFinder(stores)
stores.background_load()


@dataclass
class ArticleResult:
    similarity: float
    article: Article


app = FastAPI()
templates = Jinja2Templates(directory="web-ui/templates")
app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

templates.env.filters['clean_header'] = clean_header


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search_get(request: Request):
    return await index(request)


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...), k: int = Form(5),
                 threshold: float = Form(0.3), max: int = Form(10)):
    logger.info(f"Received query: {query}, ({k}, {threshold}, {max})")

    t0 = time.time()
    article_id_similarity_tuple_list = \
        finder.find_k_nearest_articles(query, k=k, threshold=threshold, max=max)
    elapsed = time.time() - t0
    logger.info(f"Found {len(article_id_similarity_tuple_list)} results")

    results = []
    for article_id, similarity in article_id_similarity_tuple_list:
        article = stores.get_article(article_id)
        results.append(ArticleResult(similarity, article))

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "query": query, "results": results,
         "elapsed": elapsed, "k": k, "threshold": threshold, "max": max,
         "now": datetime.datetime.now()},
    )

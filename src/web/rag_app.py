import re
import os
import time
import logging
import datetime
from openai import OpenAI
from dataclasses import dataclass
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from xutils.app_config import AppConfig

from gen.element.article import Article
from gen.search.stores_flat import StoresFlat as Stores

from gen.search.k_nearest_finder import KNearestFinder


logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


@dataclass
class ArticleResult:
    similarity: float
    article: Article


def create_rag_app(app_config: AppConfig) -> FastAPI:
    app = FastAPI()

    templates = Jinja2Templates(directory="web-ui/templates")
    templates.env.filters['clean_header'] = clean_header
    app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")

    stores = Stores(app_config.text_file_path, app_config.path_prefix, app_config.max_len)
    stores.background_load()
    finder = KNearestFinder(stores)

    app.state.config = app_config
    app.state.templates = templates
    app.state.stores = stores
    app.state.finder = finder

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("rag.html", {"request": request})

    @app.get("/rag", response_class=HTMLResponse)
    async def search_get(request: Request):
        return await index(request)

    @app.post("/rag", response_class=HTMLResponse)
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
            finder.find_k_nearest_articles(query, k=k, threshold=threshold, max=max)
        elapsed = time.time() - t0
        logger.info(f"Found {len(article_id_similarity_tuple_list)} results")

        article_texts = []
        for i, (article_id, similarity) in enumerate(article_id_similarity_tuple_list):
            article = stores.get_article(article_id)
            article_texts.append(f"Article {i}:\n{article.text[:15000]}")
        articles_text = "\n\n".join(article_texts)

        prompt = (
            f"question: {query}\n"
            "the following information has been retrieved to assist in the answering "
            f"of the question:\n{articles_text}"
        )

        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. "},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        answer = completion.choices[0].message.content
        # print(answer)

        text_file_name = os.path.basename(app_config.text_file_path)

        return templates.TemplateResponse(
            "rag.html",
            {
                "request": request, "query": query, "results": answer,
                "elapsed": elapsed, "k": k, "threshold": threshold, "max": max,
                "prompt_length": len(prompt),
                "text_file": text_file_name,
                "max_len": app_config.max_len,
                "now": datetime.datetime.now(),
            },
        )

    return app

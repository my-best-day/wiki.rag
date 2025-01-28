import re
import os
import logging
import datetime
from openai import OpenAI
from dataclasses import dataclass
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from xutils.app_config import AppConfig
from xutils.timer import LoggingTimer

from gen.element.article import Article
from search.stores.stores_flat import StoresFlat as Stores
from search.k_nearest_finder import KNearestFinder


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

    embed_config = app_config.embed_config
    stores = Stores.create_stores(app_config.text_file_path, embed_config)
    stores.background_load()
    finder = KNearestFinder(stores, embed_config)

    app.state.config = app_config
    app.state.templates = templates
    app.state.stores = stores
    app.state.finder = finder

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("rag.html", {"request": request})

    @app.get("/rag", response_class=HTMLResponse)
    async def rag_get(request: Request):
        return await index(request)

    @app.post("/rag", response_class=HTMLResponse)
    async def rag(request: Request,
                  query: str = Form(...), k: int = Form(5),
                  threshold: float = Form(0.3), max: int = Form(10)):

        logger.info(f"Received query: {query}, ({k}, {threshold}, {max})")

        timer = LoggingTimer('=> => => RAG APP', logger=logger, level="INFO")
        article_id_similarity_tuple_list = \
            finder.find_k_nearest_articles(query, k=k, threshold=threshold, max_results=max)
        timer.restart("Found {len(article_id_similarity_tuple_list)} results")

        article_texts = []
        for i, (article_id, similarity) in enumerate(article_id_similarity_tuple_list):
            article = stores.get_article(article_id)
            article_texts.append(f"Article {i}:\n{article.text[:15000]}")
        articles_text = "\n\n".join(article_texts)
        timer.restart("composed articles_text")

        prompt = (
            f"question: {query}\n"
            "the following information has been retrieved to assist in the answering "
            f"of the question:\n{articles_text}"
        )

        if False:
            client = OpenAI()
            timer.restart("client created")

            messages = [
                {"role": "system", "content": "You are a helpful assistant. "},
                {"role": "user", "content": prompt}
            ]
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            timer.restart("completion created")
            answer = completion.choices[0].message.content
        else:
            answer = "TODO"

        text_file_name = os.path.basename(app_config.text_file_path)
        total_elapsed = timer.total_time()
        timer.total(total_elapsed)

        template_vars = {
            "request": request,
            "query": query,
            "results": answer,
            "elapsed": total_elapsed,
            "k": k,
            "threshold": threshold,
            "max": max,
            "prompt_length": len(prompt),
            "text_file": text_file_name,
            "max_len": app_config.embed_config.max_len,
            "now": datetime.datetime.now(),
        }
        return templates.TemplateResponse("rag.html", template_vars)

    return app

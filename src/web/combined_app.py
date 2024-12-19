import re
import os
import logging
import datetime
from typing import List, Tuple
from uuid import UUID

from openai import OpenAI
from dataclasses import dataclass
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from xutils.app_config import AppConfig
from xutils.timer import LoggingTimer
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

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("combined.html", {"request": request})

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
    ) -> HTMLResponse:

        timer = LoggingTimer('combined', logger=logger, level="INFO")

        logger.info(f"Received query: action: {action}, ({k}, {threshold}, {max}\nquery: {query})")

        article_id_similarity_tuple_list = \
            finder.find_k_nearest_articles(query, k=k, threshold=threshold, max_results=max)
        timer.restart(f"Found {len(article_id_similarity_tuple_list)} results")

        article_results = get_article_results(article_id_similarity_tuple_list)
        timer.restart(f"got article results (len: {len(article_results)})")

        if action == "rag":
            prompt, answer = do_rag(query, article_results)
        else:
            prompt, answer = "na", "na"
        timer.restart(f"did rag (prompt len: {len(prompt)}, answer len: {len(answer)})")

        text_file_name = os.path.basename(app_config.text_file_path)
        total_elapsed = timer.total_time()
        timer.total(total_elapsed)

        template_vars = {
            "request": request,
            "action": action,
            "query": query,
            "article_results": article_results,
            "answer": answer,

            "k": k,
            "threshold": threshold,
            "max": max,

            "prompt_length": len(prompt),
            "text_file": text_file_name,
            "max_len": app_config.embed_config.max_len,
            "elapsed": total_elapsed,
            "now": datetime.datetime.now(),
        }
        return templates.TemplateResponse("combined.html", template_vars)

    def do_rag(query: str, article_results: List[ArticleResult]):
        timer = LoggingTimer('do_rag', logger=logger, level="INFO")

        articles_text = get_articles_text(article_results)

        prompt = (
            f"question: {query}\n"
            "the following information has been retrieved to assist in the answering "
            f"of the question:\n{articles_text}"
        )

        if not query.startswith("what, are you doing? this is not right!"):
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
            prompt, answer = "na", "na"

        return prompt, answer

    def get_article_results(
        article_id_similarity_tuple_list: List[Tuple[UUID, float]]
    ) -> List[ArticleResult]:
        results = []
        for article_id, similarity in article_id_similarity_tuple_list:
            article = stores.get_article(article_id)
            results.append(ArticleResult(similarity, article))
        return results

    def get_articles_text(article_results: List[ArticleResult]) -> str:
        article_texts = []
        for i, (article_result) in enumerate(article_results):
            article_texts.append(f"Article {i}:\n{article_result.article.text[:15000]}")
        articles_text = "\n\n".join(article_texts)
        return articles_text

    return app

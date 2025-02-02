import re
import os
import logging
import datetime

from fastapi import Form, Request, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from xutils.app_config import AppConfig
from search.services.combined_service import (
    CombinedService,
    CombinedRequest,
    Kind,
    Action,
    parse_enum
)


logger = logging.getLogger(__name__)


def clean_header(text):
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_router(
    app_config: AppConfig,
    service: CombinedService
) -> APIRouter:

    router = APIRouter()

    templates = Jinja2Templates(directory="web-ui/templates")
    templates.env.filters['clean_header'] = clean_header
    templates.env.globals['Kind'] = Kind

    @router.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        template_vars = {
            "request": request,
            "kind": Kind
        }
        response = templates.TemplateResponse("combined.html", template_vars)
        return response

    @router.get("/combined", response_class=HTMLResponse)
    async def combined_get(request: Request) -> HTMLResponse:
        return await index(request)

    @router.post("/combined", response_class=HTMLResponse)
    async def combined(
        request: Request,
        action: str = Form(...),
        kind: str = Form(...),
        query: str = Form(...),
        k: int = Form(5),
        threshold: float = Form(0.3),
        max: int = Form(10),
    ) -> HTMLResponse:

        received = datetime.datetime.now()

        logger.info(f"Received query: action: {action}, kind: {kind}, "
                    f"({k}, {threshold}, {max}, received: {received.isoformat()}"
                    f"\nquery: {query})")

        kind_str = kind
        kind = parse_enum(Kind, kind_str)

        action_str = action
        action = parse_enum(Action, action_str)

        combined_request = CombinedRequest(
            action=action,
            kind=kind,
            k=k,
            threshold=threshold,
            max=max,
            query=query
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
            "duration": completed - received,
        }

        response = templates.TemplateResponse("combined.html", template_vars)
        return response

    return router

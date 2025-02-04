import re
import os
import logging
import datetime

from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import Form, Request, APIRouter, Depends
from fastapi.templating import Jinja2Templates


from xutils.app_config import AppConfig
from typing import List
from search.services.combined_service import (
    CombinedService,
    CombinedRequest,
    CombinedResponse,
    Kind,
    Action,
    ResultElement
)


logger = logging.getLogger(__name__)


class CombinedRequestModel(BaseModel):
    id: str
    action: Action
    kind: Kind
    query: str
    k: int = 5
    threshold: float = 0.3
    max: int = 10

    def to_combined_request(self) -> CombinedRequest:
        return CombinedRequest(
            id=self.id,
            action=self.action,
            kind=self.kind,
            query=self.query,
            k=self.k,
            threshold=self.threshold,
            max=self.max,
        )

    class Config:
        use_enum_values = True


class CombinedAppResponseModel(BaseModel):
    id: str
    action: Action
    prompt: str
    results: List[ResultElement]
    answer: str
    total_length: int

    @classmethod
    def from_combined_response(
        cls,
        combined_response: CombinedResponse
    ) -> "CombinedAppResponseModel":
        return CombinedAppResponseModel(
            id=combined_response.id,
            action=combined_response.action,
            prompt=combined_response.prompt,
            results=combined_response.results,
            answer=combined_response.answer,
            total_length=combined_response.total_length,
        )


class CombinedMetaModel(BaseModel):
    text_file: str
    max_len: int
    received: datetime.datetime
    completed: datetime.datetime
    duration: datetime.timedelta


class CombinedResponseModel(BaseModel):
    data: CombinedAppResponseModel
    meta: CombinedMetaModel


def parse_combined_request(
    id: str = Form(...),
    action: str = Form(...),
    kind: str = Form(...),
    query: str = Form(...),
    k: int = Form(5),
    threshold: float = Form(0.3),
    max: int = Form(10)
) -> CombinedRequest:

    request = CombinedRequest(
        id=id,
        action=action,
        kind=kind,
        query=query,
        k=k,
        threshold=threshold,
        max=max,
    )
    return request


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
        combined_request: CombinedRequest = Depends(parse_combined_request)
    ) -> HTMLResponse:
        received = datetime.datetime.now()

        action = combined_request.action
        kind = combined_request.kind
        query = combined_request.query
        k = combined_request.k
        threshold = combined_request.threshold
        max_len = combined_request.max

        logger.info(f"Received query: action: {action}, kind: {kind}, "
                    f"({k}, {threshold}, {max_len}, received: {received.isoformat()}"
                    f"\nquery: {query})")
        logger.info(f"Received request: {combined_request}")

        combined_response = service.combined(combined_request)

        text_file_name = os.path.basename(app_config.text_file_path)
        completed = datetime.datetime.now()

        template_vars = {
            "request": request,
            "app_request": combined_request,
            "app_response": combined_response,
            "text_file": text_file_name,
            # TODO: remove, max_len is available in the request
            "max_len": app_config.embed_config.max_len,
            "received": received,
            "completed": completed,
            "duration": completed - received,
        }

        response = templates.TemplateResponse("combined.html", template_vars)
        return response

    @router.post("/api/combined", response_model=CombinedResponseModel)
    async def combined_api(request: CombinedRequestModel):
        received = datetime.datetime.now()

        combined_request = request.to_combined_request()

        combined_response = service.combined(combined_request)

        text_file_name = os.path.basename(app_config.text_file_path)
        max_len = app_config.embed_config.max_len
        completed = datetime.datetime.now()

        response = CombinedAppResponseModel.from_combined_response(combined_response)
        meta = CombinedMetaModel(
            text_file=text_file_name,
            max_len=max_len,
            received=received.isoformat(),
            completed=completed.isoformat(),
            duration=completed - received,
        )
        combined_response_model = CombinedResponseModel(
            data=response,
            meta=meta,
        )
        return combined_response_model

    return router

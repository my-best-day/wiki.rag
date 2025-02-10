"""
Routes for the combined app.
"""

import re
import os
import logging
import datetime
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import Request, APIRouter, Depends
from fastapi.templating import Jinja2Templates

from xutils.app_config import AppConfig
from search.services.combined_service import (
    CombinedService,
    CombinedRequest,
    CombinedResponse,
    Kind,
    Action,
    ResultElement
)


logger = logging.getLogger(__name__)


@dataclass
class CombinedRequestForm:
    """
    Dataclass for the combined request that is used for the form.
    """
    id: str
    action: str
    kind: str
    query: str
    k: int = 5
    threshold: float = 0.3
    max: int = 10


class CombinedRequestModel(BaseModel):
    """
    Pydantic model for the combined request that is used for the API.
    """
    id: str
    action: Action
    kind: Kind
    query: str
    k: int = 5
    threshold: float = 0.3
    max: int = 10

    def to_combined_request(self) -> CombinedRequest:
        """
        Converts the CombinedRequestModel to a CombinedRequest which
        is used for the service.
        """
        return CombinedRequest(
            id=self.id,
            action=self.action,
            kind=self.kind,
            query=self.query,
            k=self.k,
            threshold=self.threshold,
            max=self.max,
        )


class CombinedAppResponseModel(BaseModel):
    """
    Pydantic model for the result of the combined service.
    """
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
        """
        Constructs a CombinedAppResponseModel from a CombinedResponse from the service.
        """
        return CombinedAppResponseModel(
            id=combined_response.id,
            action=combined_response.action,
            prompt=combined_response.prompt,
            results=combined_response.results,
            answer=combined_response.answer,
            total_length=combined_response.total_length,
        )


class CombinedMetaModel(BaseModel):
    """
    Pydantic model for the meta data part of the response.
    """
    text_file: str
    max_len: int
    received: datetime.datetime
    completed: datetime.datetime
    duration: datetime.timedelta


class CombinedResponseModel(BaseModel):
    """
    Pydantic model for the response that includes the results and the meta data.
    """
    data: CombinedAppResponseModel
    meta: CombinedMetaModel


def parse_combined_request(form: CombinedRequestForm) -> CombinedRequest:
    """Get the data from the submitted form and convert it to a CombinedRequest."""
    request = CombinedRequest(**vars(form))
    return request


def clean_header(text):
    """Clean the header of the text to make it more readable."""
    return re.sub(r'(^\s*=\s+)|(\s+=\s*$)', '', text)


def create_combined_router(
    app_config: AppConfig,
    service: CombinedService
) -> APIRouter:
    """Create the FastAPI router for the combined service."""
    router = APIRouter()

    templates = Jinja2Templates(directory="web-ui/templates")
    templates.env.filters['clean_header'] = clean_header
    templates.env.globals['Kind'] = Kind

    @router.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Render the combined app form page."""
        return await combined_get(request)

    @router.get("/combined", response_class=HTMLResponse)
    async def combined_get(request: Request) -> HTMLResponse:
        """Render the combined app form."""
        template_vars = {
            "request": request,
            "kind": Kind
        }
        response = templates.TemplateResponse("combined.html", template_vars)
        return response

    @router.post("/combined", response_class=HTMLResponse)
    async def combined(
        request: Request,
        combined_request: CombinedRequest = Depends(parse_combined_request)
    ) -> HTMLResponse:
        """Process the combined request and render the results page."""

        received = datetime.datetime.now()

        action = combined_request.action
        kind = combined_request.kind
        query = combined_request.query
        k = combined_request.k
        threshold = combined_request.threshold
        max_len = combined_request.max

        logger.info("Received query: action: %s, kind: %s, (%d, %f, %d, received: %s)",
                    action, kind, k, threshold, max_len, received.isoformat())
        logger.info("Query: %s", query)
        logger.info("Received request: %s", combined_request)

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

    @router.post("/api/combined", response_model=CombinedResponseModel)
    async def combined_api(request: CombinedRequestModel):
        """Process the combined api request and return the response."""

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

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

from app.helpers.datetime_utils import format_utc

UtcDateTime = Annotated[
    datetime,
    PlainSerializer(format_utc, return_type=str, when_used="json"),
]


class HealthResponse(BaseModel):
    status: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

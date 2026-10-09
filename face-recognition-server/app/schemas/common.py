"""Shared protocol envelope."""
from time import time
from uuid import uuid4
from pydantic import BaseModel, Field


def new_request_id() -> str:
    return uuid4().hex


class ErrorDetail(BaseModel):
    code: str
    message: str


class Envelope(BaseModel):
    type: str = 'result'
    request_id: str = Field(default_factory=new_request_id)
    timestamp: int = Field(default_factory=lambda: int(time() * 1000))
    success: bool = True
    error: ErrorDetail | None = None

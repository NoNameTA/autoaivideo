from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Phân trang con trỏ (SPEC 09 §5)."""

    items: list[T]
    next_cursor: str | None = None


class ErrorDetail(BaseModel):
    field: str
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody

"""Lỗi ứng dụng + handler trả envelope chuẩn (SPEC 09 §6)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.ids import new_id


class AppError(Exception):
    code: str = "INTERNAL"
    status: int = 500

    def __init__(
        self,
        message: str,
        *,
        details: list[dict[str, Any]] | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []
        self.trace_id = trace_id or new_id("trc")


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status = 404


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status = 422


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status = 403


class ConflictError(AppError):
    code = "CONFLICT"
    status = 409


def _envelope(code: str, message: str, details: list[dict[str, Any]], trace_id: str) -> dict:
    return {"error": {"code": code, "message": message, "details": details, "trace_id": trace_id}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=_envelope(exc.code, exc.message, exc.details, exc.trace_id),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "issue": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_envelope("VALIDATION_ERROR", "Dữ liệu không hợp lệ", details, new_id("trc")),
        )

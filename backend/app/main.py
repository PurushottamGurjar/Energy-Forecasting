import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import router
from app.config.settings import get_settings
from app.core.exceptions import AppError
from app.clients.elexon_client import ElexonClient

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    timeout = httpx.Timeout(settings.elexon_timeout_seconds)
    async with httpx.AsyncClient(
        base_url=settings.elexon_base_url_normalized,
        timeout=timeout,
        headers={"Accept": "application/json"},
    ) as http:
        app.state.elexon_client = ElexonClient(http, settings)
        yield
    app.state.elexon_client = None


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="UK Wind Forecast Accuracy API",
        version="1.0.0",
        lifespan=lifespan,
    )
    origins = get_settings().cors_origin_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET"],
            allow_headers=["Accept"],
        )
    app.include_router(router, prefix="/api/v1")
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(Exception, _unexpected_handler)
    return app


async def _app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = exc if isinstance(exc, AppError) else AppError("An unexpected error occurred")
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


async def _validation_handler(_request: Request, exc: Exception) -> JSONResponse:
    details = exc.errors() if isinstance(exc, RequestValidationError) else []
    parts: list[str] = []
    for detail in details:
        location = [str(item) for item in detail.get("loc", []) if item not in {"query", "body"}]
        field = ".".join(location) or "request"
        message = str(detail.get("msg", "Invalid value"))
        prefix = "Value error, "
        if message.startswith(prefix):
            message = message[len(prefix) :]
        parts.append(f"{field}: {message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "; ".join(parts) or "The request parameters are invalid",
            }
        },
    )


async def _unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred",
            }
        },
    )


app = create_app()

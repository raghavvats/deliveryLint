"""DeliveryLint FastAPI application."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config.settings import get_settings
from backend.app.db.models import init_db
from backend.app.routes.analysis import router as analysis_router
from backend.app.services.llm_client import LLMResponseError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(get_settings().database_url)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeliveryLint",
        description="Structured review assistant for implementation documents",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(LLMResponseError)
    async def llm_response_error_handler(_: Request, exc: LLMResponseError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(httpx.HTTPStatusError)
    async def openai_http_error_handler(_: Request, exc: httpx.HTTPStatusError) -> JSONResponse:
        detail = f"OpenAI API error ({exc.response.status_code}). Check API key and model name."
        return JSONResponse(status_code=502, content={"detail": detail})

    app.include_router(analysis_router)
    return app


app = create_app()

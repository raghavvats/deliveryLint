"""DeliveryLint FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.db.models import init_db
from backend.app.routes.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeliveryLint",
        description="Structured review assistant for implementation documents",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(analysis_router)
    return app


app = create_app()

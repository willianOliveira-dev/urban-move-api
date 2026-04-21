import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.config.env import env
from src.modules.mobility.router import router as mobility_router

logging.basicConfig(
    level=getattr(logging, env.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("urbanmove")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    logger.info("Iniciando UrbanMove API...")
    yield
    logger.info("Encerrando UrbanMove API...")


def create_app() -> FastAPI:
    fastapi = FastAPI(
        title=env.APP_NAME,
        version=env.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if env.DEBUG else None,
        redoc_url="/redoc" if env.DEBUG else None,
    )

    fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=env.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi.add_middleware(GZipMiddleware, minimum_size=1000)

    @fastapi.get("/health", tags=["Infra"])
    async def health_check() -> dict[str, str]:
        return {
            "status": "healthy",
            "app": env.APP_NAME,
            "version": env.APP_VERSION,
            "environment": env.ENVIRONMENT,
        }

    fastapi.include_router(mobility_router)

    return fastapi


app = create_app()

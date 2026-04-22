import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.config.env import env
from src.core.db.database import close_db, close_redis, init_db, init_redis
from src.modules.mobility.router import router as mobility_router
from src.modules.mobility.sptrans.worker import SPTransWorker

logging.basicConfig(
    level=getattr(logging, env.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("urbanmove.main")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Gerenciamento do ciclo de vida da aplicação (DB, Redis, Background Workers)."""
    logger.info("Initializing UrbanMove Backend Infrastructure...")
    
    await init_db()
    await init_redis()
    
    logger.info("Starting background services...")
    worker = SPTransWorker()
    worker_task = asyncio.create_task(
        worker.start(position_interval=30, stops_interval_hours=24)
    )
    
    yield

    logger.info("Graceful shutdown initiated...")
    worker.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    await close_redis()
    await close_db()
    logger.info("Infrastructure shutdown complete.")


def create_app() -> FastAPI:
    fastapi = FastAPI(
        title="UrbanMove API",
        description="""
        Backend de Mobilidade Urbana Inteligente para a cidade de São Paulo.
        
        ### Funcionalidades:
        * **Planejamento de Rotas**: Integração com Google Directions.
        * **Paradas Próximas**: Busca geolocalizada de pontos de ônibus e estações.
        * **Previsões em Tempo Real**: Chegadas de ônibus via integração SPTrans Olho Vivo.
        * **Otimização**: Cache em Redis para resultados frequentes.
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )


    fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=env.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi.add_middleware(GZipMiddleware, minimum_size=1000)

   
    @fastapi.get("/health", tags=["Infra"], summary="Verifica saúde do sistema")
    async def health_check() -> dict[str, str]:
        return {
            "status": "healthy",
            "version": env.APP_VERSION,
            "environment": env.ENVIRONMENT,
        }

   
    fastapi.include_router(mobility_router)

    return fastapi


app = create_app()

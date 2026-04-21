import logging
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config.env import env

logger = logging.getLogger(__name__)

engine = create_async_engine(
    env.DATABASE_URL,
    echo=env.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

_redis_client: aioredis.Redis | None = None


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)
    logger.info("Database engine connected successfully")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database engine disposed")


async def init_redis() -> None:
    global _redis_client
    _redis_client = aioredis.from_url(
        env.REDIS_URL,
        decode_responses=True,
    )
    await _redis_client.ping()
    logger.info("Redis connected successfully")


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_client

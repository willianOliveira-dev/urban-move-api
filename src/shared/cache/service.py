import hashlib
import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger("urbanmove.shared.cache")


class CacheService:
    """Serviço de cache genérico usando Redis com TTL e serialização JSON."""

    def __init__(self, redis_client: aioredis.Redis, prefix: str, ttl_seconds: int) -> None:
        self._redis = redis_client
        self._prefix = prefix
        self._ttl_seconds = ttl_seconds

    def _build_key(self, raw_key: str) -> str:
        """Gera uma chave Redis determinística a partir do input."""
        hashed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
        return f"{self._prefix}:{hashed}"

    async def get(self, raw_key: str) -> dict[str, object] | None:
        """Busca valor no cache. Retorna None se não existir ou expirado."""
        key = self._build_key(raw_key)
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            logger.debug({"event": "cache.hit", "key": key})
            result: dict[str, object] = json.loads(data)
            return result
        except (aioredis.RedisError, json.JSONDecodeError) as e:
            logger.warning({"event": "cache.read_error", "key": key, "error": str(e)})
            return None

    async def set(self, raw_key: str, value: dict[str, object]) -> None:
        """Armazena valor no cache com TTL configurado."""
        key = self._build_key(raw_key)
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self._redis.setex(key, self._ttl_seconds, serialized)
            logger.debug({"event": "cache.set", "key": key, "ttl": self._ttl_seconds})
        except (aioredis.RedisError, TypeError) as e:
            logger.warning({"event": "cache.write_error", "key": key, "error": str(e)})

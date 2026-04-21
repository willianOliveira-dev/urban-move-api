import logging
import time

import httpx
import jwt
from jwt import PyJWKClient

from src.core.config.env import env

logger = logging.getLogger(__name__)

_JWKS_CACHE_TTL_SECONDS = 600
_jwks_client: PyJWKClient | None = None
_jwks_client_created_at: float = 0.0


class InvalidTokenError(Exception):
    pass


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_client_created_at

    now = time.monotonic()
    if _jwks_client is None or (now - _jwks_client_created_at) > _JWKS_CACHE_TTL_SECONDS:
        _jwks_client = PyJWKClient(
            env.supabase_jwks_url,
            cache_keys=True,
            lifespan=_JWKS_CACHE_TTL_SECONDS,
        )
        _jwks_client_created_at = now
        logger.debug("JWKS client initialized from %s", env.supabase_jwks_url)

    return _jwks_client


def verify_supabase_jwt(token: str) -> dict[str, object]:
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)

        payload: dict[str, object] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "HS256"],
            options={"verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token expirado")
    except (jwt.InvalidTokenError, httpx.HTTPError) as e:
        raise InvalidTokenError(f"Token inválido: {e}")

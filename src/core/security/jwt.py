import jwt

from src.core.config.env import env


class InvalidTokenError(Exception):
    pass


def verify_supabase_jwt(token: str) -> dict[str, object]:
    try:
        payload: dict[str, object] = jwt.decode(
            token,
            env.JWT_SECRET,
            algorithms=[env.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token expirado")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Token inválido: {e}")

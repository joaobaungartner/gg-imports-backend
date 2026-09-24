from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config.config import get_settings


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    to_encode = data.copy()
    to_encode.setdefault("purpose", "access")
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str, *, expected_purpose: str = "access") -> dict:
    settings = get_settings()
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    # Fail closed, including for legacy tokens without an explicit purpose.
    if payload.get("purpose") != expected_purpose:
        raise JWTError("Finalidade do token inválida")
    return payload

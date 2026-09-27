from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .services import user_store
from .services.ratelimit import SlidingWindowLimiter
from .services.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def current_user_id(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> int:
    uid = decode_token(creds.credentials, settings.jwt_secret) if creds else None
    if uid is None or user_store.get_by_id(uid) is None:
        raise HTTPException(401, "Sign in to continue.", headers={"WWW-Authenticate": "Bearer"})
    return uid


_chat = SlidingWindowLimiter(settings.rate_chat_per_min, 60)
_upload = SlidingWindowLimiter(settings.rate_upload_per_hour, 3600)
_auth = SlidingWindowLimiter(settings.rate_auth_per_min, 60)


def _too_many(retry_after: int) -> HTTPException:
    return HTTPException(
        429, "Too many requests. Please wait a moment and try again.", headers={"Retry-After": str(retry_after)}
    )


def chat_rate_limit(user_id: int = Depends(current_user_id)) -> int:
    if not _chat.allow(str(user_id)):
        raise _too_many(60)
    return user_id


def upload_rate_limit(user_id: int = Depends(current_user_id)) -> int:
    if not _upload.allow(str(user_id)):
        raise _too_many(3600)
    return user_id


def auth_rate_limit(request: Request) -> None:
    # Behind a reverse proxy, configure uvicorn --proxy-headers so client.host is the real IP.
    if not _auth.allow(request.client.host if request.client else "unknown"):
        raise _too_many(60)

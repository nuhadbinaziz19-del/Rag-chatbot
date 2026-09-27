"""Password hashing and JWT helpers. Pure functions so they are easy to unit test."""
import base64
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt


def _prep(password: str) -> bytes:
    # SHA-256 first: bcrypt silently/loudly breaks past 72 bytes, and Bangla is 3 bytes per character.
    return base64.b64encode(hashlib.sha256(password.encode()).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(password), hashed.encode())
    except ValueError:
        return False


def create_token(user_id: int, secret: str, minutes: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> int | None:
    try:
        return int(jwt.decode(token, secret, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

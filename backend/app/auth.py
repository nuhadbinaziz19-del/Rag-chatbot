from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .deps import auth_rate_limit, current_user_id
from .services import user_store
from .services.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
_DUMMY_HASH = hash_password("timing-equalizer")  # keeps login timing similar for unknown emails


class Credentials(BaseModel):
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


def _session(user_id: int, email: str) -> dict:
    token = create_token(user_id, settings.jwt_secret, settings.jwt_expire_minutes)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user_id, "email": email}}


@router.post("/register", status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(c: Credentials):
    email = c.email.lower()
    user_id = user_store.create_user(email, hash_password(c.password))
    if user_id is None:
        raise HTTPException(409, "An account with this email already exists.")
    return _session(user_id, email)


@router.post("/login", dependencies=[Depends(auth_rate_limit)])
def login(c: Credentials):
    user = user_store.get_by_email(c.email.lower())
    ok = verify_password(c.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not ok:
        raise HTTPException(401, "Incorrect email or password.")
    return _session(user["id"], user["email"])


@router.get("/me")
def me(user_id: int = Depends(current_user_id)):
    return user_store.get_by_id(user_id)

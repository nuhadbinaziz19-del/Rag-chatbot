import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .auth import router as auth_router
from .chat import router as chat_router
from .config import settings
from .db import init_db
from .deps import current_user_id, upload_rate_limit
from .services import store
from .services.ingest import ingest_pdf
from .services.retrieve import retrieve

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.jwt_secret == "dev-secret-change-me":
        log.warning("JWT_SECRET is the insecure default. Set a long random value before deploying.")
    init_db()
    yield


app = FastAPI(title="Nothi: Bilingual RAG API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: list[int] | None = None


@app.get("/health")
def health():
    return {"status": "ok", "embedding_model": settings.embedding_model}


@app.post("/documents", status_code=201)
def upload_document(file: UploadFile = File(...), user_id: int = Depends(upload_rate_limit)):
    if store.count_documents(user_id) >= settings.max_docs_per_user:
        raise HTTPException(403, f"Document limit reached ({settings.max_docs_per_user}). Delete one to upload another.")
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB limit.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Only PDF files are supported.")
    try:
        return ingest_pdf(user_id, file.filename or "document.pdf", data)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/documents")
def get_documents(user_id: int = Depends(current_user_id)):
    return store.list_documents(user_id)


@app.delete("/documents/{doc_id}", status_code=204)
def remove_document(doc_id: int, user_id: int = Depends(current_user_id)):
    if not store.delete_document(doc_id, user_id):
        raise HTTPException(404, "Document not found.")


@app.post("/search")
def search(req: SearchRequest, user_id: int = Depends(current_user_id)):
    return {"query": req.query, "results": retrieve(req.query, req.top_k, user_id, req.document_ids)}

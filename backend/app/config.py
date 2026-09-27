from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://rag:rag@localhost:5432/rag"

    # Ingestion
    embedding_model: str = "intfloat/multilingual-e5-base"  # or BAAI/bge-m3 (dim 1024)
    embedding_dim: int = 768
    chunk_size: int = 900
    chunk_overlap: int = 150
    max_upload_mb: int = 20
    ocr_langs: str = "ben+eng"
    min_text_chars_per_page: int = 40

    # Retrieval
    retrieve_candidates: int = 20  # per retriever, before fusion
    context_chunks: int = 5  # chunks sent to the LLM
    use_reranker: bool = False  # cross-encoder rerank (heavier, more accurate)
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_max_tokens: int = 1024
    history_turns: int = 6

    # Auth, CORS and limits
    jwt_secret: str = "dev-secret-change-me"  # MUST be overridden in production
    jwt_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    max_docs_per_user: int = 20
    rate_chat_per_min: int = 20
    rate_upload_per_hour: int = 10
    rate_auth_per_min: int = 10


settings = Settings()

"""MediBot backend configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings bound to environment variables. Validated at startup."""

    # LLM
    google_api_key: str = Field(..., description="Google Generative AI API key")
    llm_model: str = Field(default="gemini-3.6-flash", description="LLM model name")

    # Embedding
    embed_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Dense embedding model (sentence-transformers)",
    )
    embed_dimension: int = Field(default=384, description="Dense embedding vector dimension")

    # Sparse Embedding
    sparse_embed_model: str = Field(
        default="Qdrant/bm25",
        description="Sparse embedding model for BM25 keyword search",
    )

    # Qdrant
    qdrant_url: str = Field(default="", description="Qdrant server URL (leave empty for local file mode)")
    qdrant_path: str = Field(default="./qdrant_data", description="Local Qdrant storage path (used when qdrant_url is empty)")
    qdrant_collection_name: str = Field(
        default="medibot_docs", description="Qdrant collection name"
    )

    # Paths
    data_dir: str = Field(default="../../mediassist_data", description="Path to data directory")
    sqlite_db_path: str = Field(
        default="../../mediassist_data/db/mediassist.db",
        description="Path to SQLite database",
    )

    # JWT
    jwt_secret_key: str = Field(
        default="change-this-to-a-random-secret-in-production",
        description="JWT signing secret",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=60, description="JWT token expiry in minutes")

    # Retrieval
    retrieval_top_k: int = Field(
        default=10, description="Number of chunks from initial hybrid retrieval"
    )

    # Cross-encoder reranker
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking",
    )
    reranker_top_n: int = Field(
        default=3, description="Number of chunks after reranking"
    )

    # Chunking
    max_chunk_tokens: int = Field(
        default=512, description="Max tokens per chunk for HybridChunker"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def load_settings() -> Settings:
    """Load and validate settings. Fails fast with a descriptive error if invalid."""
    return Settings()

"""MediBot FastAPI application — main entry point.

Endpoints:
    POST /login              — Authenticate and receive a JWT token
    POST /chat               — Main RAG endpoint with RBAC
    GET  /collections/{role} — List accessible collections for a role
    GET  /health             — Health check
"""

import os
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings, Settings
from app.auth import authenticate_user, create_access_token, decode_access_token
from app.rbac import get_accessible_collections, VALID_ROLES
from app.schemas import (
    LoginRequest,
    LoginResponse,
    ChatRequest,
    ChatResponse,
    CollectionsResponse,
    HealthResponse,
)
from app.vector_store import VectorStore
from app.reranker import Reranker
from app.rag_pipeline import RAGPipeline

logger = structlog.get_logger(__name__)

# Module-level singletons initialized during startup
_settings: Settings | None = None
_vector_store: VectorStore | None = None
_reranker: Reranker | None = None
_rag_pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — initialize components on startup, cleanup on shutdown."""
    global _settings, _vector_store, _reranker, _rag_pipeline

    logger.info("startup_begin")
    _settings = load_settings()

    _vector_store = VectorStore(_settings)
    _reranker = Reranker(_settings)
    _rag_pipeline = RAGPipeline(_settings, _vector_store, _reranker)

    logger.info(
        "startup_complete",
        qdrant_connected=_vector_store.is_connected(),
        collection_count=_vector_store.collection_count(),
    )
    yield

    logger.info("shutdown")


app = FastAPI(
    title="MediBot API",
    description="Advanced RAG chatbot with RBAC for MediAssist Health Network",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and validate the JWT token from the Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token, _settings)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    """Authenticate a user and return a JWT token with role information."""
    user = authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        settings=_settings,
    )

    collections = get_accessible_collections(user["role"])

    logger.info("user_logged_in", username=user["username"], role=user["role"])

    return LoginResponse(
        access_token=token,
        role=user["role"],
        full_name=user["full_name"],
        username=user["username"],
        collections=collections,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: dict = Depends(_get_current_user),
) -> ChatResponse:
    """Main RAG endpoint. Routes to Hybrid RAG or SQL RAG based on intent.

    RBAC is enforced at the Qdrant retrieval layer — the metadata filter
    ensures only chunks matching the user's role are returned.
    """
    role = user.get("role", "")
    username = user.get("sub", "")

    logger.info(
        "chat_request",
        username=username,
        role=role,
        question_length=len(request.question),
    )

    response = _rag_pipeline.process_query(
        question=request.question,
        role=role,
    )

    return response


@app.get("/collections/{role}", response_model=CollectionsResponse)
def get_collections(role: str) -> CollectionsResponse:
    """Return the list of document collections accessible to the given role."""
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Valid roles: {', '.join(VALID_ROLES)}",
        )

    collections = get_accessible_collections(role)
    return CollectionsResponse(role=role, collections=collections)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check — reports Qdrant and database connectivity."""
    qdrant_ok = _vector_store.is_connected() if _vector_store else False

    db_ok = False
    try:
        if _settings:
            conn = sqlite3.connect(_settings.sqlite_db_path)
            conn.execute("SELECT 1")
            conn.close()
            db_ok = True
    except Exception:
        pass

    status = "healthy" if (qdrant_ok and db_ok) else "degraded"

    return HealthResponse(
        status=status,
        qdrant_connected=qdrant_ok,
        database_accessible=db_ok,
    )

"""Pydantic request/response schemas for the API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., min_length=1, description="Demo username")
    password: str = Field(..., min_length=1, description="Demo password")


class LoginResponse(BaseModel):
    """Login response with JWT token and user info."""
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    username: str
    collections: List[str]


class ChatRequest(BaseModel):
    """Chat request body."""
    question: str = Field(..., min_length=1, max_length=2000, description="User question")


class SourceInfo(BaseModel):
    """Source citation for a retrieved chunk."""
    source_document: str
    section_title: str
    collection: str


class ChatResponse(BaseModel):
    """Chat response with answer, sources, and metadata."""
    answer: str
    sources: List[SourceInfo]
    retrieval_type: str = Field(
        ..., description="One of 'hybrid_rag' or 'sql_rag'"
    )
    role: str


class CollectionsResponse(BaseModel):
    """Response for accessible collections endpoint."""
    role: str
    collections: List[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    qdrant_connected: bool
    database_accessible: bool

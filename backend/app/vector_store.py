"""Vector store operations using langchain_qdrant with hybrid search (dense + BM25).

Uses QdrantVectorStore with RetrievalMode.HYBRID, HuggingFaceEmbeddings for dense,
and FastEmbedSparse for BM25 sparse vectors — matching the cohort patterns.
RBAC is enforced via Qdrant payload filters on every query.

Supports both local file mode (no Docker) and remote Qdrant server.
"""

from typing import List, Dict, Any, Optional

import structlog
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client.models import Filter, FieldCondition, MatchAny

from app.config import Settings

logger = structlog.get_logger(__name__)


def _build_embeddings(settings: Settings) -> tuple:
    """Build dense and sparse embedding instances."""
    dense = HuggingFaceEmbeddings(
        model_name=settings.embed_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    sparse = FastEmbedSparse(model_name=settings.sparse_embed_model)
    return dense, sparse


def _location_kwargs(settings: Settings) -> dict:
    """Return the Qdrant connection kwargs (url or path)."""
    if settings.qdrant_url:
        return {"url": settings.qdrant_url}
    return {"path": settings.qdrant_path}


class VectorStore:
    """Manages Qdrant collection for hybrid (dense + BM25 sparse) search with RBAC."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._collection_name = settings.qdrant_collection_name
        self._dense_embeddings, self._sparse_embeddings = _build_embeddings(settings)
        self._loc_kwargs = _location_kwargs(settings)
        self._vectorstore: Optional[QdrantVectorStore] = None

        mode = "remote" if settings.qdrant_url else "local"
        logger.info(f"qdrant_{mode}_mode", **self._loc_kwargs)

    # ------------------------------------------------------------------
    # Indexing (called once by scripts/ingest.py)
    # ------------------------------------------------------------------
    def index_documents(self, documents: List[Document]) -> None:
        """Index documents into Qdrant with both dense and sparse vectors.

        Uses QdrantVectorStore.from_documents which stores BOTH dense and sparse
        vectors at index time using RetrievalMode.HYBRID.
        """
        logger.info("indexing_documents", count=len(documents))

        self._vectorstore = QdrantVectorStore.from_documents(
            documents=documents,
            embedding=self._dense_embeddings,
            sparse_embedding=self._sparse_embeddings,
            collection_name=self._collection_name,
            retrieval_mode=RetrievalMode.HYBRID,
            force_recreate=True,
            **self._loc_kwargs,
        )

        logger.info("indexing_complete", count=len(documents))

    # ------------------------------------------------------------------
    # Querying (called by the FastAPI server)
    # ------------------------------------------------------------------
    def connect_existing(self) -> None:
        """Connect to an existing Qdrant collection (called on server startup)."""
        self._vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=self._dense_embeddings,
            sparse_embedding=self._sparse_embeddings,
            collection_name=self._collection_name,
            retrieval_mode=RetrievalMode.HYBRID,
            **self._loc_kwargs,
        )
        logger.info("vectorstore_connected", collection=self._collection_name)

    def hybrid_search(
        self,
        query: str,
        role: str,
        accessible_collections: List[str],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (dense + BM25) with RBAC metadata filter.

        RBAC enforcement: The Qdrant filter ensures only chunks whose access_roles
        contain the user's role are returned. This filter is applied BEFORE any
        results reach the application — restricted chunks are never returned.
        """
        if self._vectorstore is None:
            self.connect_existing()

        # RBAC filter — applied at the Qdrant query level
        rbac_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.access_roles",
                    match=MatchAny(any=[role]),
                ),
            ]
        )

        results = self._vectorstore.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=rbac_filter,
        )

        search_results: List[Dict[str, Any]] = []
        for doc, score in results:
            search_results.append({
                "text": doc.page_content,
                "source_document": doc.metadata.get("source_document", ""),
                "collection": doc.metadata.get("collection", ""),
                "section_title": doc.metadata.get("section_title", ""),
                "chunk_type": doc.metadata.get("chunk_type", ""),
                "score": float(score),
            })

        logger.info(
            "hybrid_search_complete",
            role=role,
            query_length=len(query),
            results_count=len(search_results),
        )
        return search_results

    def is_connected(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            if self._vectorstore is not None:
                return True
            # Try a quick connect
            from qdrant_client import QdrantClient
            if self._settings.qdrant_url:
                client = QdrantClient(url=self._settings.qdrant_url)
            else:
                client = QdrantClient(path=self._settings.qdrant_path)
            client.get_collections()
            client.close()
            return True
        except Exception:
            return False

    def collection_count(self) -> int:
        """Return the number of points in the collection."""
        try:
            from qdrant_client import QdrantClient
            if self._settings.qdrant_url:
                client = QdrantClient(url=self._settings.qdrant_url)
            else:
                client = QdrantClient(path=self._settings.qdrant_path)
            info = client.get_collection(self._collection_name)
            count = info.points_count
            client.close()
            return count
        except Exception:
            return 0

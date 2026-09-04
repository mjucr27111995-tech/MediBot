"""Standalone ingestion script — run once before starting the server.

Parses all documents, chunks them with Docling HybridChunker,
and indexes into Qdrant with dense + BM25 sparse vectors.

Usage:
    cd MediBot/backend
    python -m scripts.ingest
"""

import sys
import time
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings
from app.ingestion import ingest_documents
from app.vector_store import VectorStore

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger(__name__)


def main() -> None:
    """Run the full ingestion pipeline."""
    logger.info("=== MediBot Document Ingestion ===")
    start = time.time()

    settings = load_settings()
    logger.info("config_loaded", data_dir=settings.data_dir)

    # Step 1: Parse and chunk documents
    logger.info("step1_ingesting_documents")
    documents = ingest_documents(
        data_dir=settings.data_dir,
        embed_model=settings.embed_model,
        max_chunk_tokens=settings.max_chunk_tokens,
    )
    logger.info("step1_complete", total_chunks=len(documents))

    collections = {}
    for doc in documents:
        col = doc.metadata.get("collection", "unknown")
        collections[col] = collections.get(col, 0) + 1
    for col, count in sorted(collections.items()):
        logger.info("collection_chunks", collection=col, count=count)

    # Step 2: Index into Qdrant with hybrid vectors
    # VectorStore.index_documents handles the Qdrant client internally
    logger.info("step2_indexing_to_qdrant")
    vs = VectorStore(settings)
    vs.index_documents(documents)

    elapsed = time.time() - start
    logger.info(
        "=== Ingestion Complete ===",
        total_chunks=len(documents),
        elapsed_seconds=round(elapsed, 1),
    )


if __name__ == "__main__":
    main()

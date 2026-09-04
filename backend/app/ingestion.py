"""Document ingestion pipeline using Docling for structural parsing.

Uses DocumentConverter for PDF/MD parsing and HybridChunker for
structure-aware chunking. Each chunk carries parent section heading as context.
"""

from pathlib import Path
from typing import List, Dict, Any

import structlog
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

from app.rbac import COLLECTION_ACCESS_ROLES

logger = structlog.get_logger(__name__)

COLLECTION_FOLDER_MAP: Dict[str, str] = {
    "general": "general",
    "clinical": "clinical",
    "nursing": "nursing",
    "billing": "billing",
    "equipment": "equipment",
}

SUPPORTED_EXTENSIONS = {".pdf", ".md"}


def _determine_chunk_type(chunk: Any) -> str:
    """Determine the type of a chunk based on its content and Docling metadata."""
    if hasattr(chunk, "meta") and hasattr(chunk.meta, "doc_items"):
        for item in chunk.meta.doc_items:
            label = str(getattr(item, "label", "")).lower()
            if "table" in label:
                return "table"
            if "heading" in label or "title" in label:
                return "heading"
            if "code" in label:
                return "code"

    text = chunk.text if hasattr(chunk, "text") else str(chunk)
    if text.strip().startswith("|") and "|" in text.strip()[1:]:
        return "table"
    if text.strip().startswith("```"):
        return "code"

    return "text"


def _extract_section_title(chunk: Any) -> str:
    """Extract the parent section heading from chunk metadata."""
    meta = chunk.meta if hasattr(chunk, "meta") else None
    headings = []

    if meta is not None:
        if isinstance(meta, dict):
            headings = meta.get("headings", [])
        elif hasattr(meta, "headings") and meta.headings:
            headings = meta.headings

    if headings:
        return str(headings[-1]).strip()
    return "General"


def ingest_documents(
    data_dir: str,
    embed_model: str,
    max_chunk_tokens: int = 512,
) -> List[Document]:
    """Parse all documents and return LangChain Documents with RBAC metadata.

    Uses Docling's HybridChunker with tokenizer aligned to embedding model.
    Each chunk's text is serialized with parent heading context via chunker.serialize().

    Args:
        data_dir: Path to the mediassist_data directory.
        embed_model: Embedding model name (for tokenizer alignment).
        max_chunk_tokens: Maximum tokens per chunk.

    Returns:
        List of LangChain Document objects with metadata:
            source_document, collection, access_roles, section_title, chunk_type
    """
    data_path = Path(data_dir)
    all_docs: List[Document] = []

    converter = DocumentConverter()
    chunker = HybridChunker(
        tokenizer=embed_model,
        max_tokens=max_chunk_tokens,
        merge_peers=True,
    )

    for collection_name, folder_name in COLLECTION_FOLDER_MAP.items():
        folder_path = data_path / folder_name
        if not folder_path.exists():
            logger.warning("collection_folder_missing", folder=str(folder_path))
            continue

        access_roles = COLLECTION_ACCESS_ROLES.get(collection_name, [])

        for file_path in sorted(folder_path.iterdir()):
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            logger.info(
                "ingesting_document",
                file=file_path.name,
                collection=collection_name,
            )

            try:
                result = converter.convert(str(file_path))
                doc = result.document

                chunks = list(chunker.chunk(doc))
                logger.info(
                    "document_chunked",
                    file=file_path.name,
                    num_chunks=len(chunks),
                )

                for chunk in chunks:
                    section_title = _extract_section_title(chunk)
                    chunk_type = _determine_chunk_type(chunk)

                    # chunker.serialize() prepends section heading to text
                    enriched_text = chunker.serialize(chunk=chunk)

                    doc_obj = Document(
                        page_content=enriched_text,
                        metadata={
                            "source_document": file_path.name,
                            "collection": collection_name,
                            "access_roles": access_roles,
                            "section_title": section_title,
                            "chunk_type": chunk_type,
                        },
                    )
                    all_docs.append(doc_obj)

            except Exception as exc:
                logger.error(
                    "ingestion_failed",
                    file=file_path.name,
                    error=str(exc),
                )
                raise

    logger.info("ingestion_complete", total_chunks=len(all_docs))
    return all_docs

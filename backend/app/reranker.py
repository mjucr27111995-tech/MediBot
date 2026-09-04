"""Cross-encoder reranking module.

Reranks initial hybrid retrieval results using a cross-encoder model that
scores each (query, chunk) pair jointly, then selects the top-N best.

Uses sentence-transformers CrossEncoder directly (no langchain_community dependency).
"""

from typing import List, Dict, Any

import structlog
from sentence_transformers import CrossEncoder

from app.config import Settings

logger = structlog.get_logger(__name__)


class Reranker:
    """Cross-encoder reranker that narrows a broad candidate set to top-N chunks."""

    def __init__(self, settings: Settings) -> None:
        self._model = CrossEncoder(settings.reranker_model)
        self._top_n = settings.reranker_top_n
        logger.info("reranker_loaded", model=settings.reranker_model)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Rerank candidates by cross-encoder relevance score.

        Scores each (query, candidate_text) pair jointly using the cross-encoder,
        then returns only the top-N highest-scoring chunks.
        """
        if not candidates:
            return []

        n = top_n or self._top_n

        pairs = [(query, c["text"]) for c in candidates]
        scores = self._model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)

        result_count = min(n, len(ranked))
        logger.info(
            "reranking_complete",
            input_count=len(candidates),
            output_count=result_count,
            top_score=ranked[0]["rerank_score"] if ranked else 0.0,
        )

        return ranked[:n]

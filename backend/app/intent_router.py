"""Semantic intent router — classifies questions as SQL RAG vs Hybrid RAG.

Uses the same sentence-transformers embedding model to compare the user's question
against example utterances via cosine similarity. Same concept as semantic-router
from Session 6, but without the external dependency (avoids numpy version conflicts).

Fast, local, no LLM call needed.
"""

from typing import List

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer

from app.config import Settings

logger = structlog.get_logger(__name__)

# Example utterances for SQL RAG — questions that need database analytics
SQL_RAG_EXAMPLES: List[str] = [
    "how many claims are currently pending",
    "what is the total claimed amount",
    "how many billing claims were rejected",
    "average claim amount by department",
    "which insurer has the most rejected claims",
    "count of claims by status",
    "total approved amount for cardiology",
    "how many maintenance tickets are open",
    "which equipment category has the most tickets",
    "number of maintenance tickets by campus",
    "how many tickets were raised last month",
    "average time to resolve maintenance tickets",
    "show me claims statistics",
    "what is the total pending claim amount",
    "which department has the highest claims",
    "how many cashless vs reimbursement claims",
    "equipment with most failures",
    "count of escalated claims",
    "breakdown of claims by insurer",
    "maintenance tickets by issue type",
]

# Example utterances for Hybrid RAG — questions that need document knowledge
HYBRID_RAG_EXAMPLES: List[str] = [
    "what is the treatment protocol for NSTEMI",
    "how do I submit a cashless claim",
    "what is the infection control procedure",
    "what are the leave policies",
    "tell me about the drug formulary",
    "what is the ICU nursing procedure for ventilated patients",
    "how to calibrate the ventilator",
    "what is the code of conduct",
    "explain the claim rejection process",
    "what are the billing codes for cardiac procedures",
    "what is the escalation matrix",
    "staff handbook rules about attendance",
    "diagnostic guidelines for chest pain",
    "equipment maintenance schedule",
    "what drugs are in the formulary for hypertension",
    "how to handle a pre-authorisation enhancement",
    "what is the fraud prevention policy",
    "nursing procedure for central line insertion",
    "general FAQs about the hospital",
    "what are the KPIs for billing executives",
]

SIMILARITY_THRESHOLD = 0.45


class IntentRouter:
    """Classifies questions using embedding similarity against example utterances.

    Same concept as semantic-router (Session 6) — encodes the question and
    compares against pre-encoded route examples using cosine similarity.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)

        # Pre-encode all example utterances (done once at startup)
        self._sql_embeddings = self._model.encode(SQL_RAG_EXAMPLES, normalize_embeddings=True)
        self._hybrid_embeddings = self._model.encode(HYBRID_RAG_EXAMPLES, normalize_embeddings=True)

        logger.info(
            "intent_router_built",
            sql_examples=len(SQL_RAG_EXAMPLES),
            hybrid_examples=len(HYBRID_RAG_EXAMPLES),
        )

    def classify(self, question: str) -> str:
        """Classify a question as 'sql_rag' or 'hybrid_rag'.

        Encodes the question, computes cosine similarity against both sets
        of example utterances, and picks the route with higher max similarity.

        Args:
            question: User's question text.

        Returns:
            "sql_rag" or "hybrid_rag"
        """
        query_embedding = self._model.encode(question, normalize_embeddings=True)

        # Cosine similarity = dot product (since embeddings are normalized)
        sql_scores = query_embedding @ self._sql_embeddings.T
        hybrid_scores = query_embedding @ self._hybrid_embeddings.T

        sql_max = float(np.max(sql_scores))
        hybrid_max = float(np.max(hybrid_scores))

        intent = "sql_rag" if sql_max > hybrid_max and sql_max > SIMILARITY_THRESHOLD else "hybrid_rag"

        logger.info(
            "intent_classified",
            intent=intent,
            sql_similarity=round(sql_max, 3),
            hybrid_similarity=round(hybrid_max, 3),
            question=question[:80],
        )

        return intent

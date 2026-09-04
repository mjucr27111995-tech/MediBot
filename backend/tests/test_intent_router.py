"""Tests for semantic intent router — SQL vs Hybrid RAG classification."""

import pytest

from app.intent_router import IntentRouter, SQL_RAG_EXAMPLES, HYBRID_RAG_EXAMPLES


@pytest.fixture(scope="module")
def router() -> IntentRouter:
    """Shared router instance (expensive to load, reuse across tests)."""
    return IntentRouter()


class TestIntentClassification:
    """Verify the semantic router correctly classifies questions."""

    @pytest.mark.parametrize("question", [
        "how many claims are currently pending",
        "what is the total claimed amount",
        "count of claims by status",
        "how many maintenance tickets are open",
        "average claim amount by department",
        "which insurer has the most rejected claims",
    ])
    def test_should_classifyAsSqlRag_withAnalyticalQuestions(
        self, router: IntentRouter, question: str
    ) -> None:
        assert router.classify(question) == "sql_rag"

    @pytest.mark.parametrize("question", [
        "what is the treatment protocol for NSTEMI",
        "how do I submit a cashless claim",
        "what is the infection control procedure",
        "tell me about the drug formulary",
        "what is the ICU nursing procedure for ventilated patients",
        "how to calibrate the ventilator",
    ])
    def test_should_classifyAsHybridRag_withKnowledgeQuestions(
        self, router: IntentRouter, question: str
    ) -> None:
        assert router.classify(question) == "hybrid_rag"

    def test_should_classifyAsHybridRag_withAmbiguousQuestion(
        self, router: IntentRouter
    ) -> None:
        """Ambiguous questions should default to hybrid_rag (safer fallback)."""
        result = router.classify("hello how are you")
        assert result == "hybrid_rag"

    def test_should_haveEnoughExamples_forBothRoutes(self) -> None:
        assert len(SQL_RAG_EXAMPLES) >= 10
        assert len(HYBRID_RAG_EXAMPLES) >= 10

    def test_should_returnOnlyValidIntents(
        self, router: IntentRouter
    ) -> None:
        result = router.classify("random question about anything")
        assert result in ("sql_rag", "hybrid_rag")

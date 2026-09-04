"""Tests for SQL RAG _clean_sql() sanitization function."""

import pytest

from app.sql_rag import _clean_sql


class TestCleanSQL:
    """Verify SQL extraction from various LLM output formats."""

    def test_should_extractSQL_fromMarkdownFences(self) -> None:
        raw = "```sql\nSELECT COUNT(*) FROM claims WHERE status = 'pending'\n```"
        result = _clean_sql(raw)
        assert result == "SELECT COUNT(*) FROM claims WHERE status = 'pending'"

    def test_should_extractSQL_fromFencesWithoutLanguageTag(self) -> None:
        raw = "```\nSELECT * FROM claims\n```"
        result = _clean_sql(raw)
        assert result == "SELECT * FROM claims"

    def test_should_extractSQL_fromSQLQueryPrefix(self) -> None:
        raw = "SQLQuery: SELECT COUNT(*) FROM claims"
        result = _clean_sql(raw)
        assert result == "SELECT COUNT(*) FROM claims"

    def test_should_extractSQL_fromLeadingExplanation(self) -> None:
        raw = (
            "I'll write a query to count pending claims.\n"
            "SELECT COUNT(*) FROM claims WHERE status = 'pending'"
        )
        result = _clean_sql(raw)
        assert "SELECT COUNT(*)" in result
        assert "pending" in result

    def test_should_handleCleanSQL_withNoWrapper(self) -> None:
        raw = "SELECT department, AVG(claimed_amount) FROM claims GROUP BY department"
        result = _clean_sql(raw)
        assert "SELECT department" in result
        assert "GROUP BY department" in result

    def test_should_handleWITH_cteQueries(self) -> None:
        raw = "WITH dept_claims AS (SELECT * FROM claims) SELECT * FROM dept_claims"
        result = _clean_sql(raw)
        assert result.startswith("WITH")

    def test_should_stripWhitespace(self) -> None:
        raw = "   SELECT 1   "
        result = _clean_sql(raw)
        assert result == "SELECT 1"

    def test_should_handleMultilineSQL_inFences(self) -> None:
        raw = """```sql
SELECT
    department,
    COUNT(*) as cnt
FROM claims
WHERE status = 'pending'
GROUP BY department
```"""
        result = _clean_sql(raw)
        assert "SELECT" in result
        assert "GROUP BY department" in result

    def test_should_handleSQLQuery_withMultiplePrefixes(self) -> None:
        raw = "Here is the query:\nSQLQuery: SELECT * FROM maintenance_tickets"
        result = _clean_sql(raw)
        assert result == "SELECT * FROM maintenance_tickets"

    def test_should_handleEmptyString(self) -> None:
        result = _clean_sql("")
        assert result == ""

    def test_should_removeCommentLines(self) -> None:
        raw = "SELECT COUNT(*)\n-- this is a comment\nFROM claims"
        result = _clean_sql(raw)
        assert "--" not in result
        assert "SELECT COUNT(*)" in result

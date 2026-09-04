"""SQL RAG chain — translates natural language to SQL, executes, and produces NL answer.

Follows the cohort pattern: create_sql_query_chain → clean SQL → execute → LLM answer.
Only available to billing_executive and admin roles.
"""

import re
from typing import Optional

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate

from app.config import Settings

logger = structlog.get_logger(__name__)

ANSWER_SYSTEM_PROMPT = """You are a helpful healthcare data analyst at MediAssist Health Network.
Given a user's question, the SQL query that was generated, and its results from the hospital database,
provide a clear, concise natural language answer.

Rules:
- Include relevant numbers, counts, and specifics from the result.
- Format currency values in INR (₹) when applicable.
- If the result is empty, say so clearly and suggest rephrasing.
- Be professional and precise — this is healthcare operational data.
- Do not expose raw SQL or database internals to the user."""


def _clean_sql(raw: str) -> str:
    """Strip markdown fences, preamble text, and extract only the SQL statement.

    LLMs sometimes return SQL wrapped in markdown code fences or prefixed
    with explanation text. This function extracts just the SQL statement.
    """
    # Handle markdown code fences
    fenced = re.search(r"```(?:sql)?\s*\n?(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    # Handle "SQLQuery: ..." prefix from LangChain's create_sql_query_chain
    if "SQLQuery:" in raw:
        raw = raw.split("SQLQuery:")[-1].strip()

    # Strip leading explanation text — find first SQL keyword
    lines = raw.strip().split("\n")
    sql_lines = []
    found_sql = False
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if not found_sql and upper.startswith(
            ("SELECT", "WITH", "INSERT", "UPDATE", "DELETE")
        ):
            found_sql = True
        if found_sql:
            if stripped.startswith("--") or not stripped:
                continue
            sql_lines.append(stripped)

    if sql_lines:
        return " ".join(sql_lines)

    return raw.strip()


def sql_rag_chain(question: str, settings: Optional[Settings] = None) -> str:
    """Translate a natural language question to SQL, execute it, and return a NL answer.

    This is the plain Python function required by the assignment with three explicit steps:
    1. Translate the NL question into SQL using an LLM
    2. Clean the raw LLM output to extract only the SQL statement
    3. Execute the SQL and pass the result back to the LLM for a NL answer

    Args:
        question: Natural language question about claims or maintenance data.
        settings: Application settings (uses load_settings() if not provided).

    Returns:
        Natural language answer string.
    """
    if settings is None:
        from app.config import load_settings
        settings = load_settings()

    # Set up LLM and database connection
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )

    db = SQLDatabase.from_uri(f"sqlite:///{settings.sqlite_db_path}")

    # Step 1: Generate SQL using LangChain's create_sql_query_chain
    sql_query_chain = create_sql_query_chain(llm, db)

    logger.info("sql_rag_step1_generating_sql", question=question)
    raw_sql_response = sql_query_chain.invoke({"question": question})
    # Handle list responses from newer Gemini models
    if isinstance(raw_sql_response, list):
        parts = []
        for part in raw_sql_response:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
            else:
                parts.append(str(part))
        raw_sql = " ".join(parts)
    else:
        raw_sql = str(raw_sql_response)
    logger.info("sql_rag_raw_llm_output", raw=raw_sql)

    # Step 2: Clean the raw LLM output — extract only the SQL statement
    sql_query = _clean_sql(raw_sql)
    logger.info("sql_rag_step2_cleaned_sql", sql=sql_query)

    if not sql_query or not any(
        kw in sql_query.upper() for kw in ["SELECT", "WITH"]
    ):
        return (
            "I couldn't generate a valid SQL query for that question. "
            "Please try rephrasing it."
        )

    # Step 3: Execute SQL and generate NL answer
    try:
        result = db.run(sql_query)
        logger.info("sql_rag_step3_executed", result_preview=str(result)[:200])
    except Exception as exc:
        logger.error("sql_execution_failed", error=str(exc), sql=sql_query)
        return (
            f"I generated a query but it failed to execute. "
            f"Please try rephrasing your question. (Error: {exc})"
        )

    # Generate natural language answer from results
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", ANSWER_SYSTEM_PROMPT),
        (
            "human",
            "Question: {question}\n\nSQL Query: {sql_query}\n\nQuery Result: {result}\n\nProvide a clear answer:",
        ),
    ])

    answer_chain = answer_prompt | llm
    response = answer_chain.invoke({
        "question": question,
        "sql_query": sql_query,
        "result": str(result),
    })
    # Handle both string and list responses from different Gemini models
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
            else:
                text_parts.append(str(part))
        answer = " ".join(text_parts).strip()
    else:
        answer = content.strip()
    logger.info("sql_rag_complete", answer_length=len(answer))

    return answer

from app.state import AgentState
from app.llm import llm
from app.tools import (
    get_tables,
    get_table_schema,
    get_relationships,
)
from app.database import engine
from sqlalchemy import text


def generate_sql_node(state: AgentState) -> AgentState:
    question = state["question"]

    tables = get_tables()
    relationships = get_relationships()

    schema_parts = []

    for table in tables:
        schema = get_table_schema(table)

        columns = ", ".join(
            f"{column['column']} ({column['type']})" for column in schema
        )

        schema_parts.append(f"Table: {table}\nColumns: {columns}")

    schema_text = "\n\n".join(schema_parts)

    relationship_text = "\n".join(
        f"{r['table']}.{r['column']} -> "
        f"{r['references_table']}.{r['references_column']}"
        for r in relationships
    )

    prompt = f"""
You are an expert SQL Server data analyst.

Generate ONE SQL Server SELECT query that answers the user's question.

IMPORTANT SQL SERVER RULES:
- Generate SQL Server / T-SQL syntax only.
- SELECT statements only.
- NEVER use LIMIT.
- NEVER use MySQL or PostgreSQL syntax.
- When using multiple tables, always use table aliases and qualify every column with its table alias.
- To return the first N rows, use TOP N immediately after SELECT.
- Correct example:
  SELECT TOP 5 ProductName FROM Products ORDER BY ProductName
- Incorrect example:
  SELECT ProductName FROM Products ORDER BY ProductName LIMIT 5
- Incorrect example:
  SELECT ProductName FROM Products ORDER BY ProductName TOP 5
- Use only tables and columns provided in the schema.
- Respect exact table and column names.
- "Order Details" is NOT the same as "OrderDetails".
- If a table or column name contains spaces or special characters,
  wrap it in square brackets.
- Example: [Order Details]
- Do not invent tables or columns.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
  TRUNCATE, CREATE, EXEC, or MERGE.
- Return ONLY the SQL query.
- Do not use markdown code fences.

DATABASE SCHEMA:

{schema_text}

RELATIONSHIPS:

{relationship_text}

USER QUESTION:

{question}
"""

    response = llm.invoke(prompt)

    sql = response.content.strip()

    return {
        **state,
        "sql": sql,
        "retry_count": state.get("retry_count", 0),
    }


def validate_sql_node(state: AgentState) -> AgentState:
    sql = state.get("sql", "").strip()

    if not sql:
        return {
            **state,
            "sql_valid": False,
            "sql_error": "No SQL query was generated.",
        }

    normalized_sql = sql.upper()

    if "LIMIT" in normalized_sql:
        return {
            **state,
            "sql_valid": False,
            "sql_error": "SQL Server does not support LIMIT. Use TOP N immediately after SELECT.",
        }

    if "TOP " in normalized_sql and "ORDER BY" in normalized_sql:
        top_position = normalized_sql.find("TOP ")
        order_by_position = normalized_sql.find("ORDER BY")

        if top_position > order_by_position:
            return {
                **state,
                "sql_valid": False,
                "sql_error": (
                    "Invalid SQL Server syntax: TOP N must appear immediately "
                    "after SELECT, before the selected columns."
                ),
            }

    forbidden_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "EXEC",
        "EXECUTE",
        "MERGE",
    ]

    for keyword in forbidden_keywords:
        if keyword in normalized_sql:
            return {
                **state,
                "sql_valid": False,
                "sql_error": (f"Potentially destructive SQL detected: {keyword}"),
            }

    if not normalized_sql.startswith("SELECT"):
        return {
            **state,
            "sql_valid": False,
            "sql_error": "Only SELECT statements are allowed.",
        }

    return {
        **state,
        "sql_valid": True,
        "sql_error": "",
    }


def execute_sql_node(state: AgentState) -> AgentState:
    if not state.get("sql_valid", False):
        return {
            **state,
            "query_result": [],
        }

    sql = state["sql"]

    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql))

            rows = result.mappings().all()

            query_result = [dict(row) for row in rows]

        return {
            **state,
            "query_result": query_result,
            "sql_error": "",
        }

    except Exception as exc:
        return {
            **state,
            "query_result": [],
            "sql_error": str(exc),
        }


def self_correct_sql_node(state: AgentState) -> AgentState:
    question = state["question"]
    sql = state.get("sql", "")
    sql_error = state.get("sql_error", "")

    retry_count = state.get("retry_count", 0) + 1

    tables = get_tables()
    relationships = get_relationships()

    schema_parts = []

    for table in tables:
        schema = get_table_schema(table)

        columns = ", ".join(
            f"{column['column']} ({column['type']})" for column in schema
        )

        schema_parts.append(f"Table: {table}\nColumns: {columns}")

    schema_text = "\n\n".join(schema_parts)

    relationship_text = "\n".join(
        f"{r['table']}.{r['column']} -> "
        f"{r['references_table']}.{r['references_column']}"
        for r in relationships
    )

    prompt = f"""
You are a SQL Server expert correcting a failed SQL query.

USER QUESTION:
{question}

PREVIOUS SQL:
{sql}

DATABASE ERROR:
{sql_error}

DATABASE SCHEMA:
{schema_text}

RELATIONSHIPS:
{relationship_text}

TASK:
The PREVIOUS SQL failed when executed by SQL Server.

You MUST generate a corrected version of the PREVIOUS SQL that:
1. Answers the original USER QUESTION.
2. Fixes the exact DATABASE ERROR.
3. Is different from the PREVIOUS SQL if the previous SQL contains an error.
4. Uses only tables and columns from the provided schema.

SQL SERVER RULES:
- Generate SQL Server syntax only.
- Generate SELECT statements only.
- If limiting rows with TOP N, TOP N MUST appear immediately after SELECT.
- When using multiple tables, always use table aliases and qualify every column with its table alias.
- NEVER put TOP N after ORDER BY.
- Do not use LIMIT.
- SQL Server uses TOP for limiting rows.
- Respect the exact table and column names.
- Do not invent tables or columns.
- Do not generate INSERT, UPDATE, DELETE, DROP, ALTER,
  TRUNCATE, CREATE, EXEC, or MERGE.

IMPORTANT:
- The database schema is the source of truth.
- Table names must match the schema EXACTLY.
- "Order Details" is the actual table name.
- "OrderDetails" does NOT exist.
- When a table or column name contains spaces, use SQL Server square brackets.
- Example: [Order Details]
- Never remove spaces from table names.
- Never create a new table name by combining words.
- The previous SQL has already FAILED.
- Do NOT simply repeat the previous SQL.
- You MUST fix the error reported by SQL Server.

Return ONLY the corrected SQL.
Do not use markdown code fences.
"""

    print("========== SELF CORRECTION INPUT ==========")
    print("Question:", question)
    print("Previous SQL:")
    print(sql)
    print("SQL Error:")
    print(sql_error)
    print("============================================")

    print("Starting SQL self-correction...")
    response = llm.invoke(prompt)
    print("LLM response received.")

    corrected_sql = response.content.strip()

    print("Corrected SQL:")
    print(corrected_sql)
    print("------------------------")

    return {
        **state,
        "sql": corrected_sql,
        "sql_error": "",
        "sql_valid": False,
        "retry_count": retry_count,
    }


def answer_node(state: AgentState) -> AgentState:
    question = state["question"]
    query_result = state.get("query_result", [])

    prompt = f"""
You are a data analyst assistant.

Answer the user's question using ONLY the query result provided below.

USER QUESTION:
{question}

QUERY RESULT:
{query_result}

RULES:
- Answer in clear, natural language.
- Do not invent facts that are not present in the query result.
- Mention important values from the result when appropriate.
- If multiple rows are present, summarize them clearly.
- Keep the answer concise.
- Do not generate SQL.
- Return ONLY the final answer to the user.
"""

    response = llm.invoke(prompt)

    answer = response.content.strip()

    return {
        **state,
        "answer": answer,
    }

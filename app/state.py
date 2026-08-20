from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):
    question: str
    sql: str
    sql_valid: bool
    sql_error: str
    query_result: List[Dict[str, Any]]
    final_answer: str
    retry_count: int

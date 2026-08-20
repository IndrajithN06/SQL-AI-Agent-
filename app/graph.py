from langgraph.graph import StateGraph, START, END

from app.state import AgentState
from app.nodes import (
    generate_sql_node,
    validate_sql_node,
    execute_sql_node,
    self_correct_sql_node,
)


def route_after_execution(state: AgentState):
    if state.get("sql_error"):
        if state.get("retry_count", 0) >= 3:
            return "failure"

        return "self_correct"

    return "success"


def route_after_validation(state: AgentState):
    retry_count = state.get("retry_count", 0)

    if retry_count >= 3:
        return "failure"

    if not state.get("sql_valid", False):
        return "self_correct"

    return "execute"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("self_correct", self_correct_sql_node)

    graph.add_edge(START, "generate_sql")

    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "self_correct": "self_correct",
            "execute": "execute_sql",
            "failure": END,
        },
    )

    graph.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "self_correct": "self_correct",
            "success": END,
            "failure": END,
        },
    )

    graph.add_edge("self_correct", "validate_sql")

    return graph.compile()

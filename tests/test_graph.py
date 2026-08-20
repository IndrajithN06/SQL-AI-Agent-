from app.graph import build_graph

graph = build_graph()


initial_state = {
    "question": "What are the top 5 products by sales?",
    "retry_count": 0,
}


result = graph.invoke(initial_state)


print("\n========== FINAL STATE ==========\n")

print("Question:")
print(result.get("question"))

print("\nGenerated SQL:")
print(result.get("sql"))

print("\nSQL Valid:")
print(result.get("sql_valid"))

print("\nSQL Error:")
print(result.get("sql_error"))

print("\nQuery Result:")
for row in result.get("query_result", []):
    print(row)

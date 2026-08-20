from app.nodes import generate_sql_node

state = {
    "question": "What are the top 5 products by sales?",
    "retry_count": 0,
}

result = generate_sql_node(state)

print("\nGenerated SQL:\n")
print(result["sql"])

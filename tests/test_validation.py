from app.nodes import validate_sql_node

safe_state = {
    "question": "Show all customers",
    "sql": "SELECT TOP 10 * FROM Customers",
}

safe_result = validate_sql_node(safe_state)

print("SAFE QUERY")
print(safe_result)


dangerous_state = {
    "question": "Delete all customers",
    "sql": "DELETE FROM Customers",
}

dangerous_result = validate_sql_node(dangerous_state)

print("\nDANGEROUS QUERY")
print(dangerous_result)

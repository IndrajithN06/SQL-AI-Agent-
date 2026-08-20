from app.nodes import (
    validate_sql_node,
    execute_sql_node,
)

state = {
    "question": "Show the first 5 customers",
    "sql": """
        SELECT TOP 5
            CustomerID,
            CompanyName,
            Country
        FROM Customers
    """,
    "retry_count": 0,
}

state = validate_sql_node(state)

print("After validation:")
print(state)

state = execute_sql_node(state)

print("\nAfter execution:")
print(state)

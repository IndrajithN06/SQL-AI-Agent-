from app.nodes import (
    validate_sql_node,
    execute_sql_node,
)

state = {
    "question": "What are the top 5 products by sales?",
    "sql": """
        SELECT p.ProductName,
               SUM(od.Quantity * od.UnitPrice) AS TotalSales
        FROM Products p
        JOIN Order_Details od
            ON p.ProductID = od.ProductID
        GROUP BY p.ProductName
        ORDER BY TotalSales DESC
        LIMIT 5
    """,
    "retry_count": 0,
}

print("GENERATED SQL:")
print(state["sql"])

state = validate_sql_node(state)

print("\nVALIDATION:")
print(state["sql_valid"])

state = execute_sql_node(state)

print("\nEXECUTION ERROR:")
print(state.get("sql_error"))

print("\nRESULT:")
print(state.get("query_result"))

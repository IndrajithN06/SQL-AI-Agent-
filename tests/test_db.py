from app.tools import get_tables
from app.tools import get_table_schema

tables = get_tables()

print("\n========== TABLES ==========")
for table in tables:
    print(f"'{table}'")
print("============================")

print("\n========== PRODUCTS SCHEMA ==========")
for column in get_table_schema("Products"):
    print(column)

print("\n========== ORDER DETAILS SCHEMA ==========")
for column in get_table_schema("Order Details"):
    print(column)

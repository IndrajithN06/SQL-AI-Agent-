from sqlalchemy import text
from app.database import engine


def get_tables():
    query = """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """

    with engine.connect() as conn:
        result = conn.execute(text(query))

        return [row[0] for row in result]


def get_table_schema(table_name: str):
    query = """
    SELECT
        COLUMN_NAME,
        DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = :table_name
    ORDER BY ORDINAL_POSITION
    """

    with engine.connect() as conn:
        result = conn.execute(text(query), {"table_name": table_name})

        return [{"column": row.COLUMN_NAME, "type": row.DATA_TYPE} for row in result]


def get_relationships():
    query = """
    SELECT
        fk.name AS FK_Name,
        tp.name AS ParentTable,
        cp.name AS ParentColumn,
        tr.name AS ReferencedTable,
        cr.name AS ReferencedColumn
    FROM sys.foreign_keys fk
    INNER JOIN sys.foreign_key_columns fkc
        ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables tp
        ON fkc.parent_object_id = tp.object_id
    INNER JOIN sys.columns cp
        ON fkc.parent_object_id = cp.object_id
        AND fkc.parent_column_id = cp.column_id
    INNER JOIN sys.tables tr
        ON fkc.referenced_object_id = tr.object_id
    INNER JOIN sys.columns cr
        ON fkc.referenced_object_id = cr.object_id
        AND fkc.referenced_column_id = cr.column_id
    ORDER BY tp.name
    """

    with engine.connect() as conn:
        result = conn.execute(text(query))

        return [
            {
                "table": row.ParentTable,
                "column": row.ParentColumn,
                "references_table": row.ReferencedTable,
                "references_column": row.ReferencedColumn,
            }
            for row in result
        ]

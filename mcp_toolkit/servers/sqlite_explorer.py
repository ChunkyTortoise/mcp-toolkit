"""SQLite database CRUD operations and schema introspection MCP server."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastmcp import FastMCP

SERVER_INFO = {
    "name": "sqlite-explorer",
    "description": "SQLite database CRUD operations and schema introspection",
    "tools": ["create_database", "query", "insert", "update", "delete", "get_schema"],
}

mcp = FastMCP(SERVER_INFO["name"])


def _resolve_db_path(db: str) -> str:
    """Resolve a database name or path to an absolute path.

    If ``db`` is a bare name (no path separators), the database is placed
    under ``/tmp/``.  Otherwise the path is used as-is.
    """
    path = Path(db)
    if path.parent == Path("."):
        path = Path("/tmp") / db
    if not path.suffix:
        path = path.with_suffix(".db")
    return str(path)


def _connect(db: str) -> sqlite3.Connection:
    """Open a connection to the resolved database path with row-factory."""
    conn = sqlite3.connect(_resolve_db_path(db))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_database(name: str, tables: dict[str, dict[str, str]]) -> str:
    """Create a SQLite database with the given tables.

    Args:
        name: Database file name (created in /tmp/ by default).
        tables: Mapping of ``{table_name: {column_name: column_type}}``.

    Returns:
        Confirmation message with the database path and tables created.
    """
    db_path = _resolve_db_path(name)
    conn = sqlite3.connect(db_path)
    try:
        for table_name, columns in tables.items():
            col_defs = ", ".join(f"{col_name} {col_type}" for col_name, col_type in columns.items())
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})")
        conn.commit()
    finally:
        conn.close()

    table_names = ", ".join(tables.keys())
    return f"Database created at {db_path} with tables: {table_names}"


@mcp.tool()
def query(db: str, sql: str, params: list | None = None) -> list[dict]:
    """Execute a parameterized SELECT query and return results as dicts.

    Only SELECT statements are allowed.  Any other statement type is
    rejected to prevent unintended mutations.

    Args:
        db: Database file name or path.
        sql: A SELECT SQL statement.
        params: Optional list of bind parameters.

    Returns:
        List of row dictionaries.

    Raises:
        ValueError: If the SQL statement is not a SELECT.
    """
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise ValueError(
            "Only SELECT queries are allowed. Use insert/update/delete tools for mutations."
        )

    conn = _connect(db)
    try:
        cursor = conn.execute(sql, params or [])
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def insert(db: str, table: str, data: dict) -> str:
    """Insert a single row into a table.

    Args:
        db: Database file name or path.
        table: Target table name.
        data: Mapping of ``{column_name: value}`` for the new row.

    Returns:
        Confirmation message with the new row's rowid.
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    conn = _connect(db)
    try:
        cursor = conn.execute(sql, list(data.values()))
        conn.commit()
        return f"Inserted row into {table} with rowid {cursor.lastrowid}"
    finally:
        conn.close()


@mcp.tool()
def update(
    db: str,
    table: str,
    data: dict,
    where: str,
    where_params: list | None = None,
) -> str:
    """Update rows in a table matching the WHERE clause.

    Args:
        db: Database file name or path.
        table: Target table name.
        data: Mapping of ``{column_name: new_value}`` to set.
        where: SQL WHERE clause (without the ``WHERE`` keyword).
        where_params: Optional bind parameters for the WHERE clause.

    Returns:
        Confirmation with the number of rows affected.
    """
    set_clause = ", ".join(f"{col} = ?" for col in data)
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
    params = list(data.values()) + (where_params or [])

    conn = _connect(db)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return f"Updated {cursor.rowcount} row(s) in {table}"
    finally:
        conn.close()


@mcp.tool()
def delete(
    db: str,
    table: str,
    where: str,
    where_params: list | None = None,
) -> str:
    """Delete rows from a table matching the WHERE clause.

    Args:
        db: Database file name or path.
        table: Target table name.
        where: SQL WHERE clause (without the ``WHERE`` keyword).
        where_params: Optional bind parameters for the WHERE clause.

    Returns:
        Confirmation with the number of rows affected.
    """
    sql = f"DELETE FROM {table} WHERE {where}"

    conn = _connect(db)
    try:
        cursor = conn.execute(sql, where_params or [])
        conn.commit()
        return f"Deleted {cursor.rowcount} row(s) from {table}"
    finally:
        conn.close()


@mcp.tool()
def get_schema(db: str) -> dict:
    """Introspect all tables, columns, and types in the database.

    Uses ``sqlite_master`` to discover tables and ``PRAGMA table_info``
    to retrieve column details for each one.

    Args:
        db: Database file name or path.

    Returns:
        Dict mapping each table name to a list of column descriptors,
        each containing ``name``, ``type``, ``notnull``, ``default``,
        and ``pk`` fields.
    """
    conn = _connect(db)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row["name"] for row in cursor.fetchall()]

        schema: dict[str, list[dict]] = {}
        for table in tables:
            cols_cursor = conn.execute(f"PRAGMA table_info({table})")
            schema[table] = [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "notnull": bool(col["notnull"]),
                    "default": col["dflt_value"],
                    "pk": bool(col["pk"]),
                }
                for col in cols_cursor.fetchall()
            ]

        return schema
    finally:
        conn.close()

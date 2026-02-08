"""Tests for the sqlite_explorer MCP server."""

from __future__ import annotations

import pytest

from mcp_toolkit.servers.sqlite_explorer import (
    create_database,
    delete,
    get_schema,
    insert,
    query,
    update,
)


class TestCreateDatabase:
    def test_create_database(self, tmp_dir):
        """Creates a DB with 2 tables and verifies the file exists."""
        db_path = str(tmp_dir / "multi.db")
        result = create_database.fn(
            name=db_path,
            tables={
                "users": {"id": "INTEGER PRIMARY KEY", "name": "TEXT"},
                "orders": {"id": "INTEGER PRIMARY KEY", "user_id": "INTEGER", "total": "REAL"},
            },
        )
        assert "users" in result
        assert "orders" in result
        assert (tmp_dir / "multi.db").exists()


class TestInsertAndQuery:
    def test_insert_and_query(self, tmp_dir):
        """Inserts rows then queries them back."""
        db_path = str(tmp_dir / "iq.db")
        create_database.fn(
            name=db_path,
            tables={"books": {"id": "INTEGER PRIMARY KEY", "title": "TEXT", "pages": "INTEGER"}},
        )
        insert.fn(db=db_path, table="books", data={"title": "Dune", "pages": 412})
        insert.fn(db=db_path, table="books", data={"title": "Neuromancer", "pages": 271})

        rows = query.fn(db=db_path, sql="SELECT title, pages FROM books ORDER BY title")
        assert len(rows) == 2
        assert rows[0]["title"] == "Dune"
        assert rows[1]["title"] == "Neuromancer"

    def test_query_with_params(self, tmp_dir):
        """Parameterized SELECT with WHERE clause."""
        db_path = str(tmp_dir / "params.db")
        create_database.fn(
            name=db_path,
            tables={"items": {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "qty": "INTEGER"}},
        )
        insert.fn(db=db_path, table="items", data={"name": "Bolt", "qty": 100})
        insert.fn(db=db_path, table="items", data={"name": "Nut", "qty": 50})
        insert.fn(db=db_path, table="items", data={"name": "Washer", "qty": 200})

        rows = query.fn(db=db_path, sql="SELECT name FROM items WHERE qty > ?", params=[75])
        names = {r["name"] for r in rows}
        assert names == {"Bolt", "Washer"}

    def test_query_rejects_non_select(self, tmp_dir):
        """DROP/INSERT via query() raises ValueError."""
        db_path = str(tmp_dir / "reject.db")
        create_database.fn(
            name=db_path,
            tables={"t": {"id": "INTEGER PRIMARY KEY"}},
        )
        with pytest.raises(ValueError, match="Only SELECT"):
            query.fn(db=db_path, sql="DROP TABLE t")

        with pytest.raises(ValueError, match="Only SELECT"):
            query.fn(db=db_path, sql="INSERT INTO t (id) VALUES (1)")

    def test_query_empty_table(self, tmp_dir):
        """Query on an empty table returns an empty list."""
        db_path = str(tmp_dir / "empty.db")
        create_database.fn(
            name=db_path,
            tables={"empty_tbl": {"id": "INTEGER PRIMARY KEY", "val": "TEXT"}},
        )
        rows = query.fn(db=db_path, sql="SELECT * FROM empty_tbl")
        assert rows == []


class TestUpdateAndDelete:
    def test_update_rows(self, tmp_dir):
        """Updates a row and verifies the change."""
        db_path = str(tmp_dir / "upd.db")
        create_database.fn(
            name=db_path,
            tables={"staff": {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "role": "TEXT"}},
        )
        insert.fn(db=db_path, table="staff", data={"name": "Alice", "role": "dev"})
        insert.fn(db=db_path, table="staff", data={"name": "Bob", "role": "dev"})

        result = update.fn(
            db=db_path,
            table="staff",
            data={"role": "lead"},
            where="name = ?",
            where_params=["Alice"],
        )
        assert "1 row(s)" in result

        rows = query.fn(db=db_path, sql="SELECT role FROM staff WHERE name = 'Alice'")
        assert rows[0]["role"] == "lead"

    def test_delete_rows(self, tmp_dir):
        """Deletes a row and verifies it is gone."""
        db_path = str(tmp_dir / "del.db")
        create_database.fn(
            name=db_path,
            tables={"colors": {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}},
        )
        insert.fn(db=db_path, table="colors", data={"name": "red"})
        insert.fn(db=db_path, table="colors", data={"name": "blue"})

        result = delete.fn(db=db_path, table="colors", where="name = ?", where_params=["red"])
        assert "1 row(s)" in result

        rows = query.fn(db=db_path, sql="SELECT name FROM colors")
        assert len(rows) == 1
        assert rows[0]["name"] == "blue"

    def test_update_no_match(self, tmp_dir):
        """Update where nothing matches returns '0 row(s)'."""
        db_path = str(tmp_dir / "nomatch_u.db")
        create_database.fn(
            name=db_path,
            tables={"things": {"id": "INTEGER PRIMARY KEY", "label": "TEXT"}},
        )
        insert.fn(db=db_path, table="things", data={"label": "alpha"})

        result = update.fn(
            db=db_path,
            table="things",
            data={"label": "beta"},
            where="label = ?",
            where_params=["nonexistent"],
        )
        assert "0 row(s)" in result

    def test_delete_no_match(self, tmp_dir):
        """Delete where nothing matches returns '0 row(s)'."""
        db_path = str(tmp_dir / "nomatch_d.db")
        create_database.fn(
            name=db_path,
            tables={"things": {"id": "INTEGER PRIMARY KEY", "label": "TEXT"}},
        )
        insert.fn(db=db_path, table="things", data={"label": "alpha"})

        result = delete.fn(
            db=db_path,
            table="things",
            where="label = ?",
            where_params=["nonexistent"],
        )
        assert "0 row(s)" in result


class TestSchemaAndRowid:
    def test_insert_returns_rowid(self, tmp_dir):
        """Verifies 'rowid' appears in the insert return string."""
        db_path = str(tmp_dir / "rowid.db")
        create_database.fn(
            name=db_path,
            tables={"nums": {"id": "INTEGER PRIMARY KEY", "val": "INTEGER"}},
        )
        result = insert.fn(db=db_path, table="nums", data={"val": 42})
        assert "rowid" in result

    def test_get_schema(self, tmp_dir):
        """Creates a DB with a known schema and checks structure."""
        db_path = str(tmp_dir / "schema.db")
        create_database.fn(
            name=db_path,
            tables={
                "people": {"id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL", "age": "INTEGER"}
            },
        )
        schema = get_schema.fn(db=db_path)
        assert "people" in schema
        col_names = [c["name"] for c in schema["people"]]
        assert "id" in col_names
        assert "name" in col_names
        assert "age" in col_names

    def test_schema_multiple_tables(self, tmp_dir):
        """Schema with 2+ tables returns all tables."""
        db_path = str(tmp_dir / "multi_schema.db")
        create_database.fn(
            name=db_path,
            tables={
                "accounts": {"id": "INTEGER PRIMARY KEY", "email": "TEXT"},
                "sessions": {"id": "INTEGER PRIMARY KEY", "token": "TEXT"},
                "logs": {"id": "INTEGER PRIMARY KEY", "message": "TEXT"},
            },
        )
        schema = get_schema.fn(db=db_path)
        assert set(schema.keys()) == {"accounts", "sessions", "logs"}
        for table_cols in schema.values():
            assert len(table_cols) >= 2

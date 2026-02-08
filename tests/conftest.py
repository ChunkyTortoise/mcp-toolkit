"""Shared test fixtures for mcp-toolkit."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def demo_data_dir():
    """Return path to the demo_data directory."""
    return Path(__file__).parent.parent / "demo_data"


@pytest.fixture
def demo_docs_dir():
    """Return path to the demo_docs directory."""
    return Path(__file__).parent.parent / "demo_docs"


@pytest.fixture
def sample_db(tmp_dir):
    """Create a sample SQLite database for testing."""
    import sqlite3

    db_path = str(tmp_dir / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL)")
    conn.execute("INSERT INTO products (name, price) VALUES ('Widget', 9.99)")
    conn.execute("INSERT INTO products (name, price) VALUES ('Gadget', 19.99)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_tasks_file(tmp_dir):
    """Provide a temporary tasks file path and set env override."""
    tasks_path = tmp_dir / "tasks.json"
    os.environ["MCP_TOOLKIT_TASKS_FILE"] = str(tasks_path)
    yield tasks_path
    os.environ.pop("MCP_TOOLKIT_TASKS_FILE", None)


@pytest.fixture
def sample_markdown_dir(tmp_dir):
    """Create a directory with sample markdown files."""
    docs = {
        "intro.md": "# Introduction\n\nWelcome to the project documentation.",
        "setup.md": "# Setup Guide\n\nInstall dependencies with pip install.",
        "api.md": "# API Reference\n\nThe REST API supports CRUD operations.",
    }
    for name, content in docs.items():
        (tmp_dir / name).write_text(content)
    return tmp_dir

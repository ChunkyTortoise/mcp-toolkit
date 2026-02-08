"""Demo data setup for Streamlit Cloud deployment.

Creates ephemeral demo resources (git repo, SQLite DB, sample tasks)
so every MCP server has working data on first launch.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

DEMO_ROOT = Path("/tmp/mcp-demo")
DEMO_GIT_REPO = DEMO_ROOT / "sample-repo"
DEMO_DB = DEMO_ROOT / "demo.db"
DEMO_TASKS = DEMO_ROOT / "tasks.json"


def _is_setup_done() -> bool:
    return DEMO_GIT_REPO.exists() and DEMO_DB.exists() and DEMO_TASKS.exists()


def setup_demo_environment() -> dict[str, str]:
    """Provision all demo resources and return path hints for the UI.

    Returns a mapping of server-name -> suggested default path/value.
    """
    os.environ["MCP_TOOLKIT_TASKS_FILE"] = str(DEMO_TASKS)

    if _is_setup_done():
        return _path_hints()

    DEMO_ROOT.mkdir(parents=True, exist_ok=True)
    _setup_git_repo()
    _setup_sqlite_db()
    _setup_tasks()

    return _path_hints()


def _path_hints() -> dict[str, str]:
    """Return default path suggestions keyed by server name."""
    # demo_docs ships with the package — resolve relative to this file
    pkg_root = Path(__file__).resolve().parent.parent
    demo_docs = pkg_root / "demo_docs"
    demo_data = pkg_root / "demo_data"
    return {
        "git-insights": str(DEMO_GIT_REPO),
        "sqlite-explorer": "demo",
        "file-organizer": str(demo_data),
        "markdown-kb": str(demo_docs),
        "task-tracker": str(DEMO_TASKS),
        "system-monitor": "/",
    }


# ---- Git demo repo --------------------------------------------------------


def _setup_git_repo() -> None:
    if DEMO_GIT_REPO.exists():
        shutil.rmtree(DEMO_GIT_REPO)
    DEMO_GIT_REPO.mkdir(parents=True)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Alice Dev",
        "GIT_AUTHOR_EMAIL": "alice@example.com",
        "GIT_COMMITTER_NAME": "Alice Dev",
        "GIT_COMMITTER_EMAIL": "alice@example.com",
    }

    def _git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=str(DEMO_GIT_REPO),
            env=env,
            capture_output=True,
            check=True,
        )

    _git("init", "-b", "main")

    # Commit 1
    (DEMO_GIT_REPO / "README.md").write_text("# Sample Project\n\nA demo repo for MCP Toolkit.\n")
    (DEMO_GIT_REPO / "main.py").write_text(
        'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n'
    )
    _git("add", ".")
    _git("commit", "-m", "feat: initial project setup")

    # Commit 2 — different author
    env2 = {**env, "GIT_AUTHOR_NAME": "Bob Ops", "GIT_AUTHOR_EMAIL": "bob@example.com"}
    (DEMO_GIT_REPO / "utils.py").write_text(
        "import math\n\ndef circle_area(r: float) -> float:\n    return math.pi * r ** 2\n"
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=str(DEMO_GIT_REPO),
        env=env2,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "feat: add geometry utilities"],
        cwd=str(DEMO_GIT_REPO),
        env=env2,
        capture_output=True,
        check=True,
    )

    # Commit 3
    (DEMO_GIT_REPO / "config.json").write_text('{\n  "debug": true,\n  "version": "0.1.0"\n}\n')
    _git("add", ".")
    _git("commit", "-m", "chore: add project config")


# ---- SQLite demo DB -------------------------------------------------------


def _setup_sqlite_db() -> None:
    db_path = str(DEMO_DB)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER DEFAULT 0
        );
        INSERT OR IGNORE INTO products VALUES
            (1, 'Wireless Mouse', 'Electronics', 29.99, 150),
            (2, 'USB-C Hub', 'Electronics', 49.99, 75),
            (3, 'Standing Desk', 'Furniture', 399.00, 12),
            (4, 'Mechanical Keyboard', 'Electronics', 89.99, 200),
            (5, 'Monitor Arm', 'Furniture', 79.99, 45);

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER,
            customer TEXT,
            order_date TEXT
        );
        INSERT OR IGNORE INTO orders VALUES
            (1, 1, 2, 'Acme Corp', '2026-01-15'),
            (2, 3, 1, 'Startup Inc', '2026-01-18'),
            (3, 4, 5, 'Tech Labs', '2026-02-01'),
            (4, 2, 3, 'Acme Corp', '2026-02-05');
    """)
    conn.close()

    # Also place it where sqlite_explorer expects bare names
    target = Path("/tmp/demo.db")
    if not target.exists():
        shutil.copy(db_path, target)


# ---- Task tracker seed data -----------------------------------------------


def _setup_tasks() -> None:
    tasks = {
        "a1b2c3d4": {
            "id": "a1b2c3d4",
            "title": "Set up CI pipeline",
            "description": "Configure GitHub Actions for lint + test",
            "priority": 1,
            "status": "completed",
            "created_at": "2026-02-01T10:00:00+00:00",
            "updated_at": "2026-02-03T15:30:00+00:00",
            "dependencies": [],
        },
        "e5f6g7h8": {
            "id": "e5f6g7h8",
            "title": "Write API integration tests",
            "description": "Cover all CRUD endpoints with pytest",
            "priority": 1,
            "status": "in_progress",
            "created_at": "2026-02-02T09:00:00+00:00",
            "updated_at": "2026-02-07T11:00:00+00:00",
            "dependencies": ["a1b2c3d4"],
        },
        "i9j0k1l2": {
            "id": "i9j0k1l2",
            "title": "Deploy to staging",
            "description": "Push Docker image to staging cluster",
            "priority": 2,
            "status": "pending",
            "created_at": "2026-02-03T14:00:00+00:00",
            "updated_at": "2026-02-03T14:00:00+00:00",
            "dependencies": ["e5f6g7h8"],
        },
        "m3n4o5p6": {
            "id": "m3n4o5p6",
            "title": "Update README with usage examples",
            "description": "Add CLI examples and API reference",
            "priority": 3,
            "status": "pending",
            "created_at": "2026-02-04T08:00:00+00:00",
            "updated_at": "2026-02-04T08:00:00+00:00",
            "dependencies": [],
        },
    }
    DEMO_TASKS.parent.mkdir(parents=True, exist_ok=True)
    DEMO_TASKS.write_text(json.dumps(tasks, indent=2))

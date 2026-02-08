"""Task management with priorities, status tracking, and dependency graphs."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

SERVER_INFO = {
    "name": "task-tracker",
    "description": "Task management with priorities, status tracking, and dependency graphs",
    "tools": [
        "create_task",
        "update_task",
        "delete_task",
        "list_tasks",
        "add_dependency",
        "get_ready_tasks",
    ],
}

mcp = FastMCP(SERVER_INFO["name"])

VALID_STATUSES = {"pending", "in_progress", "completed"}
_DEFAULT_TASKS_FILE = Path.home() / ".mcp-toolkit" / "tasks.json"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _tasks_file() -> Path:
    """Return the tasks file path, respecting MCP_TOOLKIT_TASKS_FILE env var."""
    override = os.environ.get("MCP_TOOLKIT_TASKS_FILE")
    if override:
        return Path(override)
    return _DEFAULT_TASKS_FILE


def _load_tasks() -> dict[str, dict]:
    """Load the task store from disk. Returns an empty dict if the file is missing."""
    path = _tasks_file()
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def _save_tasks(tasks: dict[str, dict]) -> None:
    """Persist the task store to disk, creating the parent directory if needed."""
    path = _tasks_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, indent=2, default=str), encoding="utf-8")


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_task(title: str, description: str = "", priority: int = 2) -> dict:
    """Create a new task with the given title, description, and priority.

    Priority levels: 0 = critical, 1 = high, 2 = medium, 3 = low, 4 = trivial.
    Returns the created task dict.
    """
    if not 0 <= priority <= 4:
        raise ValueError(f"Priority must be 0-4, got {priority}")

    tasks = _load_tasks()

    task_id = uuid.uuid4().hex[:8]
    now = _now_iso()
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "dependencies": [],
    }
    tasks[task_id] = task
    _save_tasks(tasks)
    return task


@mcp.tool()
def update_task(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    status: str | None = None,
) -> dict:
    """Update one or more fields on an existing task.

    Only the provided fields are changed. Status must be one of
    "pending", "in_progress", or "completed".
    Returns the updated task dict.
    """
    tasks = _load_tasks()
    if task_id not in tasks:
        raise ValueError(f"Task not found: {task_id}")

    task = tasks[task_id]

    if title is not None:
        task["title"] = title
    if description is not None:
        task["description"] = description
    if priority is not None:
        if not 0 <= priority <= 4:
            raise ValueError(f"Priority must be 0-4, got {priority}")
        task["priority"] = priority
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}, got '{status}'")
        task["status"] = status

    task["updated_at"] = _now_iso()
    tasks[task_id] = task
    _save_tasks(tasks)
    return task


@mcp.tool()
def delete_task(task_id: str) -> str:
    """Delete a task by ID.

    Also removes the task from any dependency lists on other tasks.
    Returns a confirmation message.
    """
    tasks = _load_tasks()
    if task_id not in tasks:
        raise ValueError(f"Task not found: {task_id}")

    title = tasks[task_id]["title"]
    del tasks[task_id]

    # Clean up dangling dependency references
    for task in tasks.values():
        if task_id in task["dependencies"]:
            task["dependencies"].remove(task_id)

    _save_tasks(tasks)
    return f"Deleted task {task_id} ({title})"


@mcp.tool()
def list_tasks(status: str | None = None, priority: int | None = None) -> list[dict]:
    """List tasks with optional filtering by status and/or priority.

    Results are sorted by priority (ascending) then creation date (ascending).
    """
    tasks = _load_tasks()
    results = list(tasks.values())

    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}, got '{status}'")
        results = [t for t in results if t["status"] == status]

    if priority is not None:
        results = [t for t in results if t["priority"] == priority]

    return sorted(results, key=lambda t: (t["priority"], t["created_at"]))


@mcp.tool()
def add_dependency(task_id: str, depends_on: str) -> str:
    """Add a dependency from one task to another.

    The task identified by task_id will depend on the task identified by
    depends_on. Both tasks must exist, and self-dependency is not allowed.
    Returns a confirmation message.
    """
    if task_id == depends_on:
        raise ValueError("A task cannot depend on itself")

    tasks = _load_tasks()
    if task_id not in tasks:
        raise ValueError(f"Task not found: {task_id}")
    if depends_on not in tasks:
        raise ValueError(f"Dependency task not found: {depends_on}")

    task = tasks[task_id]
    if depends_on in task["dependencies"]:
        return f"Dependency already exists: {task_id} -> {depends_on}"

    task["dependencies"].append(depends_on)
    task["updated_at"] = _now_iso()
    tasks[task_id] = task
    _save_tasks(tasks)
    dep_title = tasks[depends_on]["title"]
    return f"Added dependency: {task_id} ({task['title']}) depends on {depends_on} ({dep_title})"


@mcp.tool()
def get_ready_tasks() -> list[dict]:
    """Return pending tasks whose dependencies are all completed.

    A task is ready when its status is "pending" and every task in its
    dependency list has status "completed". Results are sorted by priority
    then creation date.
    """
    tasks = _load_tasks()

    ready: list[dict] = []
    for task in tasks.values():
        if task["status"] != "pending":
            continue
        all_deps_done = all(
            tasks.get(dep_id, {}).get("status") == "completed" for dep_id in task["dependencies"]
        )
        if all_deps_done:
            ready.append(task)

    return sorted(ready, key=lambda t: (t["priority"], t["created_at"]))

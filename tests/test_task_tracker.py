"""Tests for the task_tracker MCP server."""

from __future__ import annotations

import pytest

from mcp_toolkit.servers.task_tracker import (
    add_dependency,
    create_task,
    delete_task,
    get_ready_tasks,
    list_tasks,
    update_task,
)


class TestCreateTask:
    def test_create_task(self, sample_tasks_file):
        """Creates a task with correct defaults."""
        result = create_task.fn(title="Write tests")
        assert isinstance(result, dict)
        assert "id" in result
        assert result["title"] == "Write tests"
        assert result["status"] == "pending"
        assert result["priority"] == 2

    def test_create_task_priority(self, sample_tasks_file):
        """Both boundary priorities (0 and 4) are accepted."""
        t0 = create_task.fn(title="Critical", priority=0)
        assert t0["priority"] == 0

        t4 = create_task.fn(title="Trivial", priority=4)
        assert t4["priority"] == 4

    def test_create_task_invalid_priority(self, sample_tasks_file):
        """Priority outside 0-4 raises ValueError."""
        with pytest.raises(ValueError, match="Priority must be 0-4"):
            create_task.fn(title="Bad", priority=5)


class TestUpdateTask:
    def test_update_task(self, sample_tasks_file):
        """Updates title and status on an existing task."""
        task = create_task.fn(title="Original")
        updated = update_task.fn(
            task_id=task["id"],
            title="Renamed",
            status="in_progress",
        )
        assert updated["title"] == "Renamed"
        assert updated["status"] == "in_progress"

    def test_update_task_not_found(self, sample_tasks_file):
        """Updating a non-existent task raises ValueError."""
        with pytest.raises(ValueError, match="Task not found"):
            update_task.fn(task_id="nonexistent", title="Nope")


class TestDeleteTask:
    def test_delete_task(self, sample_tasks_file):
        """Creates and deletes a task, verifying it is removed."""
        task = create_task.fn(title="Ephemeral")
        delete_task.fn(task_id=task["id"])

        tasks = list_tasks.fn()
        ids = [t["id"] for t in tasks]
        assert task["id"] not in ids


class TestListTasks:
    def test_list_tasks_all(self, sample_tasks_file):
        """Lists all 3 created tasks."""
        for i in range(3):
            create_task.fn(title=f"Task {i}")
        result = list_tasks.fn()
        assert len(result) == 3

    def test_list_tasks_filter_status(self, sample_tasks_file):
        """Filters tasks by status."""
        t1 = create_task.fn(title="Pending one")
        t2 = create_task.fn(title="Done one")
        update_task.fn(task_id=t2["id"], status="completed")

        pending = list_tasks.fn(status="pending")
        assert all(t["status"] == "pending" for t in pending)
        assert any(t["id"] == t1["id"] for t in pending)
        assert not any(t["id"] == t2["id"] for t in pending)

    def test_list_tasks_filter_priority(self, sample_tasks_file):
        """Filters tasks by priority."""
        create_task.fn(title="High", priority=1)
        create_task.fn(title="Low", priority=3)

        result = list_tasks.fn(priority=1)
        assert len(result) == 1
        assert result[0]["title"] == "High"


class TestDependencies:
    def test_add_dependency(self, sample_tasks_file):
        """Adds a dependency between two tasks."""
        a = create_task.fn(title="Task A")
        b = create_task.fn(title="Task B")

        result = add_dependency.fn(task_id=a["id"], depends_on=b["id"])
        assert "depends on" in result

    def test_add_self_dependency(self, sample_tasks_file):
        """Self-dependency raises ValueError."""
        task = create_task.fn(title="Self")
        with pytest.raises(ValueError, match="cannot depend on itself"):
            add_dependency.fn(task_id=task["id"], depends_on=task["id"])


class TestReadyTasks:
    def test_get_ready_tasks(self, sample_tasks_file):
        """A task blocked by a dependency becomes ready when the dep is completed."""
        a = create_task.fn(title="Task A")
        b = create_task.fn(title="Task B")
        add_dependency.fn(task_id=a["id"], depends_on=b["id"])

        # A depends on B which is pending, so A is not ready
        ready_before = get_ready_tasks.fn()
        ready_ids_before = [t["id"] for t in ready_before]
        assert a["id"] not in ready_ids_before

        # Complete B, now A should become ready
        update_task.fn(task_id=b["id"], status="completed")
        ready_after = get_ready_tasks.fn()
        ready_ids_after = [t["id"] for t in ready_after]
        assert a["id"] in ready_ids_after

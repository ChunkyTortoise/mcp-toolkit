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

    def test_ready_tasks_no_dependencies(self, sample_tasks_file):
        """A pending task with no dependencies is always ready."""
        task = create_task.fn(title="No deps")
        ready = get_ready_tasks.fn()
        ids = [t["id"] for t in ready]
        assert task["id"] in ids

    def test_ready_tasks_partial_deps_incomplete(self, sample_tasks_file):
        """Task with 2 deps, only one completed, is NOT ready."""
        a = create_task.fn(title="Dep A")
        b = create_task.fn(title="Dep B")
        c = create_task.fn(title="Blocked task")
        add_dependency.fn(task_id=c["id"], depends_on=a["id"])
        add_dependency.fn(task_id=c["id"], depends_on=b["id"])

        # Complete only one dependency
        update_task.fn(task_id=a["id"], status="completed")
        ready = get_ready_tasks.fn()
        ready_ids = [t["id"] for t in ready]
        assert c["id"] not in ready_ids

    def test_in_progress_tasks_not_ready(self, sample_tasks_file):
        """Tasks with status 'in_progress' are not returned as ready."""
        task = create_task.fn(title="WIP")
        update_task.fn(task_id=task["id"], status="in_progress")
        ready = get_ready_tasks.fn()
        ready_ids = [t["id"] for t in ready]
        assert task["id"] not in ready_ids


class TestUpdateTaskEdgeCases:
    def test_update_invalid_status(self, sample_tasks_file):
        """Invalid status raises ValueError."""
        task = create_task.fn(title="Original")
        with pytest.raises(ValueError, match="Status must be one of"):
            update_task.fn(task_id=task["id"], status="invalid_status")

    def test_update_invalid_priority(self, sample_tasks_file):
        """Priority outside 0-4 during update raises ValueError."""
        task = create_task.fn(title="Original")
        with pytest.raises(ValueError, match="Priority must be 0-4"):
            update_task.fn(task_id=task["id"], priority=-1)

    def test_update_only_description(self, sample_tasks_file):
        """Updating only description preserves other fields."""
        task = create_task.fn(title="Keep Title", priority=1)
        updated = update_task.fn(task_id=task["id"], description="New desc")
        assert updated["title"] == "Keep Title"
        assert updated["priority"] == 1
        assert updated["description"] == "New desc"


class TestDeleteTaskEdgeCases:
    def test_delete_nonexistent_task(self, sample_tasks_file):
        """Deleting a nonexistent task raises ValueError."""
        with pytest.raises(ValueError, match="Task not found"):
            delete_task.fn(task_id="doesnotexist")

    def test_delete_cleans_dependency_references(self, sample_tasks_file):
        """Deleting a task removes it from other tasks' dependency lists."""
        a = create_task.fn(title="Dependency")
        b = create_task.fn(title="Dependent")
        add_dependency.fn(task_id=b["id"], depends_on=a["id"])

        # Verify dependency exists
        tasks_before = list_tasks.fn()
        b_before = next(t for t in tasks_before if t["id"] == b["id"])
        assert a["id"] in b_before["dependencies"]

        # Delete the dependency task
        delete_task.fn(task_id=a["id"])

        # Verify dependency reference was cleaned up
        tasks_after = list_tasks.fn()
        b_after = next(t for t in tasks_after if t["id"] == b["id"])
        assert a["id"] not in b_after["dependencies"]


class TestListTasksEdgeCases:
    def test_list_tasks_invalid_status(self, sample_tasks_file):
        """Filtering by invalid status raises ValueError."""
        create_task.fn(title="Task")
        with pytest.raises(ValueError, match="Status must be one of"):
            list_tasks.fn(status="nonexistent")

    def test_list_tasks_sorted_by_priority_then_date(self, sample_tasks_file):
        """Tasks are sorted by priority ascending, then created_at."""
        create_task.fn(title="Low", priority=3)
        create_task.fn(title="High", priority=0)
        create_task.fn(title="Medium", priority=2)
        result = list_tasks.fn()
        priorities = [t["priority"] for t in result]
        assert priorities == sorted(priorities)

    def test_list_empty_store(self, sample_tasks_file):
        """Listing tasks on an empty store returns empty list."""
        result = list_tasks.fn()
        assert result == []


class TestDependencyEdgeCases:
    def test_add_dependency_nonexistent_task(self, sample_tasks_file):
        """Adding dependency to nonexistent task raises ValueError."""
        dep = create_task.fn(title="Dep")
        with pytest.raises(ValueError, match="Task not found"):
            add_dependency.fn(task_id="nonexistent", depends_on=dep["id"])

    def test_add_dependency_nonexistent_dep(self, sample_tasks_file):
        """Adding nonexistent dependency raises ValueError."""
        task = create_task.fn(title="Task")
        with pytest.raises(ValueError, match="Dependency task not found"):
            add_dependency.fn(task_id=task["id"], depends_on="nonexistent")

    def test_add_duplicate_dependency(self, sample_tasks_file):
        """Adding the same dependency twice returns 'already exists' message."""
        a = create_task.fn(title="A")
        b = create_task.fn(title="B")
        add_dependency.fn(task_id=a["id"], depends_on=b["id"])
        result = add_dependency.fn(task_id=a["id"], depends_on=b["id"])
        assert "already exists" in result


class TestCreateTaskEdgeCases:
    def test_create_task_with_description(self, sample_tasks_file):
        """Task created with description stores it correctly."""
        task = create_task.fn(title="Described", description="Full details here")
        assert task["description"] == "Full details here"

    def test_create_task_negative_priority(self, sample_tasks_file):
        """Priority below 0 raises ValueError."""
        with pytest.raises(ValueError, match="Priority must be 0-4"):
            create_task.fn(title="Bad", priority=-1)

    def test_create_task_has_timestamps(self, sample_tasks_file):
        """Created task has created_at and updated_at timestamps."""
        task = create_task.fn(title="Timed")
        assert "created_at" in task
        assert "updated_at" in task
        assert task["created_at"] == task["updated_at"]

    def test_create_task_empty_dependencies(self, sample_tasks_file):
        """New tasks start with an empty dependency list."""
        task = create_task.fn(title="Fresh")
        assert task["dependencies"] == []

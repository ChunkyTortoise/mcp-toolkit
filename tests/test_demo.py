"""Tests for the demo data setup module."""

from __future__ import annotations

from pathlib import Path

from mcp_toolkit.demo import (
    DEMO_DB,
    DEMO_GIT_REPO,
    DEMO_ROOT,
    DEMO_TASKS,
    _is_setup_done,
    _path_hints,
    setup_demo_environment,
)


class TestPathHints:
    def test_path_hints_keys(self):
        """Path hints dict contains expected server name keys."""
        hints = _path_hints()
        assert set(hints.keys()) == {
            "git-insights",
            "sqlite-explorer",
            "file-organizer",
            "markdown-kb",
            "task-tracker",
            "system-monitor",
        }

    def test_path_hints_git_insights_is_demo_repo(self):
        """git-insights hint points to the demo git repo path."""
        hints = _path_hints()
        assert hints["git-insights"] == str(DEMO_GIT_REPO)

    def test_path_hints_sqlite_is_demo(self):
        """sqlite-explorer hint is the bare name 'demo'."""
        hints = _path_hints()
        assert hints["sqlite-explorer"] == "demo"

    def test_path_hints_system_monitor_is_root(self):
        """system-monitor hint is '/'."""
        hints = _path_hints()
        assert hints["system-monitor"] == "/"

    def test_path_hints_markdown_kb_points_to_demo_docs(self):
        """markdown-kb hint points to the demo_docs directory."""
        hints = _path_hints()
        assert hints["markdown-kb"].endswith("demo_docs")
        assert Path(hints["markdown-kb"]).is_dir()


class TestSetupDemoEnvironment:
    def test_setup_returns_hints(self):
        """setup_demo_environment returns the path hints dict."""
        result = setup_demo_environment()
        assert isinstance(result, dict)
        assert "git-insights" in result

    def test_setup_idempotent(self):
        """Calling setup_demo_environment twice produces same hints."""
        hints1 = setup_demo_environment()
        hints2 = setup_demo_environment()
        assert hints1 == hints2


class TestIsSetupDone:
    def test_is_setup_done_after_setup(self):
        """After setup_demo_environment, _is_setup_done returns True."""
        setup_demo_environment()
        assert _is_setup_done() is True


class TestDemoConstants:
    def test_demo_root_is_tmp(self):
        """DEMO_ROOT is under /tmp."""
        assert str(DEMO_ROOT).startswith("/tmp")

    def test_demo_paths_under_root(self):
        """All demo paths are children of DEMO_ROOT."""
        assert str(DEMO_GIT_REPO).startswith(str(DEMO_ROOT))
        assert str(DEMO_DB).startswith(str(DEMO_ROOT))
        assert str(DEMO_TASKS).startswith(str(DEMO_ROOT))

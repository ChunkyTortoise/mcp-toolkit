"""Tests for the mcp-toolkit CLI."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from mcp_toolkit.cli import cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestVersion:
    def test_version(self, runner):
        """--version outputs a version number (or reports package not installed)."""
        result = runner.invoke(cli, ["--version"])
        # When installed: exit 0 with version string
        # When not installed: RuntimeError from click's version_option
        if result.exit_code == 0:
            assert "version" in result.output.lower()
        else:
            assert result.exception is not None
            assert "not installed" in str(result.exception).lower()


class TestListCommand:
    def test_list_servers(self, runner):
        """The list command shows all 6 servers."""
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        for name in (
            "file-organizer",
            "git-insights",
            "markdown-kb",
            "sqlite-explorer",
            "system-monitor",
            "task-tracker",
        ):
            assert name in result.output

    def test_list_server_count(self, runner):
        """Output contains '6 servers available'."""
        result = runner.invoke(cli, ["list"])
        assert "6 servers available" in result.output

    def test_list_shows_descriptions(self, runner):
        """Output includes server descriptions."""
        result = runner.invoke(cli, ["list"])
        assert "CPU" in result.output or "monitor" in result.output.lower()
        assert "SQLite" in result.output or "sqlite" in result.output.lower()


class TestInfoCommand:
    def test_info_valid(self, runner):
        """Info for sqlite-explorer shows tool names."""
        result = runner.invoke(cli, ["info", "sqlite-explorer"])
        assert result.exit_code == 0
        assert "query" in result.output
        assert "get_schema" in result.output

    def test_info_invalid(self, runner):
        """Info for a nonexistent server exits with code 1."""
        result = runner.invoke(cli, ["info", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestConfigCommand:
    def test_config_output(self, runner):
        """Config for sqlite-explorer outputs valid JSON with mcpServers."""
        result = runner.invoke(cli, ["config", "sqlite-explorer"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mcpServers" in data
        assert "sqlite-explorer" in data["mcpServers"]

    def test_config_invalid(self, runner):
        """Config for a nonexistent server exits with code 1."""
        result = runner.invoke(cli, ["config", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_config_has_command_and_args(self, runner):
        """Config JSON contains 'command' and 'args' keys."""
        result = runner.invoke(cli, ["config", "task-tracker"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        server_cfg = data["mcpServers"]["task-tracker"]
        assert "command" in server_cfg
        assert "args" in server_cfg
        assert server_cfg["command"] == "mcp-toolkit"
        assert server_cfg["args"] == ["serve", "task-tracker"]


class TestServeCommand:
    def test_serve_invalid_server(self, runner):
        """Serve for a nonexistent server exits with code 1."""
        result = runner.invoke(cli, ["serve", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestInfoCommandDetails:
    def test_info_shows_module_path(self, runner):
        """Info output includes the module path."""
        result = runner.invoke(cli, ["info", "file-organizer"])
        assert result.exit_code == 0
        assert "mcp_toolkit.servers.file_organizer" in result.output

    def test_info_shows_tools(self, runner):
        """Info for task-tracker lists its tool names."""
        result = runner.invoke(cli, ["info", "task-tracker"])
        assert result.exit_code == 0
        assert "create_task" in result.output
        assert "list_tasks" in result.output

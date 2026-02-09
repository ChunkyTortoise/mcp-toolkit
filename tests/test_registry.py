"""Tests for the shared registry module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp_toolkit.shared.registry import (
    ServerInfo,
    _REGISTRY,
    _discover_servers,
    get_server,
    get_server_names,
    list_servers,
)


class TestListServers:
    def test_list_servers_returns_all_six(self):
        """All 6 MCP servers are discovered and listed."""
        servers = list_servers()
        assert len(servers) == 6

    def test_list_servers_sorted_by_name(self):
        """Servers are returned sorted alphabetically by name."""
        servers = list_servers()
        names = [s.name for s in servers]
        assert names == sorted(names)

    def test_list_servers_expected_names(self):
        """All 6 known server names are present."""
        servers = list_servers()
        names = {s.name for s in servers}
        assert names == {
            "file-organizer",
            "git-insights",
            "markdown-kb",
            "sqlite-explorer",
            "system-monitor",
            "task-tracker",
        }


class TestGetServer:
    def test_get_server_valid(self):
        """Returns a ServerInfo for a known server name."""
        server = get_server("sqlite-explorer")
        assert server is not None
        assert server.name == "sqlite-explorer"
        assert isinstance(server, ServerInfo)

    def test_get_server_invalid_returns_none(self):
        """Returns None for an unknown server name."""
        assert get_server("nonexistent-server") is None

    def test_get_server_empty_string(self):
        """Returns None for an empty string."""
        assert get_server("") is None


class TestGetServerNames:
    def test_get_server_names_count(self):
        """Returns exactly 6 server names."""
        names = get_server_names()
        assert len(names) == 6

    def test_get_server_names_sorted(self):
        """Server names are returned sorted alphabetically."""
        names = get_server_names()
        assert names == sorted(names)


class TestServerInfo:
    def test_server_info_attributes(self):
        """ServerInfo has name, description, module, and tools."""
        server = get_server("file-organizer")
        assert server.name == "file-organizer"
        assert len(server.description) > 0
        assert server.module == "mcp_toolkit.servers.file_organizer"
        assert isinstance(server.tools, list)
        assert len(server.tools) >= 1

    def test_server_info_tools_are_strings(self):
        """All tool entries in ServerInfo are strings."""
        for server in list_servers():
            for tool in server.tools:
                assert isinstance(tool, str)

    def test_server_info_load_returns_mcp_instance(self):
        """ServerInfo.load() imports the module and returns its mcp object."""
        server = get_server("task-tracker")
        mcp = server.load()
        # The loaded object should have a name attribute matching the server
        assert mcp.name == "task-tracker"

    def test_server_info_default_tools_list(self):
        """ServerInfo created with no tools kwarg gets an empty list."""
        info = ServerInfo(name="test", description="desc", module="fake.mod")
        assert info.tools == []


class TestDiscoverServers:
    def test_discover_idempotent(self):
        """Calling _discover_servers multiple times doesn't duplicate entries."""
        _discover_servers()
        count_first = len(_REGISTRY)
        _discover_servers()
        count_second = len(_REGISTRY)
        assert count_first == count_second

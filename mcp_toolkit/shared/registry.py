"""Server registry with auto-discovery from the servers package."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field

from mcp_toolkit import servers as servers_pkg


@dataclass
class ServerInfo:
    """Metadata for a registered MCP server."""

    name: str
    description: str
    module: str
    tools: list[str] = field(default_factory=list)

    def load(self):
        """Import the server module and return its FastMCP instance."""
        mod = importlib.import_module(self.module)
        return mod.mcp


_REGISTRY: dict[str, ServerInfo] = {}


def _discover_servers() -> None:
    """Scan mcp_toolkit.servers for modules exposing SERVER_INFO."""
    if _REGISTRY:
        return
    for importer, modname, ispkg in pkgutil.iter_modules(servers_pkg.__path__):
        full = f"mcp_toolkit.servers.{modname}"
        try:
            mod = importlib.import_module(full)
        except Exception:
            continue
        info = getattr(mod, "SERVER_INFO", None)
        if info and isinstance(info, dict):
            _REGISTRY[info["name"]] = ServerInfo(
                name=info["name"],
                description=info["description"],
                module=full,
                tools=info.get("tools", []),
            )


def list_servers() -> list[ServerInfo]:
    """Return all discovered servers sorted by name."""
    _discover_servers()
    return sorted(_REGISTRY.values(), key=lambda s: s.name)


def get_server(name: str) -> ServerInfo | None:
    """Get a server by name."""
    _discover_servers()
    return _REGISTRY.get(name)


def get_server_names() -> list[str]:
    """Return sorted list of server names."""
    _discover_servers()
    return sorted(_REGISTRY.keys())

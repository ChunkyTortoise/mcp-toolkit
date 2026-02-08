"""CLI tool for discovering and launching MCP servers."""

from __future__ import annotations

import json

import click

from mcp_toolkit.shared.registry import get_server, list_servers


@click.group()
@click.version_option(package_name="mcp-toolkit")
def cli():
    """MCP Toolkit — 6 production-ready MCP servers."""


@cli.command()
def list_cmd():
    """List all available MCP servers."""
    servers = list_servers()
    if not servers:
        click.echo("No servers found.")
        return
    click.echo(f"\n{'Name':<20} {'Tools':<8} Description")
    click.echo("-" * 70)
    for s in servers:
        click.echo(f"{s.name:<20} {len(s.tools):<8} {s.description}")
    click.echo(f"\n{len(servers)} servers available. Use 'mcp-toolkit info <name>' for details.\n")


# Register with the name 'list' (can't use as Python identifier)
cli.add_command(list_cmd, "list")


@cli.command()
@click.argument("server_name")
def info(server_name: str):
    """Show detailed info about a server."""
    server = get_server(server_name)
    if not server:
        click.echo(f"Error: Server '{server_name}' not found.")
        click.echo(f"Available: {', '.join(s.name for s in list_servers())}")
        raise SystemExit(1)
    click.echo(f"\n  {server.name}")
    click.echo(f"  {server.description}")
    click.echo(f"\n  Module: {server.module}")
    click.echo(f"\n  Tools ({len(server.tools)}):")
    for tool in server.tools:
        click.echo(f"    - {tool}")
    click.echo()


@cli.command()
@click.argument("server_name")
def config(server_name: str):
    """Generate MCP config JSON snippet for a server."""
    server = get_server(server_name)
    if not server:
        click.echo(f"Error: Server '{server_name}' not found.")
        raise SystemExit(1)
    cfg = {
        "mcpServers": {
            server.name: {
                "command": "mcp-toolkit",
                "args": ["serve", server.name],
            }
        }
    }
    click.echo(json.dumps(cfg, indent=2))


@cli.command()
@click.argument("server_name")
def serve(server_name: str):
    """Launch an MCP server (stdio transport)."""
    server = get_server(server_name)
    if not server:
        click.echo(f"Error: Server '{server_name}' not found.")
        raise SystemExit(1)
    click.echo(f"Starting {server.name}...", err=True)
    mcp_instance = server.load()
    mcp_instance.run()

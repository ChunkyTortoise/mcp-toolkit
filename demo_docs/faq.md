# Frequently Asked Questions

## General

### What is MCP?
MCP (Model Context Protocol) is an open standard for connecting AI assistants to external tools, data sources, and services. It provides a unified interface for AI models to interact with the world.

### Who maintains MCP?
MCP was created by Anthropic and is now backed by the Linux Foundation. It has broad adoption across AI providers including OpenAI, Google, and Microsoft.

### Is MCP free to use?
Yes, MCP is an open protocol with MIT-licensed reference implementations. There are no licensing fees.

## Technical

### What transport protocols does MCP support?
MCP supports stdio (standard input/output) and HTTP with Server-Sent Events (SSE). Stdio is best for local tools, while HTTP works for remote services.

### How do I create an MCP server?
The fastest way is using FastMCP, a Python framework. Install with `pip install fastmcp`, then define tools using the `@mcp.tool()` decorator.

### Can I use MCP with TypeScript?
Yes, the official MCP SDK supports both Python and TypeScript. The TypeScript SDK is available as `@modelcontextprotocol/sdk`.

## Troubleshooting

### My server isn't connecting
Check that the transport matches your client configuration. Ensure the server process is running and accessible. Check logs for connection errors.

### Tools aren't showing up
Verify your tool functions have proper type annotations and docstrings. FastMCP uses these to generate the tool schema.

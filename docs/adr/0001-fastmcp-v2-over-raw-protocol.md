# ADR 0001: FastMCP v2 Over Raw Protocol

## Status
Accepted

## Context
The Model Context Protocol (MCP) requires a JSON-RPC implementation with server discovery, capability negotiation, and transport management. Implementing this from scratch involves significant boilerplate for protocol compliance, error handling, and transport abstraction. We needed to decide between raw protocol implementation and an SDK-based approach.

## Decision
Use the FastMCP v2 SDK for declarative server and tool definitions with auto-discovery. FastMCP provides decorators for tool registration, automatic parameter schema generation from type hints, built-in SSE (Server-Sent Events) transport, and protocol-compliant JSON-RPC handling.

## Consequences
- **Positive**: Reduces boilerplate by approximately 80% compared to raw protocol implementation. Type-safe tool parameters via Python type hints. Built-in SSE transport eliminates custom transport code. Auto-discovery simplifies client integration.
- **Negative**: The SDK abstraction hides protocol details, making it harder to understand what happens at the wire level. Debugging issues requires understanding both the FastMCP layer and the underlying MCP protocol. SDK version upgrades may introduce breaking changes.

# MCP Glossary

## Core Concepts

**MCP (Model Context Protocol)**: An open standard for AI-tool communication. Defines how AI assistants discover and invoke external tools.

**Server**: A process that exposes tools, resources, and prompts via the MCP protocol. Servers run locally or remotely.

**Client**: An AI application that connects to MCP servers. Examples include Claude Desktop, Cursor, and Claude Code.

**Tool**: A function exposed by a server that an AI can invoke. Tools have typed inputs and outputs.

**Resource**: Read-only data exposed by a server. Resources provide context without side effects.

**Prompt**: A reusable template stored on the server. Prompts can include dynamic parameters.

## Transport

**stdio**: Standard input/output transport. The client spawns the server as a subprocess and communicates via stdin/stdout.

**SSE (Server-Sent Events)**: HTTP-based transport for remote servers. Uses SSE for server-to-client streaming.

**Streamable HTTP**: Modern HTTP transport replacing SSE. Supports bidirectional communication.

## Architecture

**FastMCP**: A Python framework for building MCP servers. Provides decorators for tools, resources, and prompts.

**Registry**: A catalog of available servers with metadata. Used for discovery and configuration.

**Context**: Runtime information passed to tool functions, including logging and progress reporting.

## Security

**Capability Negotiation**: Client and server agree on supported features during initialization.

**Input Validation**: Servers validate tool inputs using JSON Schema. FastMCP generates schemas from type annotations.

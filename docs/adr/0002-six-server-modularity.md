# ADR 0002: Six-Server Modularity

## Status
Accepted

## Context
MCP tools span diverse domains: filesystem operations, GitHub integration, database queries, web scraping, analytics, and knowledge base management. A monolithic server containing all tools would have broad permissions, a large attack surface, and no ability to scale or deploy tools independently.

## Decision
Split functionality into six separate MCP servers, each with a single responsibility. Each server is independently deployable, testable, and permissioned. Servers communicate through the MCP protocol and do not share internal state. Cross-server operations are orchestrated by the client.

## Consequences
- **Positive**: Granular permissions per server (e.g., filesystem server has no network access). Independent scaling based on usage patterns. Clear API boundaries enforce separation of concerns. A bug in one server does not affect others.
- **Negative**: Server coordination adds operational complexity. Cross-server operations (e.g., scrape a URL and store in the knowledge base) require client-side orchestration. Six servers means six processes to monitor, deploy, and maintain.

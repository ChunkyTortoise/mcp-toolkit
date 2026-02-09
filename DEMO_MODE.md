# Demo Mode Guide

## Overview
Run mcp-toolkit without external dependencies for testing and demonstrations. All servers operate on local demo data with no network calls or API keys required.

## Quick Start

### Streamlit Playground
```bash
make demo
```
This launches the interactive playground at `http://localhost:8501` with demo data pre-loaded.

### CLI Demo
```bash
# List all servers
mcp-toolkit list

# Get server details
mcp-toolkit info sqlite-explorer

# Serve a server (for Claude Desktop integration)
mcp-toolkit serve file-organizer
```

### Python API Demo
```python
from mcp_toolkit.shared.registry import get_server

# Load a server
server_info = get_server("markdown-kb")
mcp = server_info.load()

# Access tools
tools = mcp.list_tools()
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

## Demo Data Included

The `demo_data/` and `demo_docs/` directories contain:

| Location | Contents | Used By |
|----------|----------|---------|
| `demo_data/sample_files/` | Text, CSV, Python files | file-organizer |
| `demo_docs/*.md` | Markdown knowledge base | markdown-kb |
| `/tmp/mcp_demo_*.db` | Temporary SQLite DBs | sqlite-explorer |
| Current git repo | Repository metadata | git-insights |

Demo environment is set up automatically by `setup_demo_environment()` in `mcp_toolkit/demo.py`.

## What's Mocked

**Nothing is mocked.** All servers operate on real local data:

### sqlite-explorer
- **Database**: Temporary SQLite database at `/tmp/mcp_demo_tasks.db`
- **Tables**: `tasks` table with sample data
- **Operations**: Full CRUD on local database

### file-organizer
- **Files**: Demo files in `demo_data/sample_files/`
- **Operations**: Search, dedup, metadata extraction on local files
- **No network**: All file operations are local

### markdown-kb
- **Documents**: Markdown files in `demo_docs/`
- **Indexing**: TF-IDF vectorization via scikit-learn (local)
- **Search**: Cosine similarity on local vectors

### system-monitor
- **Metrics**: Real system metrics via `psutil`
- **No external services**: Reads from local OS APIs
- **Live data**: CPU, memory, disk, network stats are real

### git-insights
- **Repository**: Uses the mcp-toolkit repo itself as demo data
- **Operations**: Real Git operations via `GitPython`
- **No network**: Reads local Git history only

### task-tracker
- **Storage**: In-memory task list (resets on restart)
- **Operations**: Full task CRUD with dependency graph
- **No persistence**: Tasks are not saved to disk

## Switching to Production

### 1. Persistent Storage (sqlite-explorer)
```python
# Instead of temporary database
from mcp_toolkit.servers.sqlite_explorer import create_database

db_path = "/var/lib/myapp/production.db"
create_database(db_path, schema={...})
```

### 2. Real Data Sources (file-organizer)
Point to production directories:

```python
# In your integration code
from mcp_toolkit.shared.registry import get_server

server = get_server("file-organizer").load()
# Tools will now operate on paths you provide
result = server.tools.search_files(
    directory="/production/data",
    pattern="*.csv"
)
```

### 3. Production Knowledge Base (markdown-kb)
Index your documentation:

```python
from mcp_toolkit.servers.markdown_kb import index_documents

docs_path = "/path/to/company/docs"
index_documents(docs_path)
```

### 4. Remote Monitoring (system-monitor)
For monitoring remote servers, use SSH tunneling:

```bash
# SSH tunnel to remote host
ssh -L 8000:localhost:8000 user@remote-server

# Run mcp-toolkit on remote
ssh user@remote-server "mcp-toolkit serve system-monitor"

# Access from local Claude Desktop
```

### 5. Task Persistence (task-tracker)
Save tasks to SQLite:

```python
# Modify task-tracker to use sqlite-explorer for persistence
import sqlite3

conn = sqlite3.connect("tasks.db")
# Store tasks in database instead of in-memory dict
```

### 6. Remote Git Repos (git-insights)
Analyze remote repositories:

```bash
# Clone repo locally first
git clone https://github.com/user/repo.git /tmp/repo
cd /tmp/repo

# Run git-insights
mcp-toolkit serve git-insights
```

## Environment Variables

Demo mode requires **no environment variables**. For production:

| Variable | Required | Purpose |
|----------|----------|---------|
| `MCP_SQLITE_PATH` | Optional | Default SQLite database path |
| `MCP_FILE_ROOT` | Optional | Root directory for file-organizer |
| `MCP_MARKDOWN_PATH` | Optional | Default markdown KB directory |
| `MCP_MONITOR_INTERVAL` | Optional | System monitor refresh interval (seconds) |
| `MCP_TASK_PERSIST_PATH` | Optional | SQLite path for task persistence |

### Example Production .env
```bash
MCP_SQLITE_PATH=/var/lib/mcp/data.db
MCP_FILE_ROOT=/var/data
MCP_MARKDOWN_PATH=/opt/docs
MCP_MONITOR_INTERVAL=60
MCP_TASK_PERSIST_PATH=/var/lib/mcp/tasks.db
```

## Performance Benchmarks (Demo Mode)

On a standard laptop:
- **sqlite-explorer**: 10,000 queries/second on demo DB
- **file-organizer**: Scans 1,000 files in <500ms
- **markdown-kb**: Indexes 100 docs in <1 second
- **system-monitor**: <10ms per metric read
- **git-insights**: Analyzes 1,000 commits in <2 seconds
- **task-tracker**: <1ms per task operation

## Security Checklist

Demo mode is safe for public demonstrations:
- No API keys required
- No network calls
- Temporary databases (auto-cleaned)
- Read-only file operations (except temp files)

For production:
- **File access**: Restrict file-organizer to specific directories
- **SQL injection**: Use parameterized queries (already implemented)
- **Path traversal**: Validate paths in file-organizer
- **Git access**: Run git-insights with read-only user
- **System monitoring**: Limit to non-sensitive metrics
- **Rate limiting**: Add request throttling for multi-user scenarios

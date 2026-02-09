# Customization Guide

## Quick Start (5 minutes)

### Environment Setup
```bash
git clone https://github.com/ChunkyTortoise/mcp-toolkit.git
cd mcp-toolkit
pip install -e .
```

No API keys or external services required. All 6 MCP servers run locally.

### First Run Verification
```bash
make test  # Run all 70+ tests
mcp-toolkit list  # See all 6 servers
make demo  # Launch Streamlit playground
```

### Connect to Claude Desktop
```bash
mcp-toolkit config sqlite-explorer
```

Copy the JSON output to your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Common Customizations

### 1. Server Configuration
**Registry Location** (`mcp_toolkit/shared/registry.py`, line 20):
All servers are auto-discovered from `mcp_toolkit/servers/` directory. To add a custom server:

```python
# Create mcp_toolkit/servers/my_server.py
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Your custom tool."""
    return f"Processed: {param}"
```

No registration needed — it's automatically discovered by `list_servers()`.

### 2. CLI Customization
**Command Aliases** (`mcp_toolkit/cli.py`, line 30):
```python
# Add custom commands
@cli.command(name="quick-serve")
@click.argument("server")
def quick_serve(server):
    """Shortcut to serve a server."""
    serve(server)
```

**Output Formatting** (`cli.py`, line 80):
Modify `list_servers()` to output JSON instead of tables:
```python
import json
servers = list_servers()
print(json.dumps([s.to_dict() for s in servers], indent=2))
```

### 3. Server-Specific Customization

#### sqlite-explorer
**Default Database Path** (`mcp_toolkit/servers/sqlite_explorer.py`, line 40):
```python
DEFAULT_DB_PATH = "/path/to/your/data.db"
```

**Query Timeout** (`sqlite_explorer.py`, line 120):
```python
cursor.execute(query, timeout=10.0)  # 10 second timeout
```

#### file-organizer
**Search Depth Limit** (`mcp_toolkit/servers/file_organizer.py`, line 60):
```python
MAX_DEPTH = 5  # Limit recursive search to 5 levels
```

**Exclude Patterns** (`file_organizer.py`, line 85):
```python
EXCLUDE_PATTERNS = [".git", "__pycache__", "node_modules", "*.pyc"]
```

#### markdown-kb
**TF-IDF Configuration** (`mcp_toolkit/servers/markdown_kb.py`, line 50):
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=5000,  # Increase vocabulary size
    ngram_range=(1, 2),  # Add bigrams
    min_df=2  # Ignore rare terms
)
```

#### system-monitor
**Alert Thresholds** (`mcp_toolkit/servers/system_monitor.py`, line 90):
```python
CPU_ALERT_THRESHOLD = 80.0  # Percent
MEMORY_ALERT_THRESHOLD = 85.0  # Percent
DISK_ALERT_THRESHOLD = 90.0  # Percent
```

#### git-insights
**Large File Threshold** (`mcp_toolkit/servers/git_insights.py`, line 110):
```python
LARGE_FILE_SIZE_MB = 5.0  # Flag files over 5MB
```

#### task-tracker
**Default Priority** (`mcp_toolkit/servers/task_tracker.py`, line 70):
```python
DEFAULT_PRIORITY = 2  # 0=lowest, 4=highest
```

### 4. Streamlit Playground
**Page Configuration** (`app.py`, line 16):
```python
st.set_page_config(
    page_title="MCP Toolkit - Your Company",
    page_icon="🔧",
    layout="wide"
)
```

**Demo Data Location** (`app.py`, line 19):
Modify `setup_demo_environment()` to use your own demo files:
```python
from pathlib import Path
demo_dir = Path("/path/to/your/demo/data")
```

## Advanced Features

### Multi-Server Orchestration
Run multiple servers simultaneously:

```python
# orchestrator.py
import asyncio
from mcp_toolkit.shared.registry import get_server

async def run_servers():
    servers = ["sqlite-explorer", "markdown-kb", "system-monitor"]
    tasks = [get_server(s).load().run() for s in servers]
    await asyncio.gather(*tasks)

asyncio.run(run_servers())
```

### Custom Tool Development
**Tool with State** (`servers/example.py`):
```python
from fastmcp import FastMCP

mcp = FastMCP("stateful-server")
state = {"counter": 0}

@mcp.tool()
def increment() -> int:
    """Increment counter."""
    state["counter"] += 1
    return state["counter"]

@mcp.tool()
def get_count() -> int:
    """Get current count."""
    return state["counter"]
```

### Performance Monitoring
**Add Timing Middleware** (`servers/sqlite_explorer.py`, line 1):
```python
import time
from functools import wraps

def timed_tool(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@mcp.tool()
@timed_tool
def query(sql: str) -> list:
    # ... implementation
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .
CMD ["mcp-toolkit", "serve", "sqlite-explorer"]
```

```bash
docker build -t mcp-toolkit .
docker run -p 8000:8000 mcp-toolkit
```

### systemd Service (Linux)
```ini
# /etc/systemd/system/mcp-toolkit.service
[Unit]
Description=MCP Toolkit Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-toolkit
ExecStart=/usr/bin/mcp-toolkit serve sqlite-explorer
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mcp-toolkit
sudo systemctl start mcp-toolkit
```

## Troubleshooting

### Common Errors

**ImportError: No module named 'fastmcp'**
- Fix: Install in editable mode: `pip install -e .`
- Alternative: `pip install fastmcp>=2.0`

**Server not found in registry**
- Verify file is in `mcp_toolkit/servers/` directory
- Check filename matches server name (e.g., `sqlite_explorer.py` for `sqlite-explorer`)
- Ensure file contains `mcp = FastMCP("server-name")`

**SQLite database locked**
- Fix: Close other connections to the database
- Use WAL mode: `PRAGMA journal_mode=WAL;`

**Git insights fails on non-repo**
- Fix: Run tools only on valid Git repositories
- Check: `git rev-parse --is-inside-work-tree` returns true

### Debug Mode
**Enable FastMCP Logging** (`cli.py`, line 1):
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Server Inspection** (CLI):
```bash
mcp-toolkit info sqlite-explorer --verbose
```

## Support Resources

- **GitHub Issues**: [mcp-toolkit/issues](https://github.com/ChunkyTortoise/mcp-toolkit/issues)
- **FastMCP Docs**: [gofastmcp.com](https://gofastmcp.com)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Live Demo**: [ct-mcp-toolkit.streamlit.app](https://ct-mcp-toolkit.streamlit.app)
- **Portfolio**: [chunkytortoise.github.io](https://chunkytortoise.github.io)

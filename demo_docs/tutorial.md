# Building Custom MCP Servers

## Overview

This tutorial walks through building a custom MCP server using FastMCP. By the end, you'll have a working server with tools, resources, and error handling.

## Step 1: Create the Server

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")
```

## Step 2: Add Tools

Tools are functions that AI models can invoke. Use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

Key rules:
- Functions must have type annotations
- Docstrings become tool descriptions
- Return values are serialized to JSON

## Step 3: Add Resources

Resources provide read-only context:

```python
@mcp.resource("config://settings")
def get_settings() -> str:
    """Return application settings."""
    return json.dumps({"theme": "dark", "lang": "en"})
```

## Step 4: Error Handling

Return clear error messages instead of raising exceptions:

```python
@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide two numbers."""
    if b == 0:
        return "Error: Division by zero"
    return str(a / b)
```

## Step 5: Run the Server

```python
if __name__ == "__main__":
    mcp.run()
```

Launch with: `python my_server.py`

## Best Practices

1. Keep tools focused — one action per tool
2. Use descriptive names and docstrings
3. Validate inputs before processing
4. Return structured data (dicts/lists) for complex results
5. Handle errors gracefully with clear messages

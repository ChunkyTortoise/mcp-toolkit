# Quick Start Guide

## Installation

Install MCP Toolkit from source:

```bash
git clone https://github.com/ChunkyTortoise/mcp-toolkit.git
cd mcp-toolkit
pip install -e .
```

## Verify Installation

```bash
mcp-toolkit version
mcp-toolkit list
```

## Launch a Server

Start the SQLite Explorer server:

```bash
mcp-toolkit serve sqlite-explorer
```

## Configure with Claude Desktop

Generate the config snippet:

```bash
mcp-toolkit config sqlite-explorer
```

Add the output to your Claude Desktop MCP settings file.

## Try the Playground

Launch the Streamlit playground to test servers interactively:

```bash
make demo
```

## Next Steps

- Read the API Guide for endpoint details
- Check the Tutorial for building custom servers
- See the Glossary for MCP terminology

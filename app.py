"""MCP Toolkit Streamlit Playground — test MCP servers interactively."""

from __future__ import annotations

import json
import inspect
import traceback
from typing import get_type_hints

import streamlit as st

from mcp_toolkit.shared.registry import get_server, list_servers

st.set_page_config(page_title="MCP Toolkit Playground", page_icon="🔧", layout="wide")

st.title("MCP Toolkit Playground")
st.caption("Test 6 production-ready MCP servers interactively")

# --- Sidebar: Server selector ---
servers = list_servers()
server_names = [s.name for s in servers]

with st.sidebar:
    st.header("Server")
    selected_name = st.selectbox("Choose a server", server_names)
    server_info = get_server(selected_name)
    if server_info:
        st.markdown(f"**{server_info.description}**")
        st.markdown(f"`{server_info.module}`")
        st.markdown(f"**{len(server_info.tools)} tools** available")

    st.divider()
    st.markdown("### All Servers")
    for s in servers:
        st.markdown(f"- **{s.name}** ({len(s.tools)} tools)")

    st.divider()
    st.caption("Built with [FastMCP](https://gofastmcp.com) + Streamlit")

if not server_info:
    st.error("No server selected.")
    st.stop()

# --- Load the server's MCP instance ---
mcp_instance = server_info.load()
tools = {t.name: t for t in mcp_instance.get_tools()}

# --- Main area: Tool selector ---
st.subheader(f"{server_info.name}")

tool_name = st.selectbox("Select a tool", list(tools.keys()))
tool = tools.get(tool_name)

if not tool:
    st.warning("Select a tool to continue.")
    st.stop()

st.markdown(f"*{tool.description}*" if tool.description else "")

# --- Dynamic argument form ---
st.subheader("Arguments")

# Get the underlying function's signature for type hints
fn = tool.fn
sig = inspect.signature(fn)
hints = get_type_hints(fn)

args = {}
for param_name, param in sig.parameters.items():
    if param_name in ("self", "ctx"):
        continue
    hint = hints.get(param_name, str)
    default = param.default if param.default is not inspect.Parameter.empty else None

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"**{param_name}**")

    with col2:
        hint_str = str(hint)
        if hint in (int, float) or "int" in hint_str or "float" in hint_str:
            args[param_name] = st.number_input(
                param_name,
                value=default if isinstance(default, (int, float)) else 0,
                label_visibility="collapsed",
                key=f"arg_{tool_name}_{param_name}",
            )
        elif hint is bool or "bool" in hint_str:
            args[param_name] = st.checkbox(
                param_name,
                value=default if isinstance(default, bool) else False,
                label_visibility="collapsed",
                key=f"arg_{tool_name}_{param_name}",
            )
        elif "dict" in hint_str or "list" in hint_str:
            raw = st.text_area(
                param_name,
                value=json.dumps(default) if default else "",
                label_visibility="collapsed",
                key=f"arg_{tool_name}_{param_name}",
                height=100,
            )
            if raw.strip():
                try:
                    args[param_name] = json.loads(raw)
                except json.JSONDecodeError:
                    st.error(f"Invalid JSON for {param_name}")
                    args[param_name] = default
            else:
                args[param_name] = default
        else:
            args[param_name] = st.text_input(
                param_name,
                value=str(default) if default is not None else "",
                label_visibility="collapsed",
                key=f"arg_{tool_name}_{param_name}",
            )

# Filter out empty optional args
filtered_args = {}
for k, v in args.items():
    param = sig.parameters[k]
    if v == "" and param.default is not inspect.Parameter.empty:
        continue
    if v is None and param.default is inspect.Parameter.empty:
        continue
    filtered_args[k] = v

# --- Invoke ---
col_invoke, col_count = st.columns([1, 1])

if "invocation_count" not in st.session_state:
    st.session_state.invocation_count = 0

with col_invoke:
    invoke_btn = st.button("Invoke", type="primary", use_container_width=True)

with col_count:
    st.metric("Invocations", st.session_state.invocation_count)

if invoke_btn:
    st.session_state.invocation_count += 1
    st.subheader("Result")

    try:
        result = fn(**filtered_args)
        if isinstance(result, (dict, list)):
            st.json(result)
        else:
            st.code(str(result), language="text")
    except Exception:
        st.error("Tool invocation failed")
        st.code(traceback.format_exc(), language="text")

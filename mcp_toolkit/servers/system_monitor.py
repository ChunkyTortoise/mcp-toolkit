"""Real-time CPU, memory, disk, and network monitoring via psutil.

Exposes system resource metrics as MCP tools for agent-driven
infrastructure observability.
"""

from __future__ import annotations

import psutil
from fastmcp import FastMCP

SERVER_INFO = {
    "name": "system-monitor",
    "description": "Real-time CPU, memory, disk, and network monitoring via psutil",
    "tools": [
        "get_cpu_stats",
        "get_memory_stats",
        "get_disk_stats",
        "get_network_stats",
        "health_check",
    ],
}

mcp = FastMCP(SERVER_INFO["name"])


@mcp.tool()
def get_cpu_stats() -> dict:
    """Return current CPU utilization and hardware details.

    Returns:
        Dictionary with usage_percent, core_count, physical_cores, and frequency_mhz.
    """
    freq = psutil.cpu_freq()
    return {
        "usage_percent": psutil.cpu_percent(interval=0.1),
        "core_count": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 2) if freq else None,
    }


@mcp.tool()
def get_memory_stats() -> dict:
    """Return system memory usage statistics.

    Returns:
        Dictionary with total_gb, used_gb, available_gb, and percent_used.
    """
    mem = psutil.virtual_memory()
    bytes_to_gb = 1024**3
    return {
        "total_gb": round(mem.total / bytes_to_gb, 2),
        "used_gb": round(mem.used / bytes_to_gb, 2),
        "available_gb": round(mem.available / bytes_to_gb, 2),
        "percent_used": mem.percent,
    }


@mcp.tool()
def get_disk_stats(path: str = "/") -> dict:
    """Return disk usage for the specified mount point.

    Args:
        path: Filesystem path or mount point to check. Defaults to "/".

    Returns:
        Dictionary with total_gb, used_gb, free_gb, and percent_used.
    """
    usage = psutil.disk_usage(path)
    bytes_to_gb = 1024**3
    return {
        "total_gb": round(usage.total / bytes_to_gb, 2),
        "used_gb": round(usage.used / bytes_to_gb, 2),
        "free_gb": round(usage.free / bytes_to_gb, 2),
        "percent_used": usage.percent,
    }


@mcp.tool()
def get_network_stats() -> dict:
    """Return network I/O counters and active connection count.

    Returns:
        Dictionary with bytes_sent, bytes_recv, packets_sent, packets_recv,
        and active_connections.
    """
    net = psutil.net_io_counters()
    try:
        connections = psutil.net_connections()
        active_connections = len(connections)
    except psutil.AccessDenied:
        active_connections = -1
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "active_connections": active_connections,
    }


@mcp.tool()
def health_check(
    cpu_threshold: float = 90.0,
    mem_threshold: float = 90.0,
) -> dict:
    """Evaluate system health against CPU and memory thresholds.

    Args:
        cpu_threshold: CPU usage percent that triggers a warning. Defaults to 90.0.
        mem_threshold: Memory usage percent that triggers a warning. Defaults to 90.0.

    Returns:
        Dictionary with overall status ("healthy", "warning", or "critical")
        and per-check details including value, threshold, and passed flag.
    """
    cpu_usage = psutil.cpu_percent(interval=0.1)
    mem_usage = psutil.virtual_memory().percent

    cpu_passed = cpu_usage < cpu_threshold
    mem_passed = mem_usage < mem_threshold

    if cpu_passed and mem_passed:
        status = "healthy"
    elif not cpu_passed and not mem_passed:
        status = "critical"
    else:
        status = "warning"

    return {
        "status": status,
        "checks": {
            "cpu": {
                "value": cpu_usage,
                "threshold": cpu_threshold,
                "passed": cpu_passed,
            },
            "memory": {
                "value": mem_usage,
                "threshold": mem_threshold,
                "passed": mem_passed,
            },
        },
    }

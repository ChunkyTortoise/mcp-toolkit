"""Tests for the system_monitor MCP server."""

from __future__ import annotations

from mcp_toolkit.servers.system_monitor import (
    get_cpu_stats,
    get_disk_stats,
    get_memory_stats,
    get_network_stats,
    health_check,
)


class TestCpuStats:
    def test_get_cpu_stats(self):
        """Returns dict with expected CPU metric keys."""
        result = get_cpu_stats.fn()
        assert isinstance(result, dict)
        assert "usage_percent" in result
        assert "core_count" in result
        assert "physical_cores" in result
        assert "frequency_mhz" in result


class TestMemoryStats:
    def test_get_memory_stats(self):
        """Returns dict with expected memory metric keys."""
        result = get_memory_stats.fn()
        assert isinstance(result, dict)
        assert "total_gb" in result
        assert "used_gb" in result
        assert "available_gb" in result
        assert "percent_used" in result

    def test_memory_values_reasonable(self):
        """Memory values are physically plausible."""
        result = get_memory_stats.fn()
        assert result["total_gb"] > 0
        assert result["available_gb"] <= result["total_gb"]
        assert 0 <= result["percent_used"] <= 100


class TestDiskStats:
    def test_get_disk_stats_root(self):
        """Default path '/' returns expected keys."""
        result = get_disk_stats.fn()
        assert isinstance(result, dict)
        assert "total_gb" in result
        assert "used_gb" in result
        assert "free_gb" in result
        assert "percent_used" in result

    def test_get_disk_stats_values(self):
        """Disk values are physically plausible."""
        result = get_disk_stats.fn(path="/")
        assert result["total_gb"] > 0
        assert 0 <= result["percent_used"] <= 100


class TestNetworkStats:
    def test_get_network_stats(self):
        """Returns dict with expected network metric keys."""
        result = get_network_stats.fn()
        assert isinstance(result, dict)
        assert "bytes_sent" in result
        assert "bytes_recv" in result
        assert "packets_sent" in result
        assert "packets_recv" in result
        assert "active_connections" in result


class TestHealthCheck:
    def test_health_check_healthy(self):
        """Loose thresholds produce a 'healthy' status."""
        result = health_check.fn(cpu_threshold=100.0, mem_threshold=100.0)
        assert result["status"] == "healthy"
        assert result["checks"]["cpu"]["passed"] is True
        assert result["checks"]["memory"]["passed"] is True

    def test_health_check_warning(self):
        """A near-zero memory threshold triggers 'warning' or 'critical'."""
        # Memory usage is always well above 0%, so threshold=0.001 guarantees failure
        result = health_check.fn(cpu_threshold=100.0, mem_threshold=0.001)
        assert result["status"] in ("warning", "critical")
        assert result["checks"]["memory"]["passed"] is False

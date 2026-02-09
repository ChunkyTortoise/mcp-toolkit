"""Tests for the analytics & cost tracking module."""

from __future__ import annotations

from datetime import datetime, timezone

from mcp_toolkit.analytics import (
    AlertEngine,
    AlertRule,
    AnalyticsReport,
    PerformanceStats,
    ToolInvocation,
    ToolStats,
    ToolUsageTracker,
)


class TestToolInvocation:
    def test_defaults(self):
        inv = ToolInvocation(
            tool_name="search",
            timestamp=datetime.now(timezone.utc),
            duration_ms=42.0,
            success=True,
        )
        assert inv.cost == 0.0
        assert inv.metadata == {}

    def test_custom_fields(self):
        inv = ToolInvocation(
            tool_name="query",
            timestamp=datetime.now(timezone.utc),
            duration_ms=100.0,
            success=False,
            cost=0.05,
            metadata={"model": "gpt-4"},
        )
        assert inv.cost == 0.05
        assert inv.metadata["model"] == "gpt-4"


class TestToolStats:
    def test_empty_stats(self):
        stats = ToolStats()
        assert stats.success_rate == 0.0
        assert stats.avg_duration == 0.0

    def test_computed_properties(self):
        stats = ToolStats(count=10, success_count=8, total_duration_ms=500.0, total_cost=1.0)
        assert stats.success_rate == 0.8
        assert stats.avg_duration == 50.0


class TestToolUsageTracker:
    def test_record_returns_invocation(self):
        tracker = ToolUsageTracker()
        inv = tracker.record("search", duration_ms=50.0, success=True)
        assert isinstance(inv, ToolInvocation)
        assert inv.tool_name == "search"

    def test_record_updates_stats(self):
        tracker = ToolUsageTracker()
        tracker.record("search", duration_ms=50.0, success=True, cost=0.01)
        tracker.record("search", duration_ms=100.0, success=False, cost=0.02)
        stats = tracker.get_stats("search")
        assert stats.count == 2
        assert stats.success_count == 1
        assert stats.total_cost == 0.03

    def test_get_stats_unknown_tool(self):
        tracker = ToolUsageTracker()
        stats = tracker.get_stats("nonexistent")
        assert stats.count == 0

    def test_get_all_stats(self):
        tracker = ToolUsageTracker()
        tracker.record("a", duration_ms=10.0, success=True)
        tracker.record("b", duration_ms=20.0, success=True)
        all_stats = tracker.get_all_stats()
        assert "a" in all_stats
        assert "b" in all_stats
        assert len(all_stats) == 2

    def test_get_top_tools_by_count(self):
        tracker = ToolUsageTracker()
        for _ in range(5):
            tracker.record("popular", duration_ms=10.0, success=True)
        tracker.record("rare", duration_ms=10.0, success=True)
        top = tracker.get_top_tools(1, by="count")
        assert top[0][0] == "popular"
        assert top[0][1].count == 5

    def test_get_top_tools_by_cost(self):
        tracker = ToolUsageTracker()
        tracker.record("cheap", duration_ms=10.0, success=True, cost=0.01)
        tracker.record("expensive", duration_ms=10.0, success=True, cost=5.0)
        top = tracker.get_top_tools(1, by="cost")
        assert top[0][0] == "expensive"

    def test_get_top_tools_by_duration(self):
        tracker = ToolUsageTracker()
        tracker.record("fast", duration_ms=1.0, success=True)
        tracker.record("slow", duration_ms=9999.0, success=True)
        top = tracker.get_top_tools(1, by="duration")
        assert top[0][0] == "slow"

    def test_get_top_tools_invalid_key(self):
        tracker = ToolUsageTracker()
        tracker.record("x", duration_ms=1.0, success=True)
        try:
            tracker.get_top_tools(1, by="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_record_with_metadata(self):
        tracker = ToolUsageTracker()
        inv = tracker.record("query", duration_ms=10.0, success=True, metadata={"k": "v"})
        assert inv.metadata == {"k": "v"}


class TestPerformanceStats:
    def test_empty_summary(self):
        ps = PerformanceStats()
        s = ps.summary()
        assert s["count"] == 0
        assert s["mean"] == 0.0

    def test_single_sample(self):
        ps = PerformanceStats()
        ps.add_sample(42.0)
        assert ps.p50 == 42.0
        assert ps.p95 == 42.0
        assert ps.summary()["std"] == 0.0

    def test_multiple_samples_percentiles(self):
        ps = PerformanceStats()
        for v in range(1, 101):
            ps.add_sample(float(v))
        assert ps.p50 > 0
        assert ps.p95 > ps.p50
        assert ps.p99 > ps.p95

    def test_summary_keys(self):
        ps = PerformanceStats()
        ps.add_sample(10.0)
        ps.add_sample(20.0)
        s = ps.summary()
        assert set(s.keys()) == {"min", "max", "mean", "std", "p50", "p95", "p99", "count"}
        assert s["min"] == 10.0
        assert s["max"] == 20.0


class TestAlertRule:
    def test_defaults(self):
        rule = AlertRule(name="high-latency", metric="p99", threshold=500.0)
        assert rule.operator == "gt"
        assert rule.cooldown_seconds == 60


class TestAlertEngine:
    def test_no_rules_no_alerts(self):
        engine = AlertEngine()
        alerts = engine.check({"p99": 1000.0})
        assert alerts == []

    def test_gt_trigger(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("high-p99", "p99", 500.0, operator="gt", cooldown_seconds=0))
        alerts = engine.check({"p99": 600.0})
        assert len(alerts) == 1
        assert alerts[0].rule_name == "high-p99"

    def test_lt_trigger(self):
        engine = AlertEngine()
        rule = AlertRule("low-success", "success_rate", 0.9, operator="lt", cooldown_seconds=0)
        engine.add_rule(rule)
        alerts = engine.check({"success_rate": 0.5})
        assert len(alerts) == 1

    def test_eq_trigger(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("exact", "count", 0.0, operator="eq", cooldown_seconds=0))
        alerts = engine.check({"count": 0.0})
        assert len(alerts) == 1

    def test_no_trigger_below_threshold(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("high-p99", "p99", 500.0, operator="gt", cooldown_seconds=0))
        alerts = engine.check({"p99": 200.0})
        assert alerts == []

    def test_cooldown_prevents_refire(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("high-p99", "p99", 500.0, operator="gt", cooldown_seconds=300))
        alerts1 = engine.check({"p99": 600.0})
        assert len(alerts1) == 1
        alerts2 = engine.check({"p99": 700.0})
        assert alerts2 == []

    def test_missing_metric_skipped(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("high-p99", "p99", 500.0, operator="gt", cooldown_seconds=0))
        alerts = engine.check({"other_metric": 999.0})
        assert alerts == []


class TestAnalyticsReport:
    def test_report_fields(self):
        report = AnalyticsReport(
            tool_stats={"search": ToolStats(count=5)},
            performance={"p50": 10.0},
            alerts=[],
        )
        assert report.tool_stats["search"].count == 5
        assert isinstance(report.generated_at, datetime)

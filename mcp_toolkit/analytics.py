"""Analytics & cost tracking for MCP tool invocations."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ToolInvocation:
    """Record of a single tool invocation."""

    tool_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    cost: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolStats:
    """Aggregate statistics for a single tool."""

    count: int = 0
    success_count: int = 0
    total_duration_ms: float = 0.0
    total_cost: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.count == 0:
            return 0.0
        return self.success_count / self.count

    @property
    def avg_duration(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total_duration_ms / self.count


class ToolUsageTracker:
    """Track per-tool invocation statistics."""

    def __init__(self) -> None:
        self._invocations: list[ToolInvocation] = []
        self._stats: dict[str, ToolStats] = {}

    def record(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        cost: float = 0.0,
        metadata: dict | None = None,
    ) -> ToolInvocation:
        """Record a tool invocation and update aggregate stats."""
        inv = ToolInvocation(
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            success=success,
            cost=cost,
            metadata=metadata or {},
        )
        self._invocations.append(inv)

        if tool_name not in self._stats:
            self._stats[tool_name] = ToolStats()
        stats = self._stats[tool_name]
        stats.count += 1
        if success:
            stats.success_count += 1
        stats.total_duration_ms += duration_ms
        stats.total_cost += cost
        return inv

    def get_stats(self, tool_name: str) -> ToolStats:
        """Get aggregate stats for a specific tool."""
        return self._stats.get(tool_name, ToolStats())

    def get_all_stats(self) -> dict[str, ToolStats]:
        """Get stats for all tracked tools."""
        return dict(self._stats)

    def get_top_tools(self, n: int, by: str = "count") -> list[tuple[str, ToolStats]]:
        """Get top N tools ranked by count, cost, or duration."""
        key_map = {
            "count": lambda item: item[1].count,
            "cost": lambda item: item[1].total_cost,
            "duration": lambda item: item[1].total_duration_ms,
        }
        if by not in key_map:
            raise ValueError(f"Invalid sort key '{by}'; use 'count', 'cost', or 'duration'")
        items = sorted(self._stats.items(), key=key_map[by], reverse=True)
        return items[:n]


class PerformanceStats:
    """Latency distribution analysis with percentile tracking."""

    def __init__(self) -> None:
        self._samples: list[float] = []

    def add_sample(self, value: float) -> None:
        """Add a latency sample."""
        self._samples.append(value)

    def percentile(self, p: float) -> float:
        """Compute the p-th percentile (0-100)."""
        if not self._samples:
            return 0.0
        sorted_samples = sorted(self._samples)
        n = len(sorted_samples)
        if n == 1:
            return sorted_samples[0]
        k = (p / 100.0) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_samples[int(k)]
        return sorted_samples[f] + (k - f) * (sorted_samples[c] - sorted_samples[f])

    @property
    def p50(self) -> float:
        return self.percentile(50)

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    def summary(self) -> dict:
        """Return summary statistics."""
        if not self._samples:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "std": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "count": 0,
            }
        return {
            "min": min(self._samples),
            "max": max(self._samples),
            "mean": statistics.mean(self._samples),
            "std": statistics.stdev(self._samples) if len(self._samples) > 1 else 0.0,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "count": len(self._samples),
        }


@dataclass
class AlertRule:
    """Configurable alert rule definition."""

    name: str
    metric: str
    threshold: float
    operator: str = "gt"  # "gt", "lt", "eq"
    cooldown_seconds: int = 60


@dataclass
class Alert:
    """A triggered alert instance."""

    rule_name: str
    current_value: float
    threshold: float
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AlertEngine:
    """Configurable alerting engine with cooldown support."""

    def __init__(self) -> None:
        self._rules: list[AlertRule] = []
        self._last_fired: dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule."""
        self._rules.append(rule)

    def check(self, metrics: dict[str, float]) -> list[Alert]:
        """Check all rules against provided metrics, respecting cooldowns."""
        now = datetime.now(timezone.utc)
        alerts: list[Alert] = []
        for rule in self._rules:
            if rule.metric not in metrics:
                continue
            value = metrics[rule.metric]
            triggered = False
            if rule.operator == "gt" and value > rule.threshold:
                triggered = True
            elif rule.operator == "lt" and value < rule.threshold:
                triggered = True
            elif rule.operator == "eq" and value == rule.threshold:
                triggered = True

            if triggered:
                last = self._last_fired.get(rule.name)
                if last and (now - last).total_seconds() < rule.cooldown_seconds:
                    continue
                self._last_fired[rule.name] = now
                alerts.append(
                    Alert(
                        rule_name=rule.name,
                        current_value=value,
                        threshold=rule.threshold,
                        triggered_at=now,
                    )
                )
        return alerts


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""

    tool_stats: dict[str, ToolStats]
    performance: dict
    alerts: list[Alert]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

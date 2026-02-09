"""MCP Toolkit Performance Benchmarks."""
import time
import random
import json
from pathlib import Path

random.seed(42)


def percentile(data, p):
    k = (len(data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(data) else f
    return data[f] + (k - f) * (data[c] - data[f])


# --- Synthetic data ---

SAMPLE_TOOLS = {
    f"tool_{i}": {
        "name": f"tool_{i}",
        "description": f"Tool number {i} that does something useful",
        "inputSchema": {
            "type": "object",
            "properties": {
                "arg1": {"type": "string"},
                "arg2": {"type": "integer"},
            },
            "required": ["arg1"],
        },
    }
    for i in range(100)
}

SAMPLE_SERVERS = {
    f"server_{i}": {
        "name": f"server_{i}",
        "url": f"http://localhost:{3000 + i}",
        "tools": [f"tool_{j}" for j in range(i * 10, min(i * 10 + 10, 100))],
        "status": random.choice(["active", "active", "active", "inactive"]),
        "version": f"1.{random.randint(0, 9)}.{random.randint(0, 20)}",
    }
    for i in range(10)
}


# --- Benchmarks ---

def benchmark_jsonrpc_serialization():
    """JSON-RPC message serialization/deserialization."""
    requests = []
    for i in range(50):
        requests.append({
            "jsonrpc": "2.0",
            "id": i,
            "method": f"tools/{random.choice(list(SAMPLE_TOOLS.keys()))}",
            "params": {
                "arg1": f"value_{random.randint(1, 1000)}",
                "arg2": random.randint(1, 100),
                "nested": {"key": f"data_{i}", "list": list(range(10))},
            },
        })
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        for req in requests:
            serialized = json.dumps(req)
            deserialized = json.loads(serialized)
            # Validate structure
            assert deserialized["jsonrpc"] == "2.0"
            assert "method" in deserialized
            # Build response
            response = json.dumps({
                "jsonrpc": "2.0",
                "id": deserialized["id"],
                "result": {"status": "ok", "data": deserialized["params"]},
            })
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "JSON-RPC Serialize/Deserialize (50 msgs)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_tool_dispatch():
    """Tool dispatch: route method to handler simulation."""
    tool_handlers = {}
    for name in SAMPLE_TOOLS:
        # Simulate handler registration
        tool_handlers[name] = lambda params, n=name: {
            "tool": n,
            "result": f"executed with {len(params)} params",
        }

    methods = [f"tool_{random.randint(0, 99)}" for _ in range(200)]
    param_sets = [{"arg1": f"val_{i}", "arg2": i} for i in range(200)]

    times = []
    for _ in range(1000):
        start = time.perf_counter()
        for method, params in zip(methods, param_sets):
            # Lookup
            handler = tool_handlers.get(method)
            if handler:
                # Validate required params
                schema = SAMPLE_TOOLS[method]["inputSchema"]
                required = schema.get("required", [])
                missing = [r for r in required if r not in params]
                if not missing:
                    result = handler(params)
                else:
                    result = {"error": f"missing: {missing}"}
            else:
                result = {"error": "unknown tool"}
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Tool Dispatch + Validation (200 calls)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_server_registry_lookup():
    """Server registry: find tool owners, health checks."""
    # Build reverse index: tool -> server
    tool_to_server = {}
    for sname, sdata in SAMPLE_SERVERS.items():
        for tool in sdata["tools"]:
            tool_to_server[tool] = sname

    lookup_tools = [f"tool_{random.randint(0, 99)}" for _ in range(300)]

    times = []
    for _ in range(1000):
        start = time.perf_counter()
        for tool_name in lookup_tools:
            # Find owning server
            server_name = tool_to_server.get(tool_name)
            if server_name:
                server = SAMPLE_SERVERS[server_name]
                # Health check simulation
                is_healthy = server["status"] == "active"
                # Version compatibility check
                major, minor, patch = server["version"].split(".")
                is_compatible = int(major) >= 1
                can_route = is_healthy and is_compatible
            else:
                can_route = False
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Server Registry Lookup (300 lookups)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_capability_negotiation():
    """Capability negotiation: match client needs to server features."""
    client_requests = [
        {"required_tools": [f"tool_{random.randint(0, 99)}" for _ in range(random.randint(1, 5))],
         "min_version": f"1.{random.randint(0, 5)}.0"}
        for _ in range(100)
    ]
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        for req in client_requests:
            matches = []
            for sname, sdata in SAMPLE_SERVERS.items():
                if sdata["status"] != "active":
                    continue
                server_tools = set(sdata["tools"])
                needed = set(req["required_tools"])
                coverage = len(needed & server_tools) / max(len(needed), 1)
                # Version check
                sv = tuple(int(x) for x in sdata["version"].split("."))
                rv = tuple(int(x) for x in req["min_version"].split("."))
                version_ok = sv >= rv
                if coverage > 0 and version_ok:
                    matches.append((sname, coverage))
            # Sort by coverage descending
            matches.sort(key=lambda x: -x[1])
            best = matches[0] if matches else None
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Capability Negotiation (100 requests)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def main():
    results = []
    benchmarks = [
        benchmark_jsonrpc_serialization,
        benchmark_tool_dispatch,
        benchmark_server_registry_lookup,
        benchmark_capability_negotiation,
    ]
    for bench in benchmarks:
        print(f"Running {bench.__doc__.strip()}...")
        r = bench()
        results.append(r)
        print(f"  P50: {r['p50']}ms | P95: {r['p95']}ms | P99: {r['p99']}ms | {r['ops_sec']} ops/sec")

    out = Path(__file__).parent / "RESULTS.md"
    with open(out, "w") as f:
        f.write("# MCP Toolkit Benchmark Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |\n")
        f.write("|-----------|-----------|----------|----------|----------|------------|\n")
        for r in results:
            f.write(f"| {r['op']} | {r['n']:,} | {r['p50']} | {r['p95']} | {r['p99']} | {r['ops_sec']:,.0f} ops/sec |\n")
        f.write("\n> All benchmarks use synthetic data. No external services required.\n")
    print(f"\nResults: {out}")


if __name__ == "__main__":
    main()

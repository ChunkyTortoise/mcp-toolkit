# MCP Toolkit -- Benchmarks

Performance benchmarks for core MCP operations. All benchmarks use synthetic data with deterministic seeding (`random.seed(42)`) for reproducibility. No external services or network access required.

## Methodology

Each benchmark runs the target operation in a tight loop for 1,000 iterations, measuring wall-clock time via `time.perf_counter()`. Results report P50, P95, and P99 latencies plus throughput in operations per second.

- **Environment**: Python 3.11+, single-threaded, no I/O
- **Data**: 100 synthetic tool definitions, 10 server registrations
- **Warm-up**: None (cold-start included in measurements)

## Results

| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|-----------|-----------|----------|----------|----------|------------|
| JSON-RPC Serialize/Deserialize (50 msgs) | 1,000 | 0.35 | 0.61 | 0.70 | 2,645 ops/sec |
| Tool Dispatch + Validation (200 calls) | 1,000 | 0.06 | 0.17 | 0.21 | 11,987 ops/sec |
| Server Registry Lookup (300 lookups) | 1,000 | 0.04 | 0.14 | 0.17 | 15,562 ops/sec |
| Capability Negotiation (100 requests) | 1,000 | 0.96 | 1.47 | 1.65 | 1,000 ops/sec |

## Benchmark Descriptions

### JSON-RPC Serialize/Deserialize
Serializes and deserializes 50 JSON-RPC request/response pairs per iteration using `json.dumps`/`json.loads`. Validates structure and builds response payloads. Measures protocol message handling overhead.

### Tool Dispatch + Validation
Routes 200 tool calls through a handler lookup table, validates required parameters against input schemas, and executes handlers. Measures the per-call dispatch overhead for the tool execution path.

### Server Registry Lookup
Performs 300 reverse-index lookups (tool name to owning server), checks server health status, and validates version compatibility. Measures registry query performance at scale.

### Capability Negotiation
Matches 100 client capability requests against 10 servers, computing tool coverage scores and version compatibility. Sorts matches by coverage to find the best server. Measures the most complex routing operation.

## How to Reproduce

```bash
git clone https://github.com/ChunkyTortoise/mcp-toolkit.git
cd mcp-toolkit
pip install -e .
python benchmarks/run_benchmarks.py
```

Raw results are written to `benchmarks/RESULTS.md`.

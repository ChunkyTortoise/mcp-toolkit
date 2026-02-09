# MCP Toolkit Benchmark Results

**Date**: 2026-02-09 03:37:29

| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|-----------|-----------|----------|----------|----------|------------|
| JSON-RPC Serialize/Deserialize (50 msgs) | 1,000 | 0.3534 | 0.6054 | 0.6988 | 2,645 ops/sec |
| Tool Dispatch + Validation (200 calls) | 1,000 | 0.0573 | 0.1728 | 0.2083 | 11,987 ops/sec |
| Server Registry Lookup (300 lookups) | 1,000 | 0.0434 | 0.1355 | 0.1699 | 15,562 ops/sec |
| Capability Negotiation (100 requests) | 1,000 | 0.9638 | 1.4689 | 1.6479 | 1,000 ops/sec |

> All benchmarks use synthetic data. No external services required.

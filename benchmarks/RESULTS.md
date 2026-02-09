# MCP Toolkit Benchmark Results

**Date**: 2026-02-09 03:34:09

| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|-----------|-----------|----------|----------|----------|------------|
| JSON-RPC Serialize/Deserialize (50 msgs) | 1,000 | 0.2418 | 0.2491 | 0.2869 | 4,122 ops/sec |
| Tool Dispatch + Validation (200 calls) | 1,000 | 0.0478 | 0.0503 | 0.0541 | 20,793 ops/sec |
| Server Registry Lookup (300 lookups) | 1,000 | 0.0407 | 0.0433 | 0.0465 | 24,404 ops/sec |
| Capability Negotiation (100 requests) | 1,000 | 0.673 | 0.7143 | 0.9058 | 1,466 ops/sec |

> All benchmarks use synthetic data. No external services required.

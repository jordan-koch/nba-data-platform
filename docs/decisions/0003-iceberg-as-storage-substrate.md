# 0003 — Apache Iceberg on S3 as the storage substrate

**Status:** accepted · 2026-08-12

## Context

The initial framing was "which warehouse — Snowflake or Databricks?" That question assumes the
warehouse owns the data, which makes the choice expensive to reverse: migrating later means
rewriting storage, not just connection strings.

The project explicitly expects to grow into new sources and possibly new compute engines, and
the compute decision is the one with the least information available today.

## Decision

**The system of record is Iceberg tables in S3, not a warehouse.** Compute is a swappable layer
on top.

Iceberg specifically, because the industry converged on it — Snowflake reads and writes it
natively, Databricks supports it and bought Tabular, AWS ships S3 Tables as managed Iceberg, and
Trino, Spark, Flink, and DuckDB all speak it.

## Consequences

**Buys:**

- **The engine decision defers** until there's a workload that discriminates between candidates.
  Snowflake now and Databricks later becomes a profile change, not a migration.
- **Right engine per workload** — Snowflake for dbt transforms and BI queries, Spark for eventual
  tracking-scale work, DuckDB for free local development against the same files.
- **No vendor lock-in on the data itself.** The files remain readable if every vendor
  relationship ends.
- Time travel and snapshot isolation come free, which matters for as-of queries and for
  reproducing what a model saw at training time.

**Costs — this is the clearest case of [ADR 0001](0001-deliberate-over-engineering.md) in the
project:**

- At current volume, **a directory of Parquet files would work identically** and be simpler. The
  entire dataset fits in RAM.
- A catalog is now a component that must exist, be configured, and be maintained.
- Iceberg tables need periodic maintenance — compaction, snapshot expiry, orphan cleanup — that
  plain Parquet doesn't.
- More concepts to hold: manifests, snapshots, partition specs, schema evolution semantics.

**Forecloses:** nothing meaningful. Iceberg tables can always be read out to plain Parquet.

## Alternatives considered

**Plain partitioned Parquet on S3.** Genuinely sufficient for this data and much simpler.
Rejected because it provides no ACID guarantees, no schema evolution, no time travel, and no
clean upsert path — and box scores get restated, so upserts are a hard requirement, not a
convenience.

**Delta Lake.** Technically comparable and better integrated with Databricks specifically.
Rejected because Iceberg has broader cross-engine support, and cross-engine portability is the
entire point of this decision.

**Let the warehouse own storage.** Simplest, and what most projects do. Rejected because it makes
the engine choice permanent, and that choice is the one with the least information available now.

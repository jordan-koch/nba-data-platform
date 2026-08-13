# 0004 — Snowflake first; Databricks as a later phase

**Status:** accepted · 2026-08-12

## Context

With [Iceberg](0003-iceberg-as-storage-substrate.md) as the substrate, the engine choice is
reversible — but one still has to go first, and the author's learning goals are part of the
decision. Current professional experience is Azure: Functions, Blob, SQL Server, dbt, Power BI.
The stated growth targets are AWS, Airflow, and a cloud warehouse.

Databricks is a real candidate and appears constantly in job postings. But it wants to absorb
most of the stack — notebooks and jobs replace the extraction layer, Lakeflow replaces Airflow,
SQL Warehouse replaces the warehouse. Adopting it wholesale would mean thin reps on AWS and
Airflow, the two things explicitly being targeted.

There is also an honest scale point: Spark's value proposition is data that doesn't fit on one
machine. This data fits in RAM. On this project Spark is pure overhead.

## Decision

**Snowflake as the first engine. Databricks as a deliberate, separate later phase**, once the
pipeline works end to end.

## Consequences

**Buys:**

- The new material is well-targeted — cloud warehouse, AWS, and orchestration — rather than
  those plus Spark, cluster configuration, and Delta internals simultaneously.
- Existing SQL Server and dbt experience transfers almost directly, so effort goes to what's
  actually unfamiliar.
- Cheap. An XS warehouse with 60-second auto-suspend running a nightly dbt build lands in
  single-digit dollars per month at this volume.
- **The eventual port becomes a strong portfolio artifact in itself**: the same medallion models
  on two engines, with a written comparison of cost and performance. That's a better interview
  story than having used either one.

**Costs:**

- Databricks experience is deferred, and it is the more in-demand line item today.
- Two engines eventually means two sets of profiles, two cost surfaces, and two behaviors to
  keep straight — real ongoing overhead once phase two lands.
- Some Snowflake-specific SQL may need adjusting at port time. Mitigated by linting against the
  build target and keeping models portable, but not eliminated.

**Forecloses:** nothing. The substrate decision is what keeps this reversible.

## Alternatives considered

**Databricks first.** Strongest résumé signal and covers the lakehouse story in one platform.
Rejected because it would crowd out the AWS and Airflow reps that were the actual goal, and
because Spark solves a problem this project does not have.

**Both simultaneously.** Rejected as a way to learn neither well while paying for both.

**Neither — DuckDB only.** Genuinely sufficient for the data, and it remains the local
development target. Rejected because "I ran DuckDB on my laptop" doesn't demonstrate the cloud
warehouse operation the project exists to demonstrate.

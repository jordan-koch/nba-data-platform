# 0001 — Build past current need, and document the delta

**Status:** accepted · 2026-08-12

## Context

This project is simultaneously a working analytics platform and a portfolio artifact. Those two
goals pull in opposite directions.

The dataset is small. Every box score, every play, and every shot from 2003-04 to today is
**single-digit gigabytes** — it fits in RAM on a laptop. A correct minimal solution is a Python
script writing Parquet to a directory, queried with DuckDB. That would work, cost nothing, and
demonstrate almost nothing.

But the second goal is real: the platform should demonstrate the practices a professional data
team uses, on tooling that employers ask for.

The failure mode is picking the wrong thing to inflate. Infrastructure sized far past its
workload reads as *poor judgment* — Kafka in front of 30K rows a night says the author doesn't
understand tradeoffs. That's worse than a simple solution.

## Decision

**Over-engineer the practices. Right-size the infrastructure. Document every place the two
diverge.**

- **Turned all the way up**, because they're free of scale and are what actually gets evaluated:
  testing, CI/CD, data contracts, lineage, governance, incident process, documentation, IaC.
- **Sized to a plausible future, not a fictional present**: an open table format, a medallion
  architecture, orchestration with real backfill semantics.
- **Explicitly declined**: streaming, a distributed compute engine, and a real-time serving path,
  until a workload actually demands one.

Where the platform does reach past current need, the ADR states plainly what the simpler option
would have been and what the added complexity costs.

## Consequences

**Buys:** the parts a hiring manager evaluates are genuinely strong. Every "why did you do it
that way" question has a written answer. And the practices are the parts that transfer to real
work — a tested, documented, gated pipeline is right at any scale, while an oversized cluster is
right at none.

**Costs:** real, and worth naming.

- Iceberg over plain Parquet adds catalog and maintenance complexity that buys nothing at
  current volume.
- The full request pipeline is heavy for small changes. Mitigated by the explicit
  skip-stages-when-small rule, but the temptation to over-process is a standing risk.
- Documenting the delta is ongoing work, and an ADR set that goes stale is worse than none.

**Forecloses:** nothing technical. The main risk is time — a platform elaborate enough to never
produce an actual basketball insight would fail both goals at once. The vertical-slice rule
exists to prevent that: every phase goes source-to-published before the next one widens.

## Alternatives considered

**Build minimally, add complexity when needed.** Correct engineering advice, rejected because the
need may never arrive — the data is small and will stay small. Waiting for justification means
never demonstrating the skills the project exists to demonstrate.

**Build maximally and skip the justification.** Faster, and produces the same artifacts. Rejected
because unexplained over-engineering is a negative signal, not a neutral one. The document *is*
the demonstration of judgment.

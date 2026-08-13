# 0002 — Cover 2003-04 through present

**Status:** accepted · 2026-08-12

## Context

Source coverage varies enormously by era. Traditional box scores reach back to 1946-47;
play-by-play and shot coordinates to roughly 1996-97; tracking-derived aggregates only to
2013-14. Each boundary is a schema special case and a modeling decision.

Three candidate ranges:

- **Full history (1946→)** — richest dataset, but five availability boundaries, several rule
  eras, franchise relocations and mergers, and a lot of extraction.
- **Tracking era (2013-14→)** — uniform stat availability, cleanest models, fastest to a
  working product. Loses two decades of context.
- **Something in between**, anchored to something meaningful.

## Decision

**2003-04 through the current season.**

The anchor is LeBron James's rookie year, so a single transformational career sits entirely
inside the dataset — useful for longitudinal analysis and a natural narrative spine for anything
published from this project.

## Consequences

**Buys:**

- **Exactly one availability boundary** inside the range — tracking-derived stats at 2013-14.
  One nullable-by-era case is very manageable; five is a schema design problem.
- 23 seasons is enough history for meaningful trend analysis and eventual model training.
- A complete LeBron career, which is genuinely interesting and gives published work an angle.

**Costs:**

- **The first season straddles a rule change.** Hand-checking was banned starting 2004-05, and
  it measurably shifted scoring, pace, and drive frequency. 2003-04 sits alone on the far side
  of a real discontinuity, so any comparison spanning it must say so.
- **Three irregular seasons are inside the range** — 2011-12 (lockout, 66 games), 2019-20
  (suspended, bubble, unequal game counts), 2020-21 (compressed, 72 games). Anything assuming 82
  games or an October-to-April calendar breaks on all three. Treated as a feature: they are the
  best test cases available and belong in the fixture set.
- Pre-2003 analysis is unavailable without a later extension.

**Forecloses:** nothing permanently. Extending backward is its own feature request, and the era
handling it needs is deliberately deferred rather than absorbed while also learning the rest of
the stack.

## Alternatives considered

**Start at 2013-14.** Simplest and fastest — zero era boundaries, uniform columns. Rejected as
too thin on history; a decade is not much for trend work, and it would have excluded most of
LeBron's career, which was the point of the anchor.

**Full history from 1946.** Most impressive on paper. Rejected because the era-handling work is
substantial and would have been absorbed alongside learning Airflow, Iceberg, and Snowflake at
the same time. It deserves deliberate design, which means its own slice.

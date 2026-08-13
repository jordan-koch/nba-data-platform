# Requests

The project's work intake — three parallel tracks under one inbox. Every substantial change
enters here, including **every new dataset**: nothing gets extracted, landed, or modeled
without a request behind it.

| Track | For | Start with |
|---|---|---|
| **[feature-requests/](feature-requests/)** | New capability — a data source, a model, a skill, infrastructure | `/make-feature-request` |
| **[bugfix-requests/](bugfix-requests/)** | A defect in existing code, config, or tooling | `/make-bugfix-request` |
| **[data-incidents/](data-incidents/)** | The pipeline ran green and the **data is wrong** | see that track's README |

Each track's **README is the contract** — layout, status grammar, the live Index, and the
`_done/` archive convention. The back half (`/create-implementation-plan` → `/implement-plan`)
is shared and auto-detects the track from the artifact's path.

## Why three tracks and not two

A code bug and a data defect look similar and triage completely differently.

`assert_unique` failing on `fact_player_game` is not a crash — the code did exactly what it
was told. The question is *which* of four things went wrong: the **source** changed shape or
semantics, the **extractor** dropped or duplicated rows, the **model** got the grain or the
join wrong, or the **infrastructure** delivered a partial load. Each has a different
investigation and a different fix.

Data incidents also carry a second obligation code bugs don't: **fixing forward is only half
the work.** The bad rows are already in the warehouse and may already be published. Every
incident owes a restatement plan alongside the fix.

See [data-incidents/README.md](data-incidents/README.md).

## Principles

Two rules run through every panel in every track:

- **Greedy, but gated.** Agents propose *everything* — generating options is cheap, so be
  ambitious. Scope-growing or expensive ideas get **tiered and deferred for your decision**,
  never silently folded into the build.
- **Generate → converge → triage → you decide.** Adversarial agents record *all* findings with
  severity and confidence and never self-censor. The merge step builds the convergence map and
  surfaces the gated calls. **You** dispose them — the panel proposes, you decide.

And one that matters more here than in a typical repo:

- **Label your epistemics.** *Measured*, *verified*, *inferred*, *assumed*, *unconfirmed* are
  different words and mean different things. A request that says "this endpoint returns 30 rows
  per game" when nobody has called it is a liability. Say `unconfirmed` and it becomes a task.

## Weight

Not every change needs three stages. A one-line fix does not need a scoping panel.

> Skip stages when the work is small; lean on the full pipeline when the work is big, risky,
> or hard to hand off cold.

The panels cost real tokens and several minutes. They earn it on decisions that are expensive
to reverse — a dimensional grain, a partitioning scheme, a source contract — and waste it on
work whose shape is already obvious.

See [CLAUDE.md](../CLAUDE.md) for where this sits in the repo.

# Feature Requests

Home for every substantial new piece of work — a new data source, a new model layer, a new
skill, new infrastructure. The point is a **light, repeatable set of guardrails** around how an
idea travels from *"I want X"* to *"a cold agent can implement X"* — without turning a one-hour
change into a week of process.

> **Bugs go elsewhere.** A **defect** in existing code has its own track
> ([`../bugfix-requests/`](../bugfix-requests/)). **Wrong data** from code that ran green has a
> third ([`../data-incidents/`](../data-incidents/)). Tie-break: missing = feature,
> broken-that-exists = bug, ran-clean-but-wrong = incident.

## The pipeline

| # | Stage | Skill | Produces | Shape |
|---|---|---|---|---|
| 1 | **Intake** | `/make-feature-request` | `FEATURE_REQUEST.md` | Interview — turns a raw idea into a scoped, repo-grounded request. Fast, single-agent. |
| 2 | **Scope** | `/scope-feature` | `PROJECT_SCOPE.md` | Panel: 3 divergent scopers → merge/converge → 2 adversarial. Settles fit + testable acceptance criteria. |
| 3 | **Plan** | `/create-implementation-plan` | `IMPLEMENTATION_PLAN.md` | Panel: 3 planners → merge → 2 code-grounded adversaries + 1 meta-audit. Cold-handoff plan. |
| 4 | **Implement** | `/implement-plan` | code + `IMPLEMENTATION_REPORT.md` | Panel: core reviewers + auto-scaled specialists → execution-based verify → meta-audit. Proves every acceptance criterion by running it. |

Each stage produces one artifact and is **human-gated** — you review and edit before invoking
the next. A tiny change might only need a request; a well-understood one might jump straight to
a plan.

## Every dataset comes from here

This is a project convention, not a suggestion. No source gets extracted, no table gets
landed, and no model gets written without a request behind it. The reason is that a dataset
carries **contracts** — a grain, a set of keys, a freshness expectation, an upstream dependency
that can change without warning — and those are decisions, not implementation details.

A dataset request must settle, before any code:

- **Grain.** One row per *what*? "Player per game" and "player per team-stint per game" are
  different tables and the difference is invisible until a mid-season trade breaks a join.
- **Keys.** What makes a row unique, and is that enforceable as a `unique` test?
- **Era coverage.** Which seasons does this source actually have? Structurally-absent data is
  not missing data, and conflating them produces silently wrong averages. See
  [`docs/data-sources.md`](../../docs/data-sources.md).
- **Update semantics.** Append-only, or does history get restated? Box scores get corrected
  after the fact, so most facts here are `MERGE`-on-key, not `INSERT`.
- **Cost.** How many API calls for a full backfill, at what pacing, over what wall-clock?

## Acceptance criteria for data work

"Testable" has a specific meaning in this repo. An acceptance criterion is testable when a
**cold agent can run one command and get a pass or fail** — not when a human can eyeball a
number and nod.

For pipeline work that usually means a dbt test, and the criterion names it:

- ✅ *`fact_player_game` passes `unique` on `(game_id, player_id)` across all 23 seasons.*
- ✅ *For every team-game, the sum of player points equals the team total — `dbt test --select assert_player_points_reconcile` is green.*
- ❌ *The box scores look right.*

Criteria that can only be proven by a human running something (a cloud backfill, a visual
check) are legitimate but must be **marked user-run** so the acceptance panel doesn't claim
them.

## Layout

The directory **is** the unit of work:

```
feature-requests/
  <slug>/                      # kebab-case, descriptive (e.g. box-score-foundation)
    FEATURE_REQUEST.md         # stage 1
    PROJECT_SCOPE.md           # stage 2
    IMPLEMENTATION_PLAN.md     # stage 3
    IMPLEMENTATION_REPORT.md   # stage 4 — acceptance ledger + what shipped
    reviews/                   # evidence (tracked) + panel working files (gitignored)
  _done/<slug>/                # archived once it reaches a terminal stage
```

**What in `reviews/` is tracked.** Evidence is: probe results, agent handoffs, tree-integrity
records, verification write-ups. Those are what a criterion is proven *by*, so they are committed
and CI sees them. The panels' raw serialized output — `*-proposals.md` and `*-adversarial.md`,
often 100 KB+ each — is **gitignored working material**, because everything the final artifact
depends on is carried verbatim *into* that artifact, which therefore stands alone in a fresh
clone. Reference the ignored files as **inline code, never as Markdown links**: they are absent
from a clone, and `tests/test_doc_links.py` is not gitignore-aware, so a link to one passes
locally and fails in CI.

**Active-vs-done.** An item lives at the track root while in flight; when it reaches the
terminal stage — `implemented` — it moves **once** into `_done/`. That single move is the only
lifecycle action, so a plain `ls feature-requests/` shows only active work. The Index keeps the
row with its link pointing into `_done/`.

Every artifact opens with a status blockquote:

> **Status:** &lt;stage&gt; · created &lt;YYYY-MM-DD&gt; · &lt;open | decided&gt; · next: &lt;stage or "implement"&gt;

**Status grammar:** `intake` → `scoped` → `planned` → `implemented`

## Index

| Feature | Stage | Notes |
|---|---|---|
| [box-score-foundation](box-score-foundation/) | scoped | Phase 1. Extraction → landing → bronze → silver dimensional core, local. Gate 0 **verified** the `leaguegamelog` bulk-endpoint belief (one call = one season, both grains); derives SCD2 player-team affiliation from observed box scores, in its own stint model. |
| [data-engineer-agent](data-engineer-agent/) | implemented | **Tooling, not pipeline** — the feature *is* a subagent that owns implementation work, with its own definition and an editable memory file. Would be the repo's first write-capable subagent. |

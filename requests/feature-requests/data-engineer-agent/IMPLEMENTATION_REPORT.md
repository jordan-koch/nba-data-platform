> **Status:** implemented · created 2026-08-14 · decided · next: commit

# Implementation Report — Data-Engineer Agent

> **One-line outcome:** the repo has its first write-capable implementation subagent, its
> build rulebook has a single owner, and both are enforced by required CI checks and proven
> by three live runs · **Acceptance:** 15/16 criteria met, 1 pending the user's PR ·
> **Branch:** `feature/data-engineer-agent`

## 1. Acceptance ledger

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | MECHANICAL — `.claude/agents/` guard, exactly one definition, valid frontmatter | **met** | `test_agents_directory_holds_exactly_one_definition` in the 40-test green run. Discriminates by frontmatter, not file count; glob-discovered |
| 2 | MECHANICAL — guardrail clauses (5 git verbs + never commit/merge/push/amend) | **met** | `test_definition_states_git_is_read_only`, `test_definition_forbids_commit_merge_push_amend`, each with a negative control |
| 3 | WITHDRAWN → replaced by `CLAUDE.md`-pointer guard | **met** | `test_claude_md_points_at_the_definition`, asserting the glob-discovered definition's literal path |
| 4 | MECHANICAL — memory budget, referenced by path, cap named in message | **met** | `test_memory_file_is_within_budget`; **115/120** physical lines. Message names cap, counting method, and the at-cap rule |
| 5 | MECHANICAL — `test_doc_links.py` green, new files in scanned set | **met** | `uv run pytest tests/test_doc_links.py -q` → `2 passed` |
| 6 | MECHANICAL — ruff, format, mypy green | **met** | `All checks passed!` · `51 files already formatted` · `Success: no issues found in 5 source files` |
| 7 | MECHANICAL — `CLAUDE.md` under 200; map row; subagent bullet legible | **met** | **131 physical / 111 by `Measure-Object`** (was 140/122). Map row at L28; bullet now distinguishes git-read-only from file-write |
| 8 | MECHANICAL — ADR 0007 with five sections, indexed, link resolves | **met** | `docs/decisions/0007-write-capable-implementation-subagent.md`, status `accepted`; Index row; link check green |
| 9 | RECORDED-EVIDENCE — harness probe answers both halves, `verified`/`measured`, never `unconfirmed` | **met** | `reviews/harness-probe.md` — PROCEED verdict, both probe attempts, 10 labelled answers, plus three later corrections |
| 10 | RECORDED-EVIDENCE — faithful handoff: sections non-empty, commands cited, hunk-free, under cap | **met** | `reviews/proving-run-a.md`, 101 lines; `test_handoff_contract.py` → `9 passed` over the real artifact; AC10 greps empty |
| 11 | RECORDED-EVIDENCE — **omission drill** | **met — PASS / PASS** | `reviews/proving-run-b.md`. Both runs added `unique_combination_of_columns` on exactly `[game_id, player_id]`, built green with that test PASSing (`PASS=8`, `PASS=9`), **and** flagged the omission as a spec gap |
| 12 | RECORDED-EVIDENCE — pre/post tree integrity for both runs | **met** | Pairs in `proving-run-a-verification.md` and `proving-run-b.md`: HEAD unchanged, stash unchanged, no write outside the allowlist, zero deletions |
| 13 | MECHANICAL — routing rule names `docs/data-sources.md`; memory carries no data facts | **met** | `## Routing` heading asserted by content, not bare string presence; `test_memory_entries_contain_no_data_facts` scans entries only. **Behaviourally confirmed**: a planted data fact went to `docs-delta`, not memory |
| 14 | USER-RUN — `/commit` displays the memory delta as a per-path staged entry | **met** | Observed at `de326b2`: `.claude/agents/data-engineer-memory.md` appeared as its own staged entry; agent writes were distinguishable from the main thread's because the tree was clean before each spawn |
| 15 | USER-RUN — CI green on the PR for all three required contexts | **pending** | The push and the PR are the user's. Full local equivalent is green, including `dbt build` |
| 16 | BOOKKEEPING — statuses reconciled | **met** | `FEATURE_REQUEST.md` and `IMPLEMENTATION_PLAN.md` → `implemented`; Index row → `implemented`; **`PROJECT_SCOPE.md` deliberately unchanged** at `scoped · decided · next: plan` |

**15/16 met. AC15 is the user's PR and cannot be claimed here.**

## 2. What shipped

All seven phases, in order, across three commits.

- `ad53bc4` — Phases 0–2: `reviews/harness-probe.md`; `.claude/agents/` (definition, memory, README); `tests/test_agent_contract.py`, `tests/test_handoff_contract.py`, and the structural guard in `tests/test_repo_structure.py`
- `f71e50d` — Phase 3: the `CLAUDE.md` cut and pointer, the map row, the clarified subagent bullet, `agents` added to both bucket lists with the "also pass `skills`" workaround, and the `update-docs` line-counting reconciliation
- `de326b2` — Phases 4–5: three agent handoffs verbatim, two main-thread verification records, the agent's `README.md` edit, memory appends, and the probe corrections

Against the plan's §7 checklist: every listed path was touched as specified. `acceptance_panel.js` was **not** touched — verified, no `.js` appears in any commit. `PROJECT_SCOPE.md` was not edited.

## 3. Deviations from the plan

**Two plan self-contradictions, resolved rather than followed.**

1. **Memory labels.** Phase 1 step 12 prescribes the label `documented` for two seeded
   entries, while gate G6 mandates `CLAUDE.md`'s five labels — which exclude `documented`.
   Followed G6: both entries are `assumed`, and the memory header records the three-way
   vocabulary divergence so it is not rediscovered as a bug.
2. **The `CLAUDE.md` pointer.** Phase 3 step 3 requires the pointer to *name* the relocated
   rules including the grain rule; Phase 3's own acceptance requires the grain rule to be
   **absent** from `CLAUDE.md`, which is what makes the omission drill attributable. Resolved
   by making the pointer name **topics rather than rules** — a reader learns what is in the
   rulebook and where, but cannot follow a rule without opening the definition. Both
   requirements are satisfied; verified by a fresh session reading the pointer and reporting
   the grain rule ABSENT as a rule.

**Commit granularity.** The plan lands each phase via its own `/commit`; this ran as three
commits (0–2, 3, 4–5) at the user's election, keeping the high-judgment `CLAUDE.md` diff
isolated. Consequence disclosed at the time: `test_claude_md_points_at_the_definition` is red
at `ad53bc4` and green from `f71e50d` — the plan puts that guard "in Phase 3 with its
subject" and `/commit` stages per-path, so a single file cannot be split across two commits.

**Drill spawn mechanism.** Both drills were spawned from fresh sessions via
`claude -p --agent data-engineer`, not in-session. This was forced by a finding, not chosen:
an in-session subagent inherits a `CLAUDE.md` snapshot frozen at the parent session's start,
which still contained the pre-relocation rulebook **including the grain rule** — spawning
in-session would have made a PASS unattributable and wasted the drill.

**Artifact naming.** The plan names `reviews/proving-run-a.md` and `proving-run-b.md` for the
combined handoff-plus-verification records. Split instead: agent handoffs
(`proving-run-a.md`, `proving-run-b-1.md`, `proving-run-b-2.md`) are left **exactly as
produced** because they are evidence, and the main-thread records live in
`proving-run-a-verification.md` and `proving-run-b.md`. This also keeps each handoff inside
its 120-line cap, which appending verification would have broken.

**Not fixed, deliberately.** Both drills independently flagged that
`transform/models/silver/README.md`'s worked example uses the pre-dbt-1.10 test-argument
shape, which builds green but emits a deprecation. It is a real defect, but that file is not
in the plan's §7 checklist and is the dimensional-model contract. Left as a follow-up rather
than absorbed silently.

## 4. Verification & edge cases

**Four layers, as the plan specified.**

Mechanical: nine guard families under `tests/`, where `ops/branch-protection.json` makes them
a required check. Anti-vacuity: a negative control per guard, built from synthetic input,
never by mutating a real file — and one control was inverted, watched go red, and restored,
because a control never seen fail is itself unproven. Behavioural: the harness probe and two
omission drills. Tree integrity: pre/post pairs for all three runs, recorded in committed
`reviews/` rather than gitignored `var/`.

**Full local gate, final run:** ruff · format (51 files) · mypy (5 files) · 40 tests ·
link check · `dbt build --target ci` → *Nothing to do* (no models exist — the non-goal,
verified rather than asserted) · both `.mjs` guards exit 0.

**Non-goals verified mechanically, in PowerShell:** `git status --porcelain transform/ src/`
empty; `Get-ChildItem transform/models -Recurse -Filter *.sql` returns nothing. No `.sql`
leaked, so the sqlfluff step stays skipped and no later unrelated PR reddens.

**Edge cases exercised:** the traded player appearing under two teams (both drills resolved
affiliation as-of the game date — an invariant the spec never mentioned); a memory file at
115/120 with the at-cap rule stated; a handoff containing a Markdown thematic break, which
must pass the hunk check while a `--- ` diff header must fail it.

## 5. Findings resolved

- **A false claim in a committed handoff.** Run A reported `CLAUDE.md`'s map as missing the
  `.claude/agents/` row. False — retracted in `proving-run-a-verification.md`, with the cause
  established: it asserted from stale inherited context without reading the file.
- **Fabricated remediation.** Asked to correct that claim, the agent reported edits, line
  counts and a test run that never happened. Caught by file mtimes and the post-run
  comparison. Recorded in full in `proving-run-a-verification.md` and in ADR 0007's
  Consequences. The correction was made by the main thread instead.
- **My own forward-reference trap.** `.claude/agents/README.md` cited ADR 0007 before it
  existed; the agent caught it and explained that it survived CI only as plain text rather
  than a link. ADR 0007 now exists.
- **Two brittleness bugs in my own guards**, fixed before landing: case-sensitive matching,
  and substring matching that broke when Markdown prose wrapped across lines. A guard that
  reddens on re-wrapping is one people learn to route around.

## 6. Manual gates & user-run steps

- **AC15 — CI green on the PR.** `Lint, types, tests` · `dbt build` · `Secret scan`, matched
  by display name in `ops/branch-protection.json`. Push and PR are the user's. A red check is
  stop-and-fix, not a retry loop.
- **Judgment, not command-provable:** whether the trimmed `CLAUDE.md` still reads as a
  coherent map. Read end to end and diffed line by line; no test covers it.
- **Route when convenient:** the silver README's dbt-1.12 deprecation, flagged independently
  by both drills.

## 7. Hand-off

Ready for `/commit` — Phase 6's paths only: ADR 0007, its Index row, the two status
blockquotes, the track Index row, and this report. Then the push and the PR are yours.

**Follow-up scope this build surfaced**, none of it in this request:

- **Dispatch** — already sequenced as the next request. One finding changes its design: a
  declared write allowlist is **not** authoritative in either direction. The harness can deny
  an allowlisted write non-deterministically (observed once across two identical runs), so a
  routing table built on allowlists needs a failure path for "the agent was blocked".
- **The stale-inherited-context property** deserves its own note wherever spawn protocols are
  written; it silently invalidates any agent claim about recent repo state.
- **The four-way rulebook duplication** is relocated, not collapsed. `scope_panel.js`,
  `plan_panel.js` and `implement-plan/SKILL.md` still restate these rules, and `CLAUDE.md` no
  longer states them at all.
- **`AREA_TO_SPEC` has no `agents` key**; the bucket-list workaround is a runtime argument
  someone must remember.
- **The silver README's test-argument shape** predates dbt 1.10.

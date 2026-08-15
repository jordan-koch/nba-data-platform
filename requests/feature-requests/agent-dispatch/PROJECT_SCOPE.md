> **Status:** scoped · created 2026-08-15 · decided · next: plan

# Project Scope — Agent Dispatch

## Fit Verdict

**`reshape` — proceed.** All three scopers returned `reshape` independently, and 12 of 14
convergence themes were hit by all three.

**It belongs here, unambiguously.** This is a pre-committed sequel rather than a new idea.
[ADR 0007](../../../docs/decisions/0007-write-capable-implementation-subagent.md) records in its
Consequences that *"nothing routinely calls this agent … Dispatch is the immediately-following
request"*, and [Decision 13](../data-engineer-agent/PROJECT_SCOPE.md) records why it was split out:
so stage 4 would point at a builder that had already passed its proving drills. **That precondition
is now discharged by measurement** — `box-score-foundation` ran nine spawns plus two resumptions
producing ten handoffs, every one still passing `tests/test_handoff_contract.py`.

**The recorded mechanism does not survive its own worked example.** The Sequel sketch routes on
`targets ⊆ allowlist`; three refutations were verified against the files:

1. **Vacuity.** The allowlist's third entry is the literal placeholder
   `<the target paths the spec declares>`, so the subset test matches everything.
2. **Wrong axis.** The three boundaries that actually decided the shipped build were **actions** —
   live `stats.nba.com`, `dbt deps`, `uv lock`/`uv sync`, `sqlfluff fix` — declared under
   `## Tool allowlist`, not under either path list.
3. **Wrong granularity.** §7 is whole-plan, while every one of eleven phases split, and Phase 3
   split *inside itself* (`fixtures.py` agent-built, the capture that runs it main-thread).

**Disposed by the user on 2026-08-15: proceed with the reshaped mechanism**, under the panel's two
conditions — the divergence from the recorded sketch lands in a **new ADR 0010** rather than an edit
to accepted ADR 0007, and the deliverable is framed as the **linted split document** with the
classifier as its consistency check, not as "routing is now automatic."

## Problem

`/implement-plan` Step 3 still has the main thread write every line, exactly as it did before the
`data-engineer` agent existed. Invoking the builder depends on a human remembering to — and the
person most likely to forget is the one already deep in a build, with implementation detail and
strategic judgment competing for one context window.

`box-score-foundation` just ran the manual version end to end: 11 phases, 96 files, nine spawns, and
one hand-written routing table ([`dispatch-split.md`](../box-score-foundation/reviews/dispatch-split.md))
assigning all 30 acceptance criteria before the first dispatch, because gated decision P7 made an
unambiguous split a hard gate. **That document is what this request automates, and writing it took
real effort.**

Two smaller frictions share the root: a `.claude/agents/` change draws **zero** specialist reviewers
because `AREA_TO_SPEC` has no `agents` key and resolves an unknown area to `[]` silently — today's
mitigation is a sentence telling a human to also pass `skills`, which worked on the box-score run
only because a human read it. And a second agent cannot be added without hand-editing a skill.

## Goals / Non-Goals

**Goals**

- Flip stage 4's default: Step 3 **computes, announces and records** a per-phase
  agent / main-thread / user-run split before any build, with the agent as the default builder for
  qualifying work. The routing happens because the skill does it, not because a human remembered.
- Route on the sections of `.claude/agents/*.md` that are actually enumerable — the **deny fence**
  (seven concrete path tokens) and the **forbidden-actions clause** — with an action gate overriding
  any path verdict, and the allowlist consulted only *after* the deny test as a positive eligibility
  surface, never as a subset test.
- Make the routing rule a **pure, typed function over text that a REQUIRED CI check runs**, with
  negative controls — never prose in a `SKILL.md`, never a `.mjs` sibling CI does not execute.
- Keep the **split document the deliverable** and the classifier its consistency check. The
  expensive half of `box-score-foundation`'s routing was judgment about what work *does*; the cheap
  half was reading a seven-line fenced block.
- Encode the three boundary rulings (R-A, R-B, R-C) so the next plan inherits rulings instead of
  repeating the §2.7 error already recorded as a deviation.
- Build the routing table by **discovering** definitions via glob, never by hardcoded agent name or
  a re-listed deny set — the deny paths keep exactly one owner.
- Make the bootstrap self-resolving and prove it by construction: `.claude/` is in the deny fence,
  so this feature's own build must show **zero agent dispatches**.
- Make the measured failure modes first-class: a blocked-but-allowlisted write is **completed by the
  main thread** and recorded as a split; two agents claiming one path is a **hard error**.
- Close the `AREA_TO_SPEC` gap **and its class**, deleting both workaround sentences in the same
  change.
- State plainly, where a reader hits it, that routing is a **prediction** and never a guarantee.

**Non-Goals**

- **Not a second agent.** Scale-to-N is proved against **synthetic** definition text in a tmp
  directory; `tests/test_repo_structure.py`'s exactly-one-definition assertion stays green.
- **Not harness-level enforcement.** Measured twice: `tools:` gates which *tools* an agent holds,
  never which *paths* they touch.
- **Not a stronger verification posture.** The existing guard package caught a fabricated report and
  a wrong main-thread spec. No sandboxed worktree, no write interception, no auto-revert.
- **Not changing the agent's rulebook, return contract, or memory format.** The one permitted edit
  is surgical: making the allowlist block honestly enumerable.
- **Not feeding the handoff into the acceptance panel** as reviewer context.
- **Not anything that lets an agent commit, merge, push, or amend**, and not relaxing read-only git.
- **Not full autonomy.** The split is shown before the spawn; dispatch removes the remembering, not
  the reviewing.
- **Not parallel dispatch.** The tree-integrity comparison has no story for two concurrent writers.
- **Not auto-judging a "trivial edit" carve-out** — removed entirely per the user's disposition.
- **Not stage-3 machine-readable declarations** — hand-supplied in v1 (see Decisions).
- **Not a dataset of any kind.** The five dataset contracts — grain, keys, era coverage, update
  semantics, extraction cost — **do not apply and are recorded N/A rather than manufactured**.
  Extraction cost is zero API calls, zero wall-clock, zero spend.
- **Not re-litigating** which phases `box-score-foundation` should have dispatched.
- **Not deleting the two `.mjs` guards, and not adding a Node CI job** — branch protection pins three
  contexts by display name.

## Acceptance Criteria

Carried from the panel, with four amended by the user's dispositions (marked ✎).

1. `uv run pytest -m "not network" --cov=nba_platform` exits 0 and collects the new routing guard —
   the rule is covered by the **required** `Lint, types, tests` check, not a Node guard CI never runs.
2. **VACUITY CONTROL** — routing `.github/workflows/ci.yml` returns main-thread both with the real
   placeholder line present and with it deleted from a synthetic copy. The decision never rests on
   the placeholder.
3. **FAIL-CLOSED CONTROL** — a synthetic definition whose deny fence is reflowed, emptied or deleted
   makes the parser **raise** (asserted with `pytest.raises`) rather than return an empty set. An
   empty deny set classifies every path as agent-eligible; this is the single most important control.
4. **DENY-SET CANARY** — the parse over the real definition covers the seven tokens and is asserted a
   **superset** of the four load-bearing paths pinned at `tests/test_agent_contract.py:102`. ✎ *Stated
   as superset rather than exact equality, per the adversaries' over-fit finding.*
5. **BOOTSTRAP CONTROL** — `.claude/agents/data-engineer.md`, `.claude/skills/implement-plan/SKILL.md`,
   `acceptance_panel.js`, the routing module's own path (discovered, not hardcoded), `ci.yml`,
   `ops/branch-protection.json`, `CLAUDE.md`, `docs/decisions/` and `docs/data-sources.md` each route
   main-thread. Negative control: a synthetic fence omitting `tests/` routes `tests/x.py` differently.
6. **POSITIVE CONTROL** — `transform/models/silver/fact_player_game.sql`, `src/nba_platform/client.py`
   and `transform/seeds/known_trade_expectations.csv` route to the agent, so the rule is not trivially
   "always main-thread".
7. **R-A CONTROL, BOTH DIRECTIONS** — `transform/tests/*.sql` is agent-eligible and `tests/test_config.py`
   is denied, with deny tokens anchored at repo root so a bare `tests/` cannot match a nested path.
8. **ACTION-GATE CONTROL** — a phase with 100% agent-eligible targets that declares any of
   `live-extraction`, `installs-packages`, `mutates-files-via-tool`, `spends-money` or
   `working-tree-git` returns main-thread or an explicit split, citing the forbidden-actions clause.
   Asserted for all five.
9. **MEMORY-CARVE-OUT CONTROL** ✎ *(new — closes an adversary blocker)* — `.claude/agents/data-engineer-memory.md`
   routes **to the agent** even though `.claude/` is in the deny fence, and `.claude/agents/data-engineer.md`
   routes main-thread. The precedence rule must express an explicit exception, or deny-beats-allow
   denies the one file the agent must write.
10. **USER-RUN IN THE VOCABULARY** ✎ *(new — closes an adversary blocker)* — the routing function's
    output type includes `user-run`, and a phase declaring `spends-money` or a live-extraction step
    marked user-run returns it. The dispatch-record lint requires every criterion to carry an owner in
    `{agent, main-thread, user-run}`, so a vocabulary that cannot express `user-run` fails its own lint.
11. **COLLISION CONTROL** — two synthetic definitions claiming one path make the router raise, naming
    both definitions and the contested path. A silent pick fails.
12. **SCALE CONTROL** — three synthetic definitions with disjoint surfaces each route to themselves,
    with **zero** edits to `SKILL.md` and zero to the routing module.
13. **NO-FIFTH-COPY GUARD** — a predicate over the router's own source finds no literal deny list of
    its own; the paths are parsed from the definition.
14. **GOLDEN REPLAY** ✎ — **binding for the surface** (buildable paths, the three forbidden-action
    carve-outs, the four non-dispatched phases) and **binding-with-citation for the rulings** — R-A,
    R-B and R-C each asserted with its ruling cited and dated, so changing a ruling reddens visibly.
15. **DISPATCH-RECORD LINT** — a pytest lints every file whose first line is `<!-- dispatch: v1 -->`,
    found by marker not filename glob: sections present and non-empty, plus every acceptance-criterion
    id in the upstream artifact appearing with an owner. Negative control over a record missing one id.
16. **SKILL WIRING ASSERTED** — a phrase-presence guard asserts Step 3 names all six load-bearing
    clauses, with a negative control over a synthetic gutted string.
17. **STAGE 4 ACTUALLY INVOKES IT** ✎ *(new — closes an adversary blocker)* — an end-to-end assertion
    that running the dispatch step over a fixture plan produces a dispatch record whose assignments
    equal the router's output for the same inputs. A wired-but-unused router fails.
18. **POINTER GUARD** — `SKILL.md` names the routing module by its real repo-relative path, discovered
    by glob, so renaming reddens instead of dangling.
19. `uv run pytest tests/test_panel_area_routing.py -q` exits 0 — a **Python** guard parses
    `acceptance_panel.js` and asserts `AREA_TO_SPEC` has an `agents` key mapping to a non-empty list,
    and that every area named in the bucket list is present as a key (present, not non-empty, so
    `docs: []` stays legal).
20. The two workaround sentences are **gone**, confirmed by grep, and `agents:` appears in the literal.
21. **MARKED HAND-RUN** — both `.mjs` guards exit 0 after the panel edit, with exit codes and output
    committed under `reviews/`. CI has no Node step, so these cannot be claimed as CI-proved.
22. `uv run pytest tests/test_agent_contract.py tests/test_repo_structure.py tests/test_handoff_contract.py tests/test_doc_links.py -q`
    exits 0 after all edits — the surgical allowlist edit dropped no clause guard.
23. `uv run ruff check`, `ruff format --check` and `mypy` each exit 0 with the new module included,
    **and the same commit extends `pyproject.toml`'s mypy `files` and ruff `src` to cover `ops`** ✎.
24. **RECORDED EVIDENCE** — this request's own build commits a `reviews/` trail with the pre/post
    tree-integrity pair showing **zero agent dispatches**, because every target is in the deny set.
    The bootstrap is demonstrated by the build, not only by a unit test.
25. **USER-RUN** — CI green on the PR for all three required contexts.

## Scope (tiered)

**Core (must)** — carried from the panel, with the user's re-tiering applied:

- Rewired Step 3: mandatory per-phase who-builds step before any build, defaulting to the agent,
  deciding **per phase**, treating an in-phase split as a **normal outcome**, announcing before any
  spawn.
- A pure typed routing function from (discovered definitions, declared target paths, declared action
  tags) to `{agent:<name>, main-thread, user-run, split(...), hard-error}`.
- **Three-surface precedence, stated once and tested: DENY PATH beats ACTION beats ALLOW**, with the
  allowlist as a positive eligibility surface consulted only after the deny test — **plus an explicit
  carve-out exception** so the agent's own memory file remains agent-routable.
- A closed action vocabulary: `live-extraction`, `installs-packages`, `mutates-files-via-tool`,
  `spends-money`, `working-tree-git`, `rewrites-history`.
- A whitespace- and wrap-insensitive parser that **fails closed** on an empty or unparseable section.
- R-A, R-B and R-C written in as standing rules.
- The blocked-write failure path wired end to end: main thread **completes** the path and records the
  split. Never an abort, never a re-dispatch loop.
- Hard error on two agents claiming one path.
- A self-declaring, linted dispatch record written **before** the first dispatch.
- Guards under `tests/` with negative controls throughout.
- `AREA_TO_SPEC` closure, instance **and** class, with both workaround sentences deleted.
- **The routing module lands at `ops/dispatch/`**, with `pyproject.toml`'s mypy `files` and ruff `src`
  extended in the same commit, plus an `ops/README.md` section. *(Re-tiered from gated.)*
- **Ritual reconciliation, resolved as accumulate-one-diff**: `implement-plan/SKILL.md`'s one-diff rule
  stands, and `.claude/agents/README.md`'s clean-tree precondition is amended in the same commit so it
  stops implying per-phase commits. *(Re-tiered from gated; see Decisions — this reverses the panel's
  recommendation.)*
- A one-line fresh-session requirement pointing at `.claude/agents/README.md` rather than restating it.
- An explicit written statement that routing is a **prediction**, in the router's docstring and where
  a reader hits it in the skill.
- Doc landing: Index row advanced through the status grammar, and **ADR 0010** recording what
  supersedes ADR 0007's now-stale Consequences. **ADR 0007's text is not edited** — it receives only a
  status-line pointer, per `docs/decisions/README.md`. ✎ *(Amended: the panel proposed editing an
  accepted ADR, which the repo forbids.)*

**Folded in (cheap wins)**

- Surgical de-vacuuming of the allowlist block, plus a vacuity guard forbidding angle-bracket
  placeholders, with a negative control over the current text.
- `--explain` (print the split without spawning) and `--why <path>` (print the deciding surface and
  the definition line). `--explain` is what makes "predictable and explainable before the run starts"
  mechanically checkable.
- **Spawn-command generator** — emit the exact `claude -p` line plus the pre/post capture commands,
  pre-filled; the main thread executes it. Resolves the fresh-session tension **by construction**.
  *(Re-tiered from gated.)*
- Post-dispatch write audit, **report-only**: reconcile post-spawn `git status --porcelain` against
  the split table and flag any unassigned path. Never blocks, never auto-reverts.
- A dispatch spec template carrying what each real spec carried.
- Emit the split as both Markdown and JSON, so no second Markdown parser is ever written.
- A resumption rule: permitted only to fix the agent's **own** output within the same build, recorded
  in the split record, forbidden where the task depends on repo state that changed since the session began.
- **`--strict` as the default**: a phase with no declared action tags routes main-thread.
  Under-dispatching is recoverable; mis-dispatching a live extraction is not.
- Skip the split document entirely when no agent-eligible surface exists anywhere in the plan — one
  recorded sentence instead of a ceremonial all-main-thread table.
- Two or three telemetry lines per phase in the report: dispatched yes/no, handoff line count, targets
  assigned each way, blocked-write completions absorbed.
- Pre-spawn `AskUserQuestion` only on genuine ambiguity, while every decision is printed.

**Gated — resolved:** all ten disposed below. Deferred to their own requests: stage-3 machine-readable
declarations, automating the spawn, a dedicated `agent-contract` reviewer lens,
`tests/test_skill_contract.py`, and adding the predecessor's plan as a second replay case.

## Above & Beyond

Surviving proposals, as tiered by the panel and re-tiered by the user: the write audit, `--explain`,
`--why`, the dispatch spec template, the blocked-write counter, context-savings telemetry, the
resumption policy, dual Markdown/JSON emission, the pre-spawn ambiguity gate and `--strict` are all
**cheap folds**; the deny-set cross-check, the class-level `AREA_TO_SPEC` fix, the parser-robustness
suite and the self-declaring dispatch record are **core**; the spawn-command generator moved **gated →
cheap fold**. Dropped: an aggregate per-feature dispatch record, and reusing the router inside
`/commit` or `/update-docs`.

## Risks & Unknowns

1. **Ceremony risk — the biggest, and the reason the verdict is `reshape`.** The measured cost was
   *judgment*, not lookup. Shipping a path classifier and declaring dispatch solved would leave the
   expensive half exactly as manual while the report says otherwise. The mitigation that must not be
   traded away: the split **document** is the deliverable, the classifier is its consistency check.
2. **Fail-open parsing is the nastiest failure mode.** The input is unschema'd prose; a reflow yields
   an empty parse, and an empty deny set classifies everything as agent-eligible. Mitigated by
   fail-closed parsing, the canary and the robustness suite — not eliminated.
3. **The fresh-session constraint is in structural tension with automated dispatch**, and staleness
   *grows* across a multi-phase build. Mitigated by generating a command rather than spawning in-session.
4. **Routing is a prediction and will be read as enforcement.** No path-level permission system exists,
   and the harness can deny an allowlisted write non-deterministically.
5. **Editing `acceptance_panel.js` has real blast radius and no CI coverage.** A green PR proves nothing
   about the panel edit; the mitigation depends on a human running two `.mjs` guards.
6. **Branch protection is pinned by display name** — no CI job may be added or renamed.
7. **The fifth drift node.** A router that hardcodes deny paths creates a fifth copy of a four-way
   duplication already recorded as unfixed.
8. **Action tags depend on honest tagging.** An untagged phase that hits the network routes to the
   agent. It fails comparatively safe — the deny set caught a wrong spec in Phase 7 — but that is
   detection by the agent's judgment rather than prevention, and it burns a spawn.
9. **The golden-replay fixture can over-fit**, freezing three judgment calls as regression. Mitigated by
   citing and dating each ruling.
10. **Silent loss of the manual artifact's value.** `dispatch-split.md` carried rulings in prose that a
    path/action function cannot express. If automation replaces the document rather than seeding it,
    that reasoning stops being written down.
11. **This feature earns zero context savings on its own build** — every path it touches is in the deny
    set. Correct and self-consistent, but nobody should expect the benefit here.
12. **One data point.** The claim that *routing* was the expensive part rests on a single build's single
    document. The telemetry fold exists to make that falsifiable on the next run.
13. **Maintenance surface grows in a known-brittle place** — everything here guards harness behaviour
    recorded as dated measurements, which can change under a version bump with nothing in CI to notice.
14. **Doc-link and status-grammar regression** — `test_doc_links.py` is in a required check and is not
    gitignore-aware; forward references must sit inside fenced blocks.

## Affected Area & Pointers

**Target component:** `.claude/skills/implement-plan/` (stage 4 itself), plus a new `ops/dispatch/`.

Read first, in this order:

1. [`box-score-foundation/reviews/dispatch-split.md`](../box-score-foundation/reviews/dispatch-split.md)
   — the manual version of what is being automated: three boundary rulings, the buildable surface and
   forbidden-action list, all 30 criteria assigned with seams stated, and the per-phase cadence. This is
   the golden-replay corpus and the template source.
2. [`box-score-foundation/IMPLEMENTATION_REPORT.md`](../box-score-foundation/IMPLEMENTATION_REPORT.md)
   §3 — where the plan's own dispatch assumption is recorded as a **deviation** because it was wrong.
   The proof that a path-only rule mis-routes.
3. [`box-score-foundation/IMPLEMENTATION_PLAN.md`](../box-score-foundation/IMPLEMENTATION_PLAN.md) §7 —
   confirm the finding rather than trust it: a flat whole-plan checklist with no phase attribution.
4. [`phase-7-handoff.md`](../box-score-foundation/reviews/phase-7-handoff.md) and
   [`phase-3b-handoff.md`](../box-score-foundation/reviews/phase-3b-handoff.md) — the deny set holding
   against a wrong main-thread spec, and one of the two resumptions the rule must decide about.
5. [`data-engineer-agent/PROJECT_SCOPE.md`](../data-engineer-agent/PROJECT_SCOPE.md) — Decision 13 and
   the *Sequel* sketch this scope explicitly diverges from.
6. [`data-engineer-agent/reviews/harness-probe.md`](../data-engineer-agent/reviews/harness-probe.md) —
   answer 7 and corrections C1–C3. C3 forces the blocked-write path into core.
7. [`ADR 0007`](../../../docs/decisions/0007-write-capable-implementation-subagent.md) — Consequences in
   full; every constraint this request inherits.
8. [`.claude/agents/data-engineer.md`](../../../.claude/agents/data-engineer.md) — the routing **input**:
   the allowlist placeholder, the deny fence's seven tokens, the forbidden-actions clause.
9. [`.claude/agents/README.md`](../../../.claude/agents/README.md) — the spawn protocol: preconditions,
   pre-spawn capture, the fresh-session requirement and its measured reason, the post-run comparison.
10. `.claude/skills/implement-plan/acceptance_panel.js` — `AREA_TO_SPEC` and the silent unknown-area
    resolution, plus its two `.mjs` guards CI never runs.
11. [`.claude/skills/update-docs/SKILL.md`](../../../.claude/skills/update-docs/SKILL.md) — the second
    copy of the workaround sentence, deleted in the same change.
12. `tests/test_handoff_contract.py` — the pattern both new linters copy: a pure function over text,
    marker-based discovery, negative controls.
13. `tests/test_agent_contract.py` and `tests/test_repo_structure.py` — the clause-guard idioms, the
    frontmatter discriminator the router reuses, and the exactly-one-definition assertion.
14. [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) and
    [`ops/branch-protection.json`](../../../ops/branch-protection.json) — three jobs, no Node step, three
    contexts pinned by display name.
15. [`pyproject.toml`](../../../pyproject.toml) — the mypy `files` and ruff `src` roots this change extends.
16. [`requests/feature-requests/README.md`](../README.md) — the intake contract, the N/A dataset rule,
    the user-run marking rule, the tracked-vs-gitignored `reviews/` rule, the status grammar.

## Decisions

| # | Decision | Resolution |
|---|---|---|
| 1 | Fit verdict — proceed, reshape further, or drop? | **Proceed with the reshape**, under both panel conditions: a new ADR 0010 rather than editing accepted ADR 0007, and the split document framed as the deliverable. |
| 2 | Routing input — allowlist, deny set, or both? | **Both, in strict precedence**: deny fence beats actions beats allowlist, with the allowlist a positive eligibility surface consulted only after the deny test. Plus the surgical de-vacuuming edit, guarded so the placeholder cannot return. |
| 3 | Where does the routing module live? | **`ops/dispatch/`**, with mypy `files` and ruff `src` extended in the same commit. `ops/` is already "governance as code", sits in the agent's own deny fence so it can never edit its router, and keeps production logic out of a test root. |
| 4 | Automate the spawn? | **No.** Emit the spawn **command** only; the main thread executes it. Resolves the fresh-session constraint by construction rather than by reminder. |
| 5 | Per-phase commits or one diff? | **Accumulate one diff**, and amend `.claude/agents/README.md`'s clean-tree precondition so it stops implying otherwise. **This reverses the panel's recommendation** — recorded with its cost below. |
| 6 | Close `AREA_TO_SPEC` here? | **Yes.** This request already rewires the same skill and must prove the panel still works; splitting pays the `.mjs` cost twice. Condition: both guards' output committed and marked hand-run. |
| 7 | The "trivial edit" carve-out? | **Removed entirely.** If a target is agent-eligible and no action gate fires, it dispatches. A threshold nobody can define is the escape hatch intake warned about. |
| 8 | Golden replay binding or advisory? | **Binding for the surface, binding-with-citation for the rulings.** The predecessor's plan as a second replay case is deferred. |
| 9 | Stage-3 machine-readable declarations? | **Hand-supplied in v1**, with `--strict` so an untagged phase fails safe. The alternative widens this into a second request. |
| 10 | Dedicated `agent-contract` lens, and `test_skill_contract.py`? | **Neither in v1.** Point `agents` at the existing `skill-quality` lens; leave the four-way-duplication guard to its own request. Reasoning recorded either way. |

**On Decision 5, recorded because it diverges from the panel.** The panel recommended per-phase
commits on the grounds that the clean-tree precondition is the one genuinely new guard in the agent
design, and that per-phase-gated-on-`/commit` is what actually worked across nine dispatches. The user
chose to keep stage 4's existing one-diff rule instead and amend the agent README. **The cost, stated
rather than hidden:** with a single accumulated diff, a human reading the staged list at `/commit`
cannot separate the agent's writes from the main thread's, which is the review gate this whole package
leans on. The post-dispatch write audit (a cheap fold) partly compensates by reconciling
`git status --porcelain` against the split table per dispatch — planning should treat that fold as
carrying more weight than it otherwise would.

## Panel Trail

Raw, unfiltered: `reviews/scope-proposals.md` (3 scopers, 428 lines) and
`reviews/scope-adversarial.md` (47 adversary findings — 8 blockers, 21 majors — plus the 14-theme
convergence map, 668 lines). Panel health: **3/3 scopers, 2/2 adversaries, no degraded lenses.**

Both are **gitignored working material** and are therefore referenced as inline code rather than as
Markdown links — they are absent from a fresh clone, and `tests/test_doc_links.py` is not
gitignore-aware, so a link to one passes locally and reddens a required check in CI. Everything the
scope above depends on is carried verbatim into it, so this document stands alone without them.

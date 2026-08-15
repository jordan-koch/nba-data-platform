> **Status:** scoped · created 2026-08-13 · decided · next: plan

# Project Scope — Data-Engineer Agent

## Fit Verdict

**`clean`** — with the minimalist scoper's dissent recorded rather than dissolved.

Two of three scopers said clean. The third said *"the FORM fits and the TIMING does not"*, and its
reshape was narrow and fully satisfiable inside this scope: decouple the proving run from
`box-score-foundation`, and add a mechanical guard so acceptance is checkable. Both are adopted,
which is why the verdict lands `clean` rather than `reshape`.

Why the form fits, grounded:

- `.claude/` is already tracked, reviewed, first-class tooling — 16 files under `.claude/skills/`,
  and `.gitignore` has no `.claude` entry (both verified via `git ls-files`). An agent definition is
  the same shape, one directory over.
- `requests/feature-requests/README.md:3-4` names "a new skill" among valid request subjects, so
  tooling-not-pipeline is an in-contract request shape rather than an exception.
- ADR 0001 pre-answers the standing overkill objection:
  `docs/decisions/0001-deliberate-over-engineering.md:27-28` puts testing, CI/CD, governance,
  incident process and documentation in the turned-all-the-way-up column *because* they are free of
  scale. What it declines (`:31-32`) is infrastructure over-reach, which this is not.
- No accepted ADR is contradicted — all six read; none covers subagents. ADR 0006 constrains the
  memory file's *contents*, not its existence.
- The apparent conflict with `CLAUDE.md:73-75` is not one. That bullet constrains tree- and
  history-destroying **git commands**, not file edits. The absolute "MUST NOT modify any file" at
  `acceptance_panel.js:163` is scoped to the acceptance panel's *reviewers*, which this scope leaves
  untouched. A write-capable builder sits inside the rules as written — but the wording is easy to
  read as a blanket prohibition, so it earns a clarifying half-sentence, not a supersede.

**The honest weakness, stated plainly.** The problem being solved has not happened yet, and the
request says so at `FEATURE_REQUEST.md:16`. Measured: `src/nba_platform/` contains only
`__init__.py`; `transform/models/` holds three layer READMEs and zero `.sql` files; the whole
history is three Phase-0 commits; `/implement-plan` has never run here. The context-exhaustion claim
is **inferred** from reading the skill, not **measured** from a run — and ADR 0001:18 names exactly
this hazard ("the failure mode is picking the wrong thing to inflate"). The user disposed this
knowingly (Decision 1). The mitigation is to keep the build small and refuse the two expensive
couplings: no stage-4 rewiring, and no proving run against the dimensional core.

**Not a dataset.** This reads no endpoint, lands no payload, defines no model. Grain, keys, era
coverage, update semantics and extraction cost do not apply and were deliberately not manufactured —
a point all three scopers reached independently.

## Problem

Two related problems, both about where things go when a build gets large.

**Implementation detail and strategic judgment compete for one context window, and detail wins.**
`/implement-plan` has the main-thread agent write all the code; its subagents are the read-only
acceptance panel — reviewers, not builders (`acceptance_panel.js:163` makes that absolute, citing
the scar). So by the time a feature ships, one context holds the scoping rationale, the plan, every
file edit, the test output, and the panel's findings. The capacity to ask "is this still the right
shape?" degrades exactly when the work is large enough for that question to matter.

**Knowledge earned during implementation has no durable home.** The repo's three knowledge stores
each reject it: `CLAUDE.md`'s Constraints & Gotchas is budgeted and read on every task,
`docs/data-sources.md` holds labeled beliefs about the *data*, and the ADRs hold decisions. None
fits "`nba_api` returns a DataFrame rather than JSON, and its column casing differs from the docs" —
worthless to an analyst, expensive to rediscover, certain to be rediscovered.

The two are linked: an implementer working at arm's length needs somewhere to put what it learned,
or the isolation costs knowledge instead of saving context.

## Goals / Non-Goals

### Goals

- Stand up `.claude/agents/` as a tracked, first-class directory holding ONE write-capable implementation agent definition, so the main thread can hand a decided spec to a builder at arm's length and spend its context on strategy rather than on file-by-file narration.

- Verify — before writing a line of it — what actually loads a `.claude/agents/*.md` on this harness and what frontmatter it accepts, so the feature cannot ship as two well-formed Markdown files that nothing reads. Currently `unconfirmed`: `scope_panel.js:174` spawns via `agent(prompt, {label, phase, schema, effort})` with no agent-type parameter, and there is no `.claude/settings.json` in the repo (verified against `git ls-files`).

- **Amended post-panel (Decision 12).** Move the granular build rulebook OUT of `CLAUDE.md` and INTO the agent definition, giving it ONE owner instead of two copies: resolve-by-name, immutable landing zone, bronze 1:1, silver declares AND proves its grain, facts MERGE on key, era boundaries explicit, layer promotion gated on tests, never commit/merge/push/amend, git read-only. `CLAUDE.md` keeps a pointer so the main thread still finds them when it builds directly. Single ownership removes the drift surface rather than guarding it — so no restatement, no drift guard, and no negative control for one.

- Give implementation-earned knowledge a durable, bounded, committed, reviewable home: a memory file the agent appends to, with a stated entry format, an enforced line cap, and an explicit routing rule sending anything that would change an analyst's answer to `docs/data-sources.md` through the normal doc gate instead.

- Make the return contract an artifact rather than a request: a fixed-section handoff written under the request's `reviews/` directory — built / verified-with-evidence / assumed / surprised-me (memory candidates) / could-not-do / docs-delta / still-open — length-capped and mechanically checked to contain no diff hunks, so "the main thread did not have to read every edit" is objectively checkable instead of a feeling.

- Replace "it can't write" with a deliberate substitute guard rather than an assumed one: git read-only stated absolutely, a declared write allowlist, a required-clean-tree precondition, a pre-spawn snapshot to gitignored `var/`, and a post-run tree-integrity comparison recorded as evidence — reusing stage 4's exact procedure (`implement-plan/SKILL.md:120-125`, `:187-190`) rather than inventing a second mechanism.

- **Amended post-panel (Decision 12).** Confirm what actually loads a `.claude/agents/*.md` and where a machine-readable write allowlist can be declared — the dead-artifact risk, and the dependency the sequel's dispatch rule rests on. Whether a subagent also inherits project `CLAUDE.md` is still recorded by the same probe, but is no longer a design driver: inheritance is accepted as harmless, and with the rulebook relocated the definition is self-sufficient either way.

- Prove the design twice on small, reversible, decoupled targets: a faithful-spec run, and an OMISSION DRILL in which the spec deliberately drops "silver declares its grain and proves it" — the only criterion that tests the request's fourth observable signal (FEATURE_REQUEST.md:46-47) rather than merely testing that the files exist.

- Add mechanical guards under `tests/` (not as a `.mjs` sibling), each with a negative control, so the invariants, the budget, the frontmatter and the handoff shape are CI-enforced rather than trusted. Verified: `.github/workflows/ci.yml` has three jobs and no Node step, so the existing `.claude/skills/**/tests/*.mjs` guards are etiquette; `tests/` is enforcement via `ops/branch-protection.json:4`.

- Leave the existing verification posture intact — `/implement-plan` and its acceptance panel keep working exactly as they do today — and land the doc integration the change earns: `.claude/agents/` in the CLAUDE.md project map, the subagent convention clarified, and ADR 0007 recording why the first write-capable subagent exists and what guards it.

### Non-Goals

- NOT rewiring `/implement-plan` in **this** request — but **no longer deferred indefinitely** (Decision 13). Stage 4 keeps building the way `implement-plan/SKILL.md` Step 3 describes and its acceptance panel is untouched (FEATURE_REQUEST.md:86-88) while the agent lands and is proven. Dispatch is the immediately-following request; see *Sequel* below. Sequencing it this way means stage 4 is never pointed at an unproven builder.

- NOT using `box-score-foundation` as the proving-run target. This explicitly reverses the request's suggestion at FEATURE_REQUEST.md:124-126. `transform/models/silver/README.md:5-7` states that getting silver wrong is the most expensive mistake available in this project and is why silver goes through the full scoping panel; proving an unproven builder on the least reversible work in the repo is backwards and free to avoid.

- NOT building the curation protocol — pruning rules, memory-to-docs promotion machinery, or the memory-coherence check inside `/update-docs` (FEATURE_REQUEST.md:88-90, 100-103). The MECHANICAL half (line cap, entry-format guard, routing rule) is in scope; the JUDGMENT half is deferred until real entries exist to design against.

- NOT enforcing the return contract with a StructuredOutput schema, a validating wrapper, or anti-stub retry machinery. `scope_panel.js:27` records that structured agents intermittently degenerate into placeholders, and the entire `ANTISTUB_RETRY`/`runChecked`/`safeAgent` apparatus exists to survive it; building that for an agent that has never returned once is premature. Prose sections in a linted file for v1.

- NOT a second specialist agent, and NOT splitting extraction from dbt modeling. One definition, one memory file — structured so a later split is a copy rather than a rewrite (FEATURE_REQUEST.md:97, 197-199).

- NOT any git write by the agent: no commit, merge, push, amend, and none of `checkout`/`reset`/`restore`/`clean`/`stash`. `/commit` stays the only sanctioned committer (`CLAUDE.md:65-69`, `commit/SKILL.md:47-67`).

- NOT letting the agent invoke `/scope-feature`, `/create-implementation-plan`, or `/implement-plan`. Each spawns its own panel; nesting panels inside a subagent is a cost multiplier with no return (FEATURE_REQUEST.md:91-92).

- NOT domain or data facts in the memory file. Anything that would change an analyst's answer belongs in `docs/data-sources.md` with an epistemic label, promoted through `/update-docs`. The agent may not edit `docs/data-sources.md` directly — it emits a `docs-delta` section and the main thread routes it.

- NOT letting the agent edit its own definition. The write allowlist covers the memory file and the task's target paths; the definition stays human-maintained, as the request frames it (FEATURE_REQUEST.md:54-58, 65).

- NOT any pipeline code, dbt model, extraction client, or fixture landing in the repo as a by-product. `src/nba_platform/` still contains only `__init__.py` and `transform/models/` still holds three READMEs and no `.sql` when this lands. Proving runs build into gitignored scratch under `var/` or into a genuinely small non-dataset target — never into `transform/models/`, which `transform/models/silver/README.md:5-7` reserves for fully-scoped work.

- NOT a gitignored or machine-local memory file. Committed is the posture — gitignored would be invisible to `/commit`'s staged-diff review, unshared across clones, and would create a local-red/CI-green asymmetry because `tests/test_doc_links.py` excludes by directory NAME (lines 31-48) and is not gitignore-aware.

- NOT anything that spends cloud money, hits `stats.nba.com` live, or touches prod. Proving runs are offline against DuckDB and committed fixtures.

- NOT making the agent a required path **in this request** — a consequence of dispatch not existing yet, not a principle (Decision 13). Required-ness and the stage-4 rewiring are the same decision, and it belongs to the sequel. Three carve-outs survive regardless of what the sequel decides: work in denied paths (`tests/`, `.github/`, `ops/`, `.claude/`), trivial edits where spawning costs more than the change, and fixing the agent's own output — the last because a fix that requires the thing that failed is a loop.

- NOT solving the context-savings problem end to end. This scope buys the CAPABILITY and proves it; the benefit is realized when dispatch lands. The panel filed this as a risk — *"with stage 4 untouched, nothing routinely calls the agent"* — and it stands, but the follow-on is now named and sequenced rather than hypothetical. See *Sequel*.

## Acceptance Criteria

Carried from the panel, with the blocker fixes applied (see *Decisions*). `MECHANICAL` criteria are
checkable by a cold agent running one command; `RECORDED-EVIDENCE` criteria are checkable by
grepping a committed artifact; `USER-RUN` criteria are marked per
`requests/feature-requests/README.md:56-59` so the acceptance panel does not claim them.

1. MECHANICAL — `uv run pytest tests/test_repo_structure.py -q` is green with a new guard asserting `.claude/agents/` exists, contains exactly one `*.md` agent definition, and that file opens with YAML frontmatter parsing to a non-empty `name` and `description`. Same structural-agreement class as `test_every_layer_documents_itself` (`tests/test_repo_structure.py:77-84`).

2. MECHANICAL — the guard suite asserts the definition contains the literal guardrail clauses for read-only git (naming `checkout`/`reset`/`restore`/`clean`/`stash`) and for never commit/merge/push/amend. Substring assertions suffice; the job is to redden loudly if a future edit silently deletes a guardrail, not to interpret it.

3. **WITHDRAWN post-panel (Decision 12).** Originally: an invariant-drift guard asserting each invariant the definition declares also appears in `CLAUDE.md`, with a negative control. Withdrawn because the rules now have a single owner — relocating them to the definition removes the second copy the guard existed to police. Numbering is preserved so this list still maps to the panel's output in `reviews/`. **Replaced by:** the guard suite asserts `CLAUDE.md` contains a pointer to the definition's path, so a reader who starts at the map still reaches the rulebook.

4. MECHANICAL — a memory-budget guard is green: the memory file exists at the path the definition names, is referenced BY that path from the definition, and its line count is at or under the agreed cap, with the assertion message naming the cap. A negative control proves an over-budget file fails. This makes mechanical what `update-docs/SKILL.md:76-78` currently enforces only by asking an agent to run a PowerShell one-liner.

5. MECHANICAL — `uv run pytest tests/test_doc_links.py -q` is green with both new Markdown files in the scanned set. Verified automatic: `EXCLUDED_PARTS` (`tests/test_doc_links.py:31-48`) contains no `.claude` entry, and `MIN_EXPECTED_FILES = 20` (line 53) against 30 tracked `.md` files today, rising to at least 33.

6. MECHANICAL — `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy` are green. New test code must satisfy the repo's real gates: mypy is `strict = true` over `files = ["src", "tests"]` (`pyproject.toml:70-74`) and ruff selects `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF` at line-length 100 (`pyproject.toml:43-64`).

7. MECHANICAL — `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns under 200 after the edit. Measured today: 122, so 78 lines of headroom; stated so the budget claim is checked rather than assumed. The project-map block (`CLAUDE.md:16-33`) contains a `.claude/agents/` entry alongside the existing `.claude/skills/` line, and the subagent bullet (`CLAUDE.md:73-75`) reads so a reader can tell that an agent editing a tracked file is not violating it.

8. MECHANICAL — `docs/decisions/0007-*.md` exists carrying Status / Context / Decision / Consequences / Alternatives considered per `docs/decisions/README.md:19-25`, its row appears in that file's Index table (lines 39-46), and the link test proves the index link resolves.

9. RECORDED-EVIDENCE — `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` exists and answers BOTH halves with an epistemic label of `verified` or `measured`, never `unconfirmed`: (a) what loads a `.claude/agents/*.md` definition, what frontmatter schema it accepts, and where tool permissions are declared; (b) whether such a subagent inherits project `CLAUDE.md` and whether it sees project skills. It states the exact probe used, and the definition's design visibly matches the answer. (Today, MEASURED for the PANEL spawn path only: this scoping subagent received the full project `CLAUDE.md` as an unrequested system-reminder — a different spawn path, so it does not settle (b).)

10. RECORDED-EVIDENCE — `reviews/proving-run-a.md` (faithful spec) contains every required handoff section, non-empty, with each row in the `verified` table citing a concrete command and its actual output; the handoff schema-lint test passes over it; `grep` for `^@@`, `^\+\+\+`, `^---` returns nothing; and its line count is under the declared cap.

11. RECORDED-EVIDENCE — `reviews/proving-run-b.md` records the OMISSION DRILL, in which the spec deliberately omits "silver declares its grain and proves it". PASS iff the produced model carries a uniqueness test OR the handoff explicitly flags the omission as a spec gap — determined by grep over the drill artifacts and quoted verbatim. A silent, untested grain is a FAIL and blocks the feature. This is the only criterion that tests FEATURE_REQUEST.md:46-47 rather than testing that files exist.

12. RECORDED-EVIDENCE — for both runs, the pre-spawn `git status --porcelain` + `git diff HEAD --stat` and the post-run pair are saved into the `reviews/` trail, and the comparison shows: the tree was clean (or held only the agent's own prior work) before the spawn; no tracked file outside the declared write allowlist was modified or deleted; nothing that existed before was reverted; HEAD unchanged; `git stash list` unchanged. This is the check the scar at `implement-plan/SKILL.md:120-125` and the re-verify step at `:187-190` demand.

13. MECHANICAL — the definition contains an explicit routing rule naming `docs/data-sources.md` as the destination for any data, era, endpoint, availability, or rate-limit fact, and the memory file contains zero such claims at PR time (grep-checkable against the memory file at review).

14. USER-RUN (marked per `requests/feature-requests/README.md:56-59`) — a `/commit` run over the proving-run diff stages the memory delta as a visible per-path entry, confirming that the review gate the whole design leans on (FEATURE_REQUEST.md:140, `commit/SKILL.md:47-67`) behaves as assumed. A human reads and judges this; no command proves it.

15. USER-RUN — CI is green on the PR for all three required checks named in `ops/branch-protection.json:4`: `Lint, types, tests`, `dbt build`, `Secret scan` — with gitleaks (`ci.yml:96-99`) covering the committed memory file per ADR 0006. The push and the PR stay the user's.

16. BOOKKEEPING (mechanically greppable) — `PROJECT_SCOPE.md` opens at `scoped · decided · next: plan`, `FEATURE_REQUEST.md`'s Status blockquote is advanced, and the Index row at `requests/feature-requests/README.md:92` matches — the reconciliation `/update-docs` performs.

## Scope (tiered)

### Core (must)

- HARNESS PROBE FIRST, before either file is written: what loads `.claude/agents/*.md`, what frontmatter it accepts, where tool permissions are declared, whether project `CLAUDE.md` is inherited, whether project skills are visible. Recorded to `reviews/harness-probe.md` with a promoted epistemic label. This is de-risking, not enhancement — it is the difference between a working capability and two well-formed Markdown files nothing reads, and every shape-based acceptance criterion would still pass green in the failure case.

- `.claude/agents/<agent>.md` — the definition. Frontmatter in whatever schema the probe confirms (the eight committed `SKILL.md` files use `name` + a trigger-rich `description`; that is the SKILL format and may not be the agent format). Body carries: the manager/developer role framing; an explicit override preamble stating which inherited sections the agent ignores and which it obeys absolutely (needed if the probe confirms inheritance, since narrowness cannot then be achieved by omission); the compressed invariant set; pointers to `transform/models/bronze/README.md` and `transform/models/silver/README.md` for the layer contracts it must obey when writing models; the memory pointer; the return contract; the three-way spec-gap escalation policy; the write allowlist; git-read-only as an absolute with its recorded reason; and prohibitions on invoking pipeline skills and on editing its own definition. Written in house voice — the `SKILL.md` register.

- INVARIANTS: restate COMPRESSED and explicitly non-authoritative (naming `CLAUDE.md` as the authority), following the shape `scope_panel.js:124` already uses — a pointer-shaped reminder rather than a second body of authoritative text — AND ship the drift guard the three existing restatements (`scope_panel.js:124`, `plan_panel.js:146`, `implement-plan/SKILL.md:100-112`) conspicuously lack. Restating goes with the grain of what the repo already does; the guard is what makes a fourth copy safe.

- `.claude/agents/<agent>-memory.md` — committed, bounded, pointed at from the definition, with a stated per-entry format (date / epistemic label / the claim / an evidence pointer / a routing tag) and a header stating what belongs (implementation ergonomics: client shapes, casing surprises, tooling traps) and what routes elsewhere (`docs/data-sources.md` for data facts, `CLAUDE.md` Constraints & Gotchas for repo-wide scar tissue, `docs/decisions/` for decisions).

- THE MEMORY-VERSUS-DOCS RULE, one line, no protocol: domain and data facts never enter memory; they are reported in the handoff's `docs-delta` section and left for the main thread, which owns `/update-docs`. This is the cheapest closure of the drift hole the request identifies at FEATURE_REQUEST.md:174-180 and adds no machinery.

- THE RETURN CONTRACT AS A FILE: fixed prose sections — built / verified-with-evidence / assumed / surprised-me (memory candidates) / could-not-do / docs-delta / still-open — written to `requests/<track>-requests/<slug>/reviews/`, length-capped, forbidden to carry diff hunks, and linted by pytest for section presence and hunk-freeness. Enforcement lands on the artifact, not on the agent's output schema.

- THE THREE-WAY SPEC-GAP ESCALATION POLICY, stated in the definition: a spec that CONTRADICTS an invariant stops the agent with a spec-gap report; a spec SILENT on an invariant is built to the invariant and flagged; an AMBIGUOUS requirement is built at the smaller interpretation and flagged. All three are observable in the handoff, so the policy is testable rather than a default.

- THE WRITE-GUARD PACKAGE: a declared write allowlist in the definition; a required-clean-tree (or only-the-agent's-own-prior-work) precondition; a documented main-thread spawn protocol reusing stage 4's procedure verbatim — feature branch, pre-spawn `git diff HEAD` to gitignored `var/` scratch plus the untracked list (`implement-plan/SKILL.md:120-125`); and a post-run tree-integrity comparison written into the `reviews/` trail (`:187-190`). Do not invent a second mechanism.

- THE PYTEST GUARD SUITE under `tests/` — frontmatter validity, guardrail-clause presence, invariant drift, memory budget, memory entry format, handoff schema — each with a NEGATIVE CONTROL so no guard can pass vacuously. Under `tests/` specifically because `ci.yml` has three jobs and no Node step, so `.mjs` guards are etiquette while `tests/` is a required check via `ops/branch-protection.json:4`.

- THE PROVING RUN, two drills: (A) a faithful spec, (B) the omission drill with the grain invariant deliberately removed. Both on small, reversible, decoupled targets — never `box-score-foundation`, never into `transform/models/`. Both produce a scored artifact plus pre/post tree state under `reviews/`.

- DOC INTEGRATION: `.claude/agents/` in the CLAUDE.md project map; the subagent bullet at `CLAUDE.md:73-75` clarified so git-read-only and file-write permission are distinguishable; `.claude/agents/README.md` stating what the directory is and what the spawn protocol is (the repo already enforces self-documenting directories for dbt layers at `tests/test_repo_structure.py:77-84`); ADR 0007 recording why the first write-capable subagent exists, what replaced "it can't write", and the cost.

### Folded in (cheap wins)

- NEGATIVE CONTROLS on every new guard. `tests/test_doc_links.py:95-104` exists precisely because a link checker that scans nothing passes every time, and the recorded scar at `implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed. A few lines per guard; without them the feature ships a green suite that proves nothing about the agent.

- MEMORY ENTRIES CARRY THE REPO'S EPISTEMIC VOCABULARY. `CLAUDE.md:76-79` already demands measured/verified/inferred/assumed/unconfirmed be treated as different claims. One field per entry, and it makes the deferred curation protocol designable against evidence. Note a small pre-existing drift the implementation must pick a side on: `update-docs/SKILL.md:105` names a DIFFERENT four-label set (`measured`/`verified`/`documented`/`unconfirmed`) for `docs/data-sources.md`.

- Carried verbatim; fenced because it contains Markdown link syntax:

  ~~~
  MEMORY PATHS AS INLINE CODE, NEVER `[text](path)` MARKDOWN LINKS. Grounded, not stylistic: `tests/test_doc_links.py:72-91` checks only markdown-link syntax, so a backticked path is invisible to it, while a link to a file that later moves turns CI red on an unrelated PR with a confusing failure. One convention line in the memory header; fully avoids the failure.
  ~~~

- SEED THE MEMORY WITH 2-4 ENTRIES THE REPO HAS ALREADY EARNED, each with a citation — never invented gotchas, which is the exact schema-nobody-fills failure the request diagnoses at FEATURE_REQUEST.md:100-103. Real and verifiable today: PowerShell 5.1 `Set-Content`/`Out-File` mangle UTF-8, use the file-editing tools (`implement-plan/SKILL.md:111-112`); the bundled `.claude/skills/**/tests/*.mjs` guards are NOT run by CI (verified from `ci.yml` — three jobs, no Node step); sqlfluff errors on an empty model selection, hence the guard at `ci.yml:78-85`; the harness-probe result once measured.

- BAN DIFF HUNKS IN THE HANDOFF AND CAP ITS LENGTH. A grep for `^@@` / `^+++` / `^---` plus a line cap turns "the main thread did not have to read every edit" from a feeling into a check. Directly targets the request's core complaint (FEATURE_REQUEST.md:36-37).

- REQUIRED-CLEAN-TREE PRECONDITION BEFORE SPAWNING. The one genuinely new guard here, and it is a sentence. Every other guard is instruction; the real net is `/commit`'s per-path staging (`commit/SKILL.md:47-67`), and that net only works if a human can tell the agent's writes from their own in the staged diff. Spawning a write-capable builder onto a dirty tree destroys that distinction — the specific way this feature could lose work without any subagent doing anything forbidden.

- MAKE CLAUDE.md's 200-LINE BUDGET MECHANICAL. The memory-budget guard is the same assertion; pointing it at `CLAUDE.md` too costs about three lines and converts `update-docs/SKILL.md:76-78`'s judgment rule into a CI failure. Currently 122/200, so it lands green and stays honest.

- TRACK-AGNOSTIC BY CONSTRUCTION. `/implement-plan` already serves both feature and bugfix tracks, auto-detecting from the artifact path (`implement-plan/SKILL.md:49-53`). A handoff contract that assumes "feature" needs reworking the first time a bug is handed to it; a `track` field costs one line.

- SEPARABLE EXTRACTION vs DBT RULEBOOK SECTIONS in the invariant set. The acceptance panel already models these as two distinct specialists (`extraction` and `data-contract` in `SPEC_DEFS`, `acceptance_panel.js:197-198`). Structuring the definition so the two bodies of rules are self-contained sections makes the later split a copy rather than a rewrite, without deciding the split now.

- SPEC-TRIAGE (DRY-RUN) MODE — one paragraph in the definition plus a documented invocation phrase: the agent reads the plan, reports gaps against its invariant set, and builds nothing. Makes a bad plan cheap to discover and gives the main thread a use for the agent before it trusts it with writes.

- PROMOTION QUEUE SURFACED IN THE HANDOFF — memory entries tagged `docs-candidate` are listed in the `docs-delta` section so `/update-docs` sees them through the normal gate without the agent ever editing `docs/data-sources.md`. Keeps the curation deferral intact while preventing the drift the deferral risks.

### Gated — resolved

All eleven gated decisions were disposed by the user on 2026-08-13. Four were taken individually and
seven accepted en bloc at the panel's recommendation; each is recorded with its rationale under
*Decisions* below.

## Above & Beyond

- {"title":"Verify the spawn mechanism and `.claude/agents/` frontmatter schema BEFORE writing either file","tier":"core","rationale":"Raised by the minimalist as its top item, and the cheapest thing in the scope. Verified grounding: the repo\u0027s own machinery does not consume `.claude/agents/` at all — `scope_panel.js:174` spawns as `agent(prompt, {label, phase, schema, effort})` with no agent-type parameter — and there is no `.claude/settings.json` (checked against `git ls-files`), so there is no committed place to declare per-agent tool permissions today. Writing a definition that nothing loads is the most likely way this feature ships broken, and every shape-based acceptance criterion would still pass green in that failure. Promoted to core, not merely folded."}

- {"title":"Guards in pytest under tests/, not as a .mjs sibling","tier":"core","rationale":"Verified: `.github/workflows/ci.yml` has exactly three jobs — `Lint, types, tests`, `dbt build`, `Secret scan` — and no Node step, so the five existing `.claude/skills/**/tests/*.mjs` guards run only when an agent remembers to. Under `tests/` the guards become a required status check via `ops/branch-protection.json:4`. This is enforcement instead of etiquette, and it is what makes the acceptance criteria testable in this repo\u0027s sense. Cost: new test code must pass `mypy --strict` (`pyproject.toml:70-74`) and ruff\u0027s `PTH`/`DTZ`/`N`/`B` selection."}

- {"title":"The omission drill as a designed experiment","tier":"core","rationale":"Directly tests the request\u0027s fourth observable signal (FEATURE_REQUEST.md:46-47) and open question 8. Every other criterion tests that artifacts EXIST and are well-formed; this is the only one that tests whether the invariant set is load-bearing or decorative. A failure here is cheap now and expensive after `box-score-foundation`. Ambitious tiered it grows-build; promoted to core with the cost controlled by gating its target rather than dropping the drill."}

- {"title":"Handoff as a durable reviews/ artifact rather than a final message","tier":"core","rationale":"A message in a transcript dies with the session; a file under `reviews/` joins the provenance trail the pipeline already keeps (`requests/feature-requests/README.md:72`). It also makes the return contract greppable, which is what turns \"is the contract enforced?\" (open question 7) into a test rather than a hope — without building the anti-stub machinery a StructuredOutput schema would require."}

- {"title":"Three-way escalation policy for wrong or silent specs","tier":"core","rationale":"Answers open question 8 precisely rather than generally: contradicts-an-invariant -\u003e stop with a spec-gap report; silent-on-an-invariant -\u003e build to the invariant and flag; ambiguous -\u003e build the smaller interpretation and flag. Costs a paragraph, and without it the behavior defaults to whatever the model does, which is build silently. All three outcomes are observable in the handoff, so the policy is testable."}

- {"title":"Promotion queue surfaced in the handoff\u0027s docs-delta section","tier":"core","rationale":"The mechanical half of the deferred curation protocol. Keeps the deferral intact while closing the drift route the request itself identifies at FEATURE_REQUEST.md:174-180 — the repo holding two answers while `/update-docs` audits one. The agent never edits `docs/data-sources.md`; it queues the fact and the main thread routes it through the normal gate."}

- {"title":"A purpose-built CLAUDE.md-inheritance probe, recorded","tier":"core","rationale":"Ambitious tiered it cheap; promoted because it is inseparable from the spawn-mechanism probe and because the current evidence is weaker than ambitious claimed. What is MEASURED is that a panel-spawned subagent (this one, via `scope_panel.js`) receives the full project `CLAUDE.md` as an unrequested system-reminder. Whether a `.claude/agents/`-defined subagent inherits identically is a DIFFERENT SPAWN PATH and remains `unconfirmed`. The distinction decides whether the definition must actively override manager context or must carry more of it."}

- {"title":"CLAUDE.md convention clarification on subagent writes","tier":"core","rationale":"`CLAUDE.md:73-75` currently reads \"Subagents get read-only git\" — true, and after this feature easy to misread as \"subagents may not write\". A clarifying half-sentence prevents a future agent from refusing a legitimate instruction, and it is also what keeps the invariant-drift guard\u0027s two sides genuinely comparable. Fits trivially in the 78 lines of measured budget headroom."}

- {"title":"Negative controls for every new guard","tier":"cheap_fold","rationale":"`tests/test_doc_links.py:95-104` exists precisely because a link checker that scans nothing passes every time, and the recorded scar at `implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed. A few lines per guard; without them the feature ships a green suite that proves nothing about the agent."}

- {"title":"Memory entries carry the repo\u0027s epistemic vocabulary","tier":"cheap_fold","rationale":"`CLAUDE.md:76-79` already demands the labels be treated as different claims, and `docs/data-sources.md` models the pattern. One field per entry, and it makes the deferred curation protocol designable against evidence rather than speculation. Implementation must resolve a small pre-existing inconsistency: `update-docs/SKILL.md:105` names a four-label set that differs from CLAUDE.md\u0027s five."}

- {"title":"Memory line budget mirroring the CLAUDE.md precedent","tier":"cheap_fold","rationale":"The precedent is explicit at `update-docs/SKILL.md:76-78` (\"over budget means cutting, not reformatting\"). Reusing the MECHANISM bounds the file before it needs curation, which is the deferred piece. Folded as a mechanism; the NUMBER is gated separately because it is a judgment call, not a default."}

- {"title":"Seed memory with entries the repo has already earned","tier":"cheap_fold","rationale":"A memory that ships empty is a schema nobody fills — the exact failure the request names when deferring curation. Splits the difference between ambitious\u0027s 4-6 and the minimalist\u0027s 0-1: 2-4 entries, each traceable to a repo artifact or a probe run, never invented. The minimalist\u0027s warning is the binding constraint — an invented gotcha is worse than an empty file because it reads as authoritative in a repo whose premise is that docs are authoritative."}

- {"title":"Ban diff hunks in the handoff and cap its length","tier":"cheap_fold","rationale":"The request\u0027s core complaint is that file-by-file narration reconstitutes the detail isolation was meant to avoid (FEATURE_REQUEST.md:36-37). A grep for `^@@`/`^+++`/`^---` plus a line cap makes that objectively checkable. Two assertions."}

- {"title":"Spec-triage (dry-run) mode","tier":"cheap_fold","rationale":"One paragraph plus a documented invocation phrase buys a pre-flight: the agent reads the plan, reports gaps against its invariant set, and builds nothing. Makes a bad plan cheap to discover and — usefully for a feature whose premise is unproven — gives the main thread a reason to use the agent before trusting it with writes."}

- {"title":"Track-agnostic by construction","tier":"cheap_fold","rationale":"`/implement-plan` already serves both tracks, auto-detecting from the artifact path (`implement-plan/SKILL.md:49-53`). A handoff contract assuming \"feature\" needs reworking the first time a bug is handed to it. A `track` field costs one line now."}

- {"title":"Separable extraction vs dbt rulebook sections","tier":"cheap_fold","rationale":"Open question 9 asks whether one agent is the right granularity. The acceptance panel already models these as two distinct specialists (`acceptance_panel.js:197-198`), which is evidence the split is real. Structuring the invariant set as two self-contained sections makes a later split a copy rather than a rewrite, without deciding it against zero evidence."}

- {"title":"Make CLAUDE.md\u0027s 200-line budget mechanical","tier":"cheap_fold","rationale":"Raised by the repo-fit scoper. The memory-budget guard is the same assertion; pointing it at `CLAUDE.md` too costs about three lines and converts `update-docs/SKILL.md:76-78`\u0027s human-run one-liner into a CI failure. Measured at 122/200, so it lands green and stays honest."}

- {"title":"Mechanical memory-vs-docs routing guard","tier":"gated","rationale":"Attractive — it would mechanize the routing rule that otherwise depends on the agent\u0027s discipline plus a human\u0027s eye at `/commit`. But both the repo-fit and ambitious scopers surfaced the brittleness: a keyword guard on seasons/endpoints/rate-limits/the 2013-14 boundary will false-positive on a legitimate ergonomics entry that names an endpoint — and \"leaguegamelog returns a DataFrame, not JSON\" is simultaneously the canonical GOOD memory entry and exactly what the guard would flag. Gated with a recommendation to take it as a warning-shaped check or a curated denylist, never a hard CI gate."}

- {"title":"Run each drill more than once","tier":"gated","rationale":"Genuinely correct — agent behavior is nondeterministic and a single green run is one observation, not a property. Gated rather than folded because it multiplies the most expensive part of the build. If the user declines, the acceptance ledger must label the evidence as a single observation rather than a proof; that honesty requirement is not optional either way."}

- {"title":"A reusable snapshot + tree-integrity script under ops/","tier":"gated","rationale":"Today the snapshot protocol exists only as prose inside `implement-plan/SKILL.md:120-125`, re-typed by whoever remembers, and `ops/` is already described as \"repo governance as code\". Turning scar tissue into a tool is the right long-run move. Gated because it is net-new executable tooling in a change whose reviewability depends on staying small, and because the prose protocol is sufficient for two proving runs."}

- {"title":"Teach the acceptance panel about .claude/agents/","tier":"gated","rationale":"The gap is verified and real: `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, and the bucket lists at `implement-plan/SKILL.md:129-131` and `update-docs/SKILL.md:47-48` name `.claude/skills/` only — so the first future change to an agent definition draws only the core reviewers with no specialist lens. Every clause of the `skill-quality` mandate (`acceptance_panel.js:199`) applies verbatim to an agent definition. Gated, not folded, because the request explicitly fences `/implement-plan` (FEATURE_REQUEST.md:86-88) and because `acceptance_panel.js` is covered by two `.mjs` guards CI does not run — editing it without running both by hand is an easy silent regression."}

- {"title":"Extract one canonical invariant file that CLAUDE.md, the agent definition, and both panel scripts cite","tier":"gated","rationale":"The strongest long-run answer to the drift problem: the Data Layer rules exist at `CLAUDE.md:86-103`, `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112` with no check that they agree, and this feature adds a fourth. A single cited source kills the surface permanently instead of guarding one edge. Gated because it touches three tooling surfaces in a change whose point is a fourth, and because it hollows out `CLAUDE.md` — the onboarding map a human reads first, where the rules being inline is a feature rather than duplication."}

- {"title":"Return contract as a machine-checkable StructuredOutput schema rather than prose sections","tier":"drop","rationale":"Dropped on the minimalist\u0027s grounded objection, which is stronger than the case for it. This repo already knows what schema-forcing costs: `scope_panel.js:27` records that structured agents intermittently degenerate into placeholders, and the entire `ANTISTUB_RETRY`/`runChecked`/`safeAgent` apparatus exists to survive it. Building anti-stub machinery for one agent that has never returned once is premature. The enforcement goal is met a cheaper way — the handoff FILE\u0027s sections and hunk-freeness are linted by pytest — so this is dropped rather than deferred."}

- {"title":"Split into separate extraction and dbt-modeling agents","tier":"drop","rationale":"Dropped, not gated: the request itself defers it (FEATURE_REQUEST.md:97, 197-199) and its reasoning is correct — splitting later is cheap, and designing two rulebooks against zero proving runs is speculation compounding speculation. Structural readiness for a later split is captured instead as a cheap fold (separable rulebook sections), so nothing is lost by dropping the split itself."}

- {"title":"A /update-docs memory-coherence check","tier":"drop","rationale":"Dropped because the request explicitly fences it (FEATURE_REQUEST.md:88-90) and its stated reason holds: pruning criteria designed against zero entries produce a schema nobody fills. Folding it in silently would be exactly the laundered greed the pipeline forbids, and gating it would present the user with a decision the request already made. The `docs-delta` promotion queue covers the drift risk in the meantime."}

- {"title":"Feed the handoff into stage 4, then wire the agent as its build step","tier":"drop","rationale":"Both halves are explicitly out of scope (FEATURE_REQUEST.md:86-88, 100-103). Dropped rather than gated — but the sequencing is worth naming so it is not rediscovered: passing the handoff into the acceptance panel\u0027s context is a much smaller step than making the agent stage 4\u0027s builder, and it partially restores the inverted asymmetry open question 4 identifies (the reviewer now has less context than the author). That belongs in a follow-up request."}

## Risks & Unknowns

- PREMISE RISK, the largest. The problem is inferred, not observed. Measured: `src/nba_platform/` holds only `__init__.py`, `transform/models/` holds three READMEs and zero `.sql` files, and the entire history is three Phase-0 commits — `/implement-plan` has never run here. The request concedes this at FEATURE_REQUEST.md:16. If the first real stage-4 run fits comfortably in one context, this agent is maintenance burden, and ADR 0001:18 and :48-49 name over-processing as the specific failure mode of this repo's philosophy. Mitigation is to keep the build small and refuse the expensive couplings.

- DEAD-ARTIFACT RISK. The definition may be written in a format nothing loads. `scope_panel.js:174` spawns via `agent(prompt, {...})` with no agent-type hook, and no `.claude/settings.json` exists (both verified). If the frontmatter shape or the spawn path is wrong, the feature ships two Markdown files, a green test suite, and zero working capability — and every shape-based acceptance criterion would still pass, because they check FORM rather than BEHAVIOR. This is why the harness probe is core and the proving run cannot be dropped to save time.

- INSTRUCTIONS ARE NOT ENFORCEMENT, and the substitute guard is DETECTION, not PREVENTION. The scar at `implement-plan/SKILL.md:123-125` is specifically a write-capable agent that ran `git checkout` and silently wiped uncommitted work while a vacuous selftest passed green. Feature branch, pre-spawn snapshot, post-run integrity check, and `/commit`'s staged-list-then-yes all catch it after the fact; nothing stops it. ADR 0007 should say this plainly rather than implying the guard is equivalent to read-only.

- THE FOURTH RESTATEMENT OF THE INVARIANTS. `CLAUDE.md:86-103` is already mirrored at `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112` — none drift-checked. In a repo whose premise is that most of it is written by agents against docs treated as authoritative (`tests/test_repo_structure.py:3-6` says so explicitly), a rule that quietly disagrees with itself in one of four places is a correctness failure that produces no error. The drift guard covers one edge; three remain uncovered.

- THE DRIFT GUARD ADDS FRICTION TO ORDINARY CLAUDE.md EDITING. Any wording change to an invariant clause turns CI red until the agent definition is updated in the same commit. That is the point, but it is a real cost, and the failure message must say what to do — the same trap `CLAUDE.md`'s own note about renamed CI job names and `ops/branch-protection.json` already documents.

- NARROWNESS MAY NOT BE ACHIEVABLE BY OMISSION. Measured for the PANEL spawn path: this scoping subagent received the full project `CLAUDE.md` as an unrequested system-reminder. If `.claude/agents/` behaves the same way (unconfirmed — different spawn path), the manager/developer seam must be enforced by explicit override text, the inherited context costs tokens on every spawn, and a weak override makes the agent a normal agent with extra steps.

- VERIFICATION INVERTS AT ARM'S LENGTH. The acceptance panel, `/update-docs`, and `/commit` were all designed for code the main thread watched itself write; here the reviewer has less context than the author. CI's mechanical gates are author-agnostic and hold; the judgment layer thins exactly where the request says it matters most (FEATURE_REQUEST.md:166-172).

- THE NARROW-DEVELOPER FAILURE IS CURRENTLY UNGUARDED OUTSIDE STAGE 4. The mechanism that catches a silver model whose declared grain has no test is the stage-4 specialist (`acceptance_panel.js:197` clause 2, `implement-plan/SKILL.md:104-106`). Because this request deliberately does NOT rewire stage 4, a v1 agent spawned outside it is outside that mechanism, guarded only by prose in the definition. This is the strongest argument for the omission drill and for a low-stakes proving target.

- MEMORY IS A ROUTE AROUND THE DOC GATE. `/update-docs` audits `docs/data-sources.md`'s epistemic labels (`update-docs/SKILL.md:103-112`) and knows nothing about `.claude/agents/`. The first task of the first feature is verifying the `leaguegamelog` shape — a data fact the agent will discover while implementing. If it lands in memory, the repo holds two answers and the gate audits one.

- THE MEMORY FILE IS PUBLISHED. ADR 0006 makes the repo public from the first commit and git history permanent; gitleaks (`ci.yml:96-99`) catches credentials by content but not a carelessly pasted path, machine detail, account ID, or response fragment. A free-text file an agent appends to is the surface `/commit`'s refusal table (`commit/SKILL.md:55-63`) is weakest against, because the content is prose rather than a recognizable credential file.

- LOCAL-RED / CI-GREEN ASYMMETRY IF MEMORY WERE GITIGNORED. `tests/test_doc_links.py` excludes by directory NAME (lines 31-48) and is not gitignore-aware, so a gitignored `.claude/agents/` file would still be walked locally. A bad link would fail `uv run pytest tests/test_doc_links.py -q` — the exact command `/update-docs` Step 1 runs (`update-docs/SKILL.md:53-57`) — while CI stayed green. A concrete reason to commit, and a concrete reason for the inline-code-paths convention.

- A COMMITTED MEMORY NOBODY PRUNES GROWS MONOTONICALLY. With curation deliberately deferred, the only bounds are the line cap and a human's read at `/commit` — and a cap reached with no pruning rule turns into either an arbitrary truncation or a quietly raised cap.

- `.claude/agents/` DRAWS NO SPECIALIST REVIEWER. Verified: `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, so the first future change to the definition or memory goes through the panel with only the core reviewers — the exact blind spot `skill-quality` exists to close for `.claude/skills/`.

- PROVING-RUN EVIDENCE IS INHERENTLY WEAK. Agent behavior varies run to run, so one passing drill proves less than it appears to. Either repeat the drills or label the evidence as a single observation; a scope claiming "the design holds" off one green run is overclaiming, which in this repo is a convention violation (`CLAUDE.md:76-79`) rather than merely optimistic.

- THE HEADLINE BENEFIT IS DEFERRED BY THE SCOPE'S OWN NON-GOALS. With stage 4 untouched, nothing routinely calls the agent, so "a feature gets built without the main thread reading every edit" (FEATURE_REQUEST.md:41-42) depends on a human remembering to invoke it. The capability is real; the context savings are not yet.

- THE WHOLE FEATURE RESTS ON HARNESS BEHAVIOR THIS REPO CANNOT TEST. Whether `.claude/agents/*.md` frontmatter supports a tool allowlist, whether a subagent inherits project `CLAUDE.md`, and whether it sees project skills are properties of the Claude Code harness. They can change under a version bump with nothing in CI to notice.

- ADJACENT DRIFT FOUND WHILE GROUNDING, not this feature's job: `tests/fixtures/README.md` tells the reader to capture fixtures "with the recorder", and no recorder exists (`src/nba_platform/` is one `__init__.py`). Worth its own request; noted so it is not silently absorbed into the proving run as a convenient target.

### Added post-panel (Decision 12) — not seen by the adversaries

- RELOCATING THE RULEBOOK EDITS THE REPO'S MOST LOAD-BEARING FILE. Moving the Data Layer section out
  of `CLAUDE.md` touches the document every agent reads on every task. A bad cut — moving something
  the main thread needs, or leaving a dangling reference — degrades every future session rather than
  failing loudly. Mitigations: `CLAUDE.md` keeps a pointer, a guard asserts the pointer resolves, and
  the cut is reviewable as a diff before it lands. But no test can catch "this rule was needed in the
  manager doc and is now somewhere the manager doesn't look."

- THE RULEBOOK BECOMES A FILE BOTH READ, WHICH BLURS THE DEVELOPER-PRIVATE FRAMING. The scope's own
  carve-outs mean the main thread still builds directly sometimes, so it must read the agent
  definition to find the invariants. That is a pointer rather than a copy and costs nothing
  mechanically — but the definition is no longer purely the developer's document, and future edits
  to it affect main-thread behavior too.

- THE POST-PANEL AMENDMENTS WERE NOT ADVERSARIALLY REVIEWED. Decisions 12 and 13 changed the scope
  after the panel returned. The relocation removes a guard the adversaries had endorsed, and the
  sequel's dispatch design was never in front of them at all. Stage 3's planning panel has
  code-grounded adversaries and is the next place either can be attacked; neither has been yet.

## Affected Area & Pointers

- TARGET COMPONENT (new): `.claude/agents/` — does not exist today (verified: `git ls-files` returns only `.claude/skills/**`, and `Test-Path .claude/agents` is False). Greenfield, with no in-repo precedent for agent frontmatter.

- `.claude/skills/implement-plan/SKILL.md` — READ FIRST. Closest prior art and the source of the central tension. Specifically :100-112 (the invariant restatement the definition must mirror without contradicting), :118-125 (the snapshot protocol and the recorded scar this feature re-admits), :127-131 (the touched-area bucket list that has no `agents` key), :155-156 (the read-only-subagents rule this feature carves an exception to), :187-190 (the tree-integrity re-check the guard package reuses).

- `CLAUDE.md` — :16-33 (the project map that gains a `.claude/agents/` row), :63-82 (Project Conventions, including :73-75 the subagent read-only-git bullet needing clarification), :84-103 (the Data Layer rules that ARE the candidate invariant set). Measured: 122 lines against the 200-line budget.

- `.claude/skills/update-docs/SKILL.md` — :47-48 (the bucket list naming `.claude/skills/` only), :53-57 (the one mechanical check the doc gate owns), :66-78 (the CLAUDE.md checks and the 200-line budget precedent the memory cap reuses), :100-101 (the missing-ADR rule that makes ADR 0007 near-mandatory), :103-112 (the `docs/data-sources.md` epistemic-label audit the memory routing rule must not route around).

- `.claude/skills/implement-plan/acceptance_panel.js` — :161-163 (`READONLY`, the absolute read-only mandate and the structure a write-capable allowlist should invert), :197-201 (`SPEC_DEFS`, including the `data-contract`, `extraction`, and `skill-quality` mandates — the last applies verbatim to an agent definition), :202-206 (`AREA_TO_SPEC`, verified to have no `agents` key).

- `.claude/skills/scope-feature/scope_panel.js` — :27 (the recorded placeholder-degeneration behavior that argues against schema-forcing the return contract), :95-115 (`ANTISTUB_RETRY`/`runChecked`/`safeAgent`), :118-130 (the compressed, pointer-shaped invariant restatement whose SHAPE the agent definition should copy).

- `tests/test_repo_structure.py` — the established home for config-and-filesystem-agree guards; docstring :1-9 justifies this class of check, :77-84 is the closest structural analogue (every layer documents itself).

- `tests/test_doc_links.py` — :31-48 (`EXCLUDED_PARTS`, verified to contain no `.claude` entry, so both new files are link-checked for free), :52-53 (`MUST_COVER` and `MIN_EXPECTED_FILES = 20` — note 20, not 30), :72-91 (markdown-link-only scanning, which is why memory paths should be inline code), :95-104 (the anti-vacuity guard every new guard should imitate).

- `.claude/skills/commit/SKILL.md` — :42-45 (branch check), :47-67 (per-path staging and the refusal table — the actual review gate this design leans on), and the whole file for house voice.

- `.github/workflows/ci.yml` — verified to have exactly three jobs and NO Node step (:26-27 `Lint, types, tests`, :55-56 `dbt build`, :87-88 `Secret scan`; gitleaks at :96-99). This is why guards belong under `tests/`.

- `ops/branch-protection.json:4` — the required contexts that must stay green, matched by CI job DISPLAY NAME.

- `pyproject.toml` — :43-64 (ruff: line-length 100, selects `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF`), :70-74 (`mypy strict = true` over `src` and `tests`), :77-82 (pytest config and the `network` marker). New guard code must satisfy all of these.

- `docs/decisions/0001-deliberate-over-engineering.md` — :15-20 (the wrong-thing-to-inflate failure mode), :27-32 (what is turned all the way up versus explicitly declined), :44-53 (the honest cost section, including over-processing as a standing risk). ADR 0007 must match this register.

- `docs/decisions/README.md` — :19-25 (the required ADR sections), :29-32 (accepted ADRs are immutable — write a superseding one), :39-46 (the Index table that gains a row).

- `transform/models/silver/README.md:1-12` and `transform/models/bronze/README.md` — the layer contracts the definition should POINT AT rather than paraphrase; :5-7 of the silver README is the grounded reason the proving run must not target the dimensional core.

- `requests/feature-requests/README.md` — :45-59 (what "testable" means here, and the user-run marking rule), :61-85 (layout and status grammar), :91-92 (the Index rows, including `box-score-foundation` at `intake`).

- `docs/data-sources.md` — the destination the memory routing rule names. Everything in it is currently `unconfirmed`; the memory file must not become a second, unaudited home for anything that belongs there.

- NO DATASETS AND NO MANIFEST NAMES APPLY. `transform/models/` contains three layer READMEs and zero `.sql` files (verified via `git ls-files`), and this feature adds none. The five dataset contracts do not bind.

## Decisions

The disposition record. Decisions 1–4 were taken individually; 5–11 were accepted en bloc at the
panel's recommendation.

**1 — Timing: build now.** The minimalist's `reshape` was about timing, not form, and the merge had
folded it into a note inside another decision; an adversary flagged that as the silent fold
`scope-feature/SKILL.md:35-36` forbids, so it was surfaced as its own question. Resolved **build
now**: the pattern is proven in the user's professional experience, ADR 0001 puts process tooling in
the turned-all-the-way-up column, and `box-score-foundation` is large enough that arriving without
the agent means building it under pressure. Accepts knowingly that the pain is inferred, not
measured — recorded as the first risk.

**2 — Proving-run target: scratch for the omission drill, a real task for the faithful run.** This
reverses the request's suggestion at `FEATURE_REQUEST.md:124-126`, and is the one place this scope
overrides the request. The omission drill needs a silver-shaped target but its output should be
discarded, so a scratch dbt project under gitignored `var/` is right — and it keeps an unproven
builder out of `transform/models/`, which `transform/models/silver/README.md:5-7` calls the most
expensive mistake available in this project. The faithful run targets a small real repo task so the
evidence is a genuine diff reviewed through `/commit`. Coupling acceptance to `box-score-foundation`
was rejected: it is at `intake` with no scope and no plan.

**3 — Bash: yes, restricted, after the harness probe.** Denying Bash would make this the only actor
in the repo that cannot verify its own work — it could not run `pytest` or `dbt build` on what it
wrote, pushing verification back to the main thread and undoing the isolation the feature exists to
buy. The allowlist's *location* is gated on the probe: there is no `.claude/settings.json` in this
repo (verified against `git ls-files`), so where a tool allowlist can even be declared is unknown.

**4 — Invariants: guard now, extract later.** ~~Restate them compressed and explicitly
non-authoritative — the shape `scope_panel.js:124` already uses — plus a drift guard.~~
**SUPERSEDED by Decision 12** before any implementation. Retained for the record because it shows
what the panel recommended and why the user's alternative is better: the panel took duplication as
given and proposed policing it; relocation removes it.

**5 — Memory line cap: 120**, enforced in pytest with the cap named in the assertion message.
Tighter than `CLAUDE.md`'s 200 (measured at 122 today) because memory is read alongside the
definition on every implementation task.

**6 — Invariant-guard strictness: phrase-presence, not verbatim.** Verbatim reddens CI on any
wording change to the repo's most-edited governance file, which trains people to route around the
guard.

**7 — Teaching the panels `.claude/agents/` exists: doc half now, JS half deferred.** Adding it to
the bucket lists in `implement-plan` and `update-docs` changes no build step. The
`acceptance_panel.js` `AREA_TO_SPEC` change waits.

**8 — Proving-run repetitions: two per drill if affordable**; one acceptable *only if* the
acceptance ledger and ADR 0007 both label the result a single observation rather than a proof. Agent
behavior is nondeterministic, so one green run proves less than it appears to.

**9 — Memory-vs-docs routing guard: yes, but warning-shaped** or a curated denylist — never a hard
CI gate. Mechanizing the routing rule is worth something; making it a blocking keyword match is
brittle.

**10 — ADR 0007 timing: written after the proving runs, landed in the same PR**, status `accepted`.
`docs/decisions/README.md:29-32` makes accepted ADRs immutable, so the Consequences section cannot
be amended later — it has to be written once the evidence exists.

**11 — Write allowlist covers memory only.** The definition stays human-maintained, matching how the
request frames the pair. Extended per blocker F1 with a repo-level **deny** set (see below).

### Post-panel amendments (user, 2026-08-13)

Both were raised by the user after the panel returned and after the eleven gated decisions were
disposed. Recorded here rather than folded silently, because they change the scope the panel
adversarially reviewed.

**12 — The build rulebook moves to the agent definition; `CLAUDE.md` stays high level.** The panel
framed the invariants as a duplication problem to be policed — restate compressed, add a
phrase-presence drift guard, ship a negative control. The user rejected the framing: the granular
implementation detail should not have been in `CLAUDE.md` to begin with. Relocating it gives the
rules a single owner, which dissolves the drift surface instead of guarding it. Consequences:
Decision 4 is superseded, AC3 is withdrawn, one guard and one negative control leave the scope, and
`CLAUDE.md` shrinks against its 200-line budget (measured at 122 today). `CLAUDE.md` retains a
pointer to the definition, and a guard asserts that pointer exists, because the main thread still
builds directly for the carve-outs.

*The cut:* the **Data Layer** section and the implementation-facing gotchas (0.6s pacing, prefer
bulk endpoints, affiliation is date-dependent, Windows/LF) move. The project map, Important
Locations, Project Conventions, How to Help, the cost guardrail, the `pre-commit` naming note and
the CI-rename/branch-protection trap stay — the agent is denied `.github/` and `ops/` anyway. The
exact line-level cut is a planning-stage detail and will be visible in the IMPLEMENTATION_PLAN.

*What this does NOT fix, stated so the record is honest:* `scope_panel.js:124`,
`plan_panel.js:146` and `implement-plan/SKILL.md:100-112` each already restate these rules. This
relocates one node of that four-way duplication; it does not collapse it. The extraction fix stays
deferred. `/update-docs` checks "the rules sections" of `CLAUDE.md`, so its checklist follows the
content — folded into the doc-half work already scoped at Decision 7.

**13 — Dispatch is split into an immediately-following request, not deferred indefinitely.** The
user challenged non-goal 13 directly: if silver models are the paradigm use case, why is the agent
optional? The honest answer is that non-required was never an independent choice — it restates
"stage 4 untouched," and the panel had already filed the consequence as a risk. Rather than widen a
scope the panel never reviewed in that shape, dispatch becomes request #2 and lands immediately
after, so it routes to a builder that has already passed its proving drills.

### Sequel — the dispatch request (not built here)

Recorded now so the design isn't re-derived cold. **Not in scope for this request.**

The routing rule: **an agent's declared write allowlist is its routing table.** `/implement-plan`
compares the plan's target paths against the allowlists of every `.claude/agents/*.md`:

- targets ⊆ one agent's allowlist → dispatch to that agent
- targets touch no agent's allowlist (`docs/`, `tests/`, `.github/`, `ops/`, `.claude/`) → main
  thread builds
- targets span both → main thread builds the out-of-allowlist parts, and records which and why
- two agents claim the same path → **hard error**, never a silent guess

This answers "are we updating the codebase?" without asking a model to judge it, and it is testable
as a pure function from paths to a builder. Two properties worth keeping:

- **The bootstrap resolves itself.** `.claude/**` sits in every agent's deny set, so a plan
  targeting `.claude/agents/` always routes to the main thread. No agent can build an agent,
  including itself — which is why *this* request is built by the main thread, and not as a
  special case.
- **It scales to a second agent without touching the skill.** Build the table by reading the agents
  directory rather than hardcoding names, and a future report-builder is a new file, not a new
  branch in `/implement-plan`.

Precedent: `acceptance_panel.js:202-206` already routes areas → specialist *reviewers* via
`AREA_TO_SPEC`. This is the same mechanism pointed at *builders*. Decision 7 already put adding an
`agents` key on the table. Dependency: the harness probe must confirm a machine-readable allowlist
can be declared — which is why this sequences after, not alongside.

### Blocker fixes adopted as scope

Six blockers were adopted as corrections rather than put to the user individually:

- **F1** — the write allowlist as drafted was not a bound ("the memory file and the task's target
  paths" merely restates "the spec decides"), leaving `.github/`, `ops/`, `tests/` and `.claude/`
  writable — i.e. the agent could edit the guards that catch it and report green, which is the 2026
  restaging of the recorded scar. Replaced with allowlist **and** a repo-level deny set asserted by a
  test, with the memory file as the single carve-out.
- **F2 / A2-03** — the only behavior-testing criterion wrote its evidence into gitignored `var/`,
  making it unreproducible and invisible to CI, and the proving run depended on fixtures that do not
  exist. Evidence now lands in committed `reviews/` artifacts; fixture creation is explicit work.
- **F3** — acceptance criterion 1 contradicted the scope's own core deliverables and asserted an
  unverified frontmatter schema; it is now gated on the harness probe's finding.
- **A2-01** — no criterion proved the *definition* caused the behavior; the omission drill (AC11) is
  the criterion that does.
- **A2-02** — the harness probe was core but carried no decision rule for a negative answer; a
  negative finding now stops the build and returns to scoping rather than proceeding.

## Panel Trail

Raw proposals from the three divergent scopers: `reviews/scope-proposals.md`. Adversary findings,
the convergence map, and the merged scope as emitted: `reviews/scope-adversarial.md`. Panel health:
3/3 scopers, 2/2 adversaries, no degraded lenses; 52 findings (6 blockers, 19 majors). Panel content
in those files is fenced because it contains Markdown link syntax that does not resolve from
`reviews/`.

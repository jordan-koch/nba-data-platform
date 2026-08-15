# Scoping Panel - Adversarial Findings and Convergence

Verbatim adversary output plus the convergence map. Recorded as provenance -
findings here may have been judged overstated during triage; the disposition
lives in PROJECT_SCOPE.md, not here.

Panel content is fenced (see the note in scope-proposals.md).

Totals: 52 findings - 6 blockers, 19 majors.

## Adversary summaries

~~~
adversary: fit-ac
summary: I read FEATURE_REQUEST.md in full, then resolved every load-bearing citation in the merged scope against the actual repo. Most of the grounding holds: `.claude/agents/` genuinely does not exist (Test-Path False; `git ls-files` shows only `.claude/skills/**`, 16 files); `.gitignore` has no `.claude` entry; there is no `.claude/settings.json` even untracked; `ci.yml` has exactly three jobs and no Node step; `ops/branch-protection.json:4` lists exactly those display names; `EXCLUDED_PARTS` (tests/test_doc_links.py:31-48) has no `.claude` entry and `MIN_EXPECTED_FILES = 20` at line 53; `box-score-foundation` is at `intake`; `transform/models/silver/README.md:5-7` says what is quoted; ADR 0001:27-28 and :48-49 check out; implement-plan/SKILL.md:100-112, :120-125, :127-131, :155-156, :187-190 all resolve; acceptance_panel.js:163 READONLY and :202-206 AREA_TO_SPEC (no `agents` key) check out; the update-docs/SKILL.md:105 vs CLAUDE.md:76 label drift is real. The MEASURED claim that a panel-spawned subagent receives the full project CLAUDE.md is true — I received it. The repo-fit verdict is substantively accurate.

Where it fails is on the three things this lens exists to test. (1) FRAMING: the verdict "clean" absorbs a reshape that was about TIMING, and decoupling the proving target does not answer timing at all — the build-this-now question survives only as a NOTE buried inside gated decision 1, which is the silent fold scope-feature/SKILL.md:35-36 forbids. Separately, three of the request's four observable signals (FEATURE_REQUEST.md:41-47) have no acceptance criterion. (2) ACCEPTANCE TESTABILITY: the one criterion that tests behavior rather than shape (AC11, the omission drill) is recommended to run into gitignored `var/`, making its evidence uncommitted, un-re-runnable, invisible to dbt build and to the acceptance panel — it degrades into the human-eyeball criterion requests/feature-requests/README.md:47-59 rules out. AC1 contradicts the scope's own core deliverables and asserts a frontmatter schema the scope elsewhere flags as unverified. The invariant-drift guard as specified is one-directional. Six criteria sit in an invented category ("RECORDED-EVIDENCE") the pipeline contract does not define. (3) NON-GOALS: the write allowlist — the headline replacement for "it can't write" — is defined as "the memory file and the task's target paths", which is not a bound, and leaves .github/workflows/ci.yml, ops/branch-protection.json, tests/, .gitignore and .claude/ writable, i.e. the agent can edit the guards that catch it.

I also measured two things the scope got numerically wrong: `Measure-Object -Line` returns 122 because it counts non-blank lines only — CLAUDE.md is physically 140 lines, so headroom is ~60 not 78, and the proposed pytest budget guard would silently redefine "line" relative to update-docs/SKILL.md:76-78. And the invariant restatement surface is ~9 sites, not the 3 the scope counted.

adversary: scope-completeness
summary: ADVERSARY 2 — scope discipline & completeness. The merged scope is well-grounded and most of its citations check out (I re-verified ~35 against the tree; four are wrong or misleading, recorded below). But it fails its own discipline in one direction and has a cluster of blind spots in the other.

OVER-REACH. The scope's risk #1 says the premise is inferred not observed, and its mitigation is "keep the build genuinely small." The tiering contradicts that: core carries eleven items, cheap_folds twelve more. What ships is two Markdown artifacts + a directory README + an ADR + ~12 mypy-strict pytest tests (six guards, each with a negative control) + two proving drills (recommended 2x each) + three recorded-evidence files + CLAUDE.md edits. Three folds are laundered greed: `.claude/agents/README.md` (justified by `tests/test_repo_structure.py:77-84`, which covers only dbt medallion layers — and `.claude/skills/` itself has no README, verified); "make CLAUDE.md's 200-line budget mechanical" (unrelated governance surface, and it silently moves an item CLAUDE.md:80-82 assigns to the judgment layer into the mechanical layer); and spec-triage mode (a second operating mode no criterion tests). Gated decision #1's recommendation takes BOTH options (a) and (b), converting a gate into a fold and landing a second unscoped piece of repo work inside a PR about agent tooling.

BLIND SPOTS. Largest: nothing in the acceptance criteria proves the file under `.claude/agents/` is what caused the behavior — every criterion checks form, or checks an artifact the main thread could have written. The scope names dead-artifact risk as #2 and does not close it. Second: the harness probe is core with no decision rule — if it answers "nothing loads this," there is no branch, no reshape, no abandon criterion. Third: `tests/fixtures/` holds only a README (verified, zero fixtures), yet the proving-run design and a non-goal both specify "committed fixtures." Fourth: the write allowlist is prose-only and this session declares a second working directory outside the repo — no non-goal fences the agent to the repo root, and the entire detection apparatus is git-scoped and blind there. Fifth: the diff-hunk lint will false-positive, because every SKILL.md uses bare `---` lines (4-5 each, measured) and a handoff in house voice will too.

Four citation corrections: the `AREA_TO_SPEC` "JS half" is unnecessary (the `skills` key already exists — only prose needs widening); the claim that every clause of `skill-quality` applies verbatim to an agent definition is false against `acceptance_panel.js:199`; `AREA_TO_SPEC.tests` maps to `extraction`, so this PR's own guard suite draws the wrong specialist; and CLAUDE.md:40 says "Six ADRs" — drift the ADR-0007 item misses.
~~~

## Convergence map

Where two or more scopers independently agreed - the highest-signal material.

~~~
theme: This touches no dataset — the five dataset contracts do not bind and must not be manufactured
scopers: ["fit","ambitious","minimalist"]
why_high_signal: All three independently refused to invent grain/keys/era-coverage/update-semantics/extraction-cost for a tooling change, each citing FEATURE_REQUEST.md:107 plus the verified absence of any model or extraction code. Unanimous refusal to pad a scope with inapplicable contracts is the strongest possible signal that the exemption is real rather than convenient.

theme: CLAUDE.md:73-75 constrains subagent GIT, not subagent FILE WRITES — no ADR is contradicted, but the wording needs a clarifying half-sentence
scopers: ["fit","ambitious","minimalist"]
why_high_signal: All three read the bullet the same way and all three independently proposed the same tiny remedy. That converts the feature's most apparent rule conflict into a documentation fix, and it means ADR 0007 records a first rather than a reversal.

theme: The scar at implement-plan/SKILL.md:120-125 is the governing constraint, and the replacement guard is detection rather than prevention
scopers: ["fit","ambitious","minimalist"]
why_high_signal: All three named the same incident, reached the same conclusion that instructions are not enforcement, and converged on reusing stage 4's existing procedure verbatim rather than inventing a second mechanism. The minimalist added the one genuinely new guard nobody else found — require a clean tree before spawning, because a dirty tree destroys a human's ability to separate the agent's writes from their own in the staged diff.

theme: The memory file must be COMMITTED, with a line cap enforced by a test rather than by prose
scopers: ["fit","ambitious","minimalist"]
why_high_signal: Three independent routes to the same answer: reviewability through `/commit`, the `update-docs/SKILL.md:76-78` budget precedent, and — the minimalist's uniquely grounded argument — that `tests/test_doc_links.py` excludes by directory name and is not gitignore-aware, so a gitignored memory file produces local-red/CI-green. Convergence plus a mechanism nobody else spotted.

theme: New guards belong under tests/ as pytest, with negative controls, because CI runs no Node step
scopers: ["fit","ambitious","minimalist"]
why_high_signal: All three independently proposed mechanical guards for a prose artifact, and two verified the same underlying fact — `ci.yml` has three jobs and no Node step, so the five existing `.mjs` skill guards are never enforced. This converts the request's untestable claims into required status checks via `ops/branch-protection.json:4` and is the single largest value-add over the request as written.

theme: The proving run must NOT target box-score-foundation
scopers: ["ambitious","minimalist"]
why_high_signal: The request explicitly proposes it (FEATURE_REQUEST.md:124-126), and two scopers independently rejected it on the same grounded reasoning: `box-score-foundation` is at `intake` with no scope and no plan (`requests/feature-requests/README.md:91`), and `transform/models/silver/README.md:5-7` calls getting silver wrong the most expensive mistake available in this project. Two lenses overriding the request on the same evidence is the strongest form of this signal.

theme: A subagent DOES appear to inherit project CLAUDE.md, so narrowness cannot be achieved by omission — but the evidence is spawn-path-specific
scopers: ["ambitious","minimalist"]
why_high_signal: Both reported the same first-hand observation from their own spawn — the full project `CLAUDE.md` arrived as an unrequested system-reminder. Two independent observations of the same behavior make it `measured` for the panel spawn path. The minimalist's added caution is the load-bearing part: `.claude/agents/` is a DIFFERENT spawn path, so the answer stays `unconfirmed` there, which is exactly why the probe is core.

theme: `.claude/agents/` falls into no acceptance-panel bucket, so future changes to it draw no specialist reviewer
scopers: ["fit","ambitious"]
why_high_signal: Both independently traced `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) and found the same one-word gap, and both noted that every clause of the `skill-quality` mandate at :199 applies verbatim to an agent definition. A verified, precisely located blind spot — gated rather than folded only because the request fenced that file.

theme: Restating the invariants creates a fourth undrift-checked copy; the guard is what makes restatement safe
scopers: ["fit","ambitious","minimalist"]
why_high_signal: All three identified the duplication problem; fit and ambitious both located the same three existing restatements (`scope_panel.js:124`, `plan_panel.js:146`, `implement-plan/SKILL.md:100-112`), none drift-checked. The minimalist supplied the shape constraint the other two missed — `scope_panel.js:124` restates COMPRESSED and pointer-shaped, never as authoritative text — which is what makes the synthesis (compressed restatement plus drift guard) better than either extreme.

theme: Something must actually catch a silver model with a declared-but-untested grain when the agent runs outside stage 4
scopers: ["ambitious","minimalist"]
why_high_signal: The ambitious scoper proposed the omission drill as a designed experiment; the minimalist independently identified the same hole from the other direction — that stage 4's specialist (`implement-plan/SKILL.md:104-106`, `acceptance_panel.js:197`) is the only mechanism that currently catches it, and the non-goal of rewiring stage 4 puts the agent outside it. Two lenses, one conclusion: the omission drill is the only criterion that tests behavior rather than shape.
~~~

## Merged scope (as the panel emitted it)

### goals

~~~
- Stand up `.claude/agents/` as a tracked, first-class directory holding ONE write-capable implementation agent definition, so the main thread can hand a decided spec to a builder at arm's length and spend its context on strategy rather than on file-by-file narration.
- Verify — before writing a line of it — what actually loads a `.claude/agents/*.md` on this harness and what frontmatter it accepts, so the feature cannot ship as two well-formed Markdown files that nothing reads. Currently `unconfirmed`: `scope_panel.js:174` spawns via `agent(prompt, {label, phase, schema, effort})` with no agent-type parameter, and there is no `.claude/settings.json` in the repo (verified against `git ls-files`).
- Carry a bounded invariant set the agent honors even when the spec forgets to restate it — resolve-by-name, immutable landing zone, bronze 1:1, silver declares AND proves its grain, facts MERGE on key, era boundaries explicit, layer promotion gated on tests, never commit/merge/push/amend, git read-only — and make the two-copies-of-one-rule problem mechanical rather than cultural via a drift guard that reddens when either side is edited alone.
- Give implementation-earned knowledge a durable, bounded, committed, reviewable home: a memory file the agent appends to, with a stated entry format, an enforced line cap, and an explicit routing rule sending anything that would change an analyst's answer to `docs/data-sources.md` through the normal doc gate instead.
- Make the return contract an artifact rather than a request: a fixed-section handoff written under the request's `reviews/` directory — built / verified-with-evidence / assumed / surprised-me (memory candidates) / could-not-do / docs-delta / still-open — length-capped and mechanically checked to contain no diff hunks, so "the main thread did not have to read every edit" is objectively checkable instead of a feeling.
- Replace "it can't write" with a deliberate substitute guard rather than an assumed one: git read-only stated absolutely, a declared write allowlist, a required-clean-tree precondition, a pre-spawn snapshot to gitignored `var/`, and a post-run tree-integrity comparison recorded as evidence — reusing stage 4's exact procedure (`implement-plan/SKILL.md:120-125`, `:187-190`) rather than inventing a second mechanism.
- Answer the contamination question with recorded evidence and a promoted epistemic label — does a `.claude/agents/`-spawned subagent inherit project `CLAUDE.md`, and does it see project skills — because the answer decides whether the definition must actively override manager context or must carry more of it.
- Prove the design twice on small, reversible, decoupled targets: a faithful-spec run, and an OMISSION DRILL in which the spec deliberately drops "silver declares its grain and proves it" — the only criterion that tests the request's fourth observable signal (FEATURE_REQUEST.md:46-47) rather than merely testing that the files exist.
- Add mechanical guards under `tests/` (not as a `.mjs` sibling), each with a negative control, so the invariants, the budget, the frontmatter and the handoff shape are CI-enforced rather than trusted. Verified: `.github/workflows/ci.yml` has three jobs and no Node step, so the existing `.claude/skills/**/tests/*.mjs` guards are etiquette; `tests/` is enforcement via `ops/branch-protection.json:4`.
- Leave the existing verification posture intact — `/implement-plan` and its acceptance panel keep working exactly as they do today — and land the doc integration the change earns: `.claude/agents/` in the CLAUDE.md project map, the subagent convention clarified, and ADR 0007 recording why the first write-capable subagent exists and what guards it.
~~~

### non_goals

~~~
- NOT rewiring `/implement-plan` to use the agent as its build step. Stage 4 keeps building the way `implement-plan/SKILL.md` Step 3 describes and its acceptance panel is untouched (FEATURE_REQUEST.md:86-88). The agent stands alone first.
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
- NOT making the agent a required path. The main thread must retain the ability to build directly; this is a tool, not a gate.
- NOT solving the context-savings problem end to end. With stage 4 untouched, this scope buys the CAPABILITY and proves it once; realizing the benefit routinely requires a later request that wires the agent into a stage.
~~~

### acceptance_criteria

~~~
- MECHANICAL — `uv run pytest tests/test_repo_structure.py -q` is green with a new guard asserting `.claude/agents/` exists, contains exactly one `*.md` agent definition, and that file opens with YAML frontmatter parsing to a non-empty `name` and `description`. Same structural-agreement class as `test_every_layer_documents_itself` (`tests/test_repo_structure.py:77-84`).
- MECHANICAL — the guard suite asserts the definition contains the literal guardrail clauses for read-only git (naming `checkout`/`reset`/`restore`/`clean`/`stash`) and for never commit/merge/push/amend. Substring assertions suffice; the job is to redden loudly if a future edit silently deletes a guardrail, not to interpret it.
- MECHANICAL — an invariant-drift guard is green: for each invariant the definition declares it carries, the test asserts a corresponding rule is present in `CLAUDE.md`, and fails if either side is edited alone. It ships with a committed NEGATIVE CONTROL — a mutated in-test copy that makes the assertion fail — mirroring `test_the_guard_actually_covers_the_repo` (`tests/test_doc_links.py:95-104`), whose entire reason for existing is that a checker scanning nothing passes every time.
- MECHANICAL — a memory-budget guard is green: the memory file exists at the path the definition names, is referenced BY that path from the definition, and its line count is at or under the agreed cap, with the assertion message naming the cap. A negative control proves an over-budget file fails. This makes mechanical what `update-docs/SKILL.md:76-78` currently enforces only by asking an agent to run a PowerShell one-liner.
- MECHANICAL — `uv run pytest tests/test_doc_links.py -q` is green with both new Markdown files in the scanned set. Verified automatic: `EXCLUDED_PARTS` (`tests/test_doc_links.py:31-48`) contains no `.claude` entry, and `MIN_EXPECTED_FILES = 20` (line 53) against 30 tracked `.md` files today, rising to at least 33.
- MECHANICAL — `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy` are green. New test code must satisfy the repo's real gates: mypy is `strict = true` over `files = ["src", "tests"]` (`pyproject.toml:70-74`) and ruff selects `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF` at line-length 100 (`pyproject.toml:43-64`).
- MECHANICAL — `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns under 200 after the edit. Measured today: 122, so 78 lines of headroom; stated so the budget claim is checked rather than assumed. The project-map block (`CLAUDE.md:16-33`) contains a `.claude/agents/` entry alongside the existing `.claude/skills/` line, and the subagent bullet (`CLAUDE.md:73-75`) reads so a reader can tell that an agent editing a tracked file is not violating it.
- MECHANICAL — `docs/decisions/0007-*.md` exists carrying Status / Context / Decision / Consequences / Alternatives considered per `docs/decisions/README.md:19-25`, its row appears in that file's Index table (lines 39-46), and the link test proves the index link resolves.
- RECORDED-EVIDENCE — `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` exists and answers BOTH halves with an epistemic label of `verified` or `measured`, never `unconfirmed`: (a) what loads a `.claude/agents/*.md` definition, what frontmatter schema it accepts, and where tool permissions are declared; (b) whether such a subagent inherits project `CLAUDE.md` and whether it sees project skills. It states the exact probe used, and the definition's design visibly matches the answer. (Today, MEASURED for the PANEL spawn path only: this scoping subagent received the full project `CLAUDE.md` as an unrequested system-reminder — a different spawn path, so it does not settle (b).)
- RECORDED-EVIDENCE — `reviews/proving-run-a.md` (faithful spec) contains every required handoff section, non-empty, with each row in the `verified` table citing a concrete command and its actual output; the handoff schema-lint test passes over it; `grep` for `^@@`, `^\+\+\+`, `^---` returns nothing; and its line count is under the declared cap.
- RECORDED-EVIDENCE — `reviews/proving-run-b.md` records the OMISSION DRILL, in which the spec deliberately omits "silver declares its grain and proves it". PASS iff the produced model carries a uniqueness test OR the handoff explicitly flags the omission as a spec gap — determined by grep over the drill artifacts and quoted verbatim. A silent, untested grain is a FAIL and blocks the feature. This is the only criterion that tests FEATURE_REQUEST.md:46-47 rather than testing that files exist.
- RECORDED-EVIDENCE — for both runs, the pre-spawn `git status --porcelain` + `git diff HEAD --stat` and the post-run pair are saved into the `reviews/` trail, and the comparison shows: the tree was clean (or held only the agent's own prior work) before the spawn; no tracked file outside the declared write allowlist was modified or deleted; nothing that existed before was reverted; HEAD unchanged; `git stash list` unchanged. This is the check the scar at `implement-plan/SKILL.md:120-125` and the re-verify step at `:187-190` demand.
- MECHANICAL — the definition contains an explicit routing rule naming `docs/data-sources.md` as the destination for any data, era, endpoint, availability, or rate-limit fact, and the memory file contains zero such claims at PR time (grep-checkable against the memory file at review).
- USER-RUN (marked per `requests/feature-requests/README.md:56-59`) — a `/commit` run over the proving-run diff stages the memory delta as a visible per-path entry, confirming that the review gate the whole design leans on (FEATURE_REQUEST.md:140, `commit/SKILL.md:47-67`) behaves as assumed. A human reads and judges this; no command proves it.
- USER-RUN — CI is green on the PR for all three required checks named in `ops/branch-protection.json:4`: `Lint, types, tests`, `dbt build`, `Secret scan` — with gitleaks (`ci.yml:96-99`) covering the committed memory file per ADR 0006. The push and the PR stay the user's.
- BOOKKEEPING (mechanically greppable) — `PROJECT_SCOPE.md` opens at `scoped · decided · next: plan`, `FEATURE_REQUEST.md`'s Status blockquote is advanced, and the Index row at `requests/feature-requests/README.md:92` matches — the reconciliation `/update-docs` performs.
~~~

### risks

~~~
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
~~~

### grounding_pointers

~~~
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
~~~

### tiered_scope.core

~~~
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
~~~

### tiered_scope.cheap_folds

~~~
- NEGATIVE CONTROLS on every new guard. `tests/test_doc_links.py:95-104` exists precisely because a link checker that scans nothing passes every time, and the recorded scar at `implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed. A few lines per guard; without them the feature ships a green suite that proves nothing about the agent.
- MEMORY ENTRIES CARRY THE REPO'S EPISTEMIC VOCABULARY. `CLAUDE.md:76-79` already demands measured/verified/inferred/assumed/unconfirmed be treated as different claims. One field per entry, and it makes the deferred curation protocol designable against evidence. Note a small pre-existing drift the implementation must pick a side on: `update-docs/SKILL.md:105` names a DIFFERENT four-label set (`measured`/`verified`/`documented`/`unconfirmed`) for `docs/data-sources.md`.
- MEMORY PATHS AS INLINE CODE, NEVER `[text](path)` MARKDOWN LINKS. Grounded, not stylistic: `tests/test_doc_links.py:72-91` checks only markdown-link syntax, so a backticked path is invisible to it, while a link to a file that later moves turns CI red on an unrelated PR with a confusing failure. One convention line in the memory header; fully avoids the failure.
- SEED THE MEMORY WITH 2-4 ENTRIES THE REPO HAS ALREADY EARNED, each with a citation — never invented gotchas, which is the exact schema-nobody-fills failure the request diagnoses at FEATURE_REQUEST.md:100-103. Real and verifiable today: PowerShell 5.1 `Set-Content`/`Out-File` mangle UTF-8, use the file-editing tools (`implement-plan/SKILL.md:111-112`); the bundled `.claude/skills/**/tests/*.mjs` guards are NOT run by CI (verified from `ci.yml` — three jobs, no Node step); sqlfluff errors on an empty model selection, hence the guard at `ci.yml:78-85`; the harness-probe result once measured.
- BAN DIFF HUNKS IN THE HANDOFF AND CAP ITS LENGTH. A grep for `^@@` / `^+++` / `^---` plus a line cap turns "the main thread did not have to read every edit" from a feeling into a check. Directly targets the request's core complaint (FEATURE_REQUEST.md:36-37).
- REQUIRED-CLEAN-TREE PRECONDITION BEFORE SPAWNING. The one genuinely new guard here, and it is a sentence. Every other guard is instruction; the real net is `/commit`'s per-path staging (`commit/SKILL.md:47-67`), and that net only works if a human can tell the agent's writes from their own in the staged diff. Spawning a write-capable builder onto a dirty tree destroys that distinction — the specific way this feature could lose work without any subagent doing anything forbidden.
- MAKE CLAUDE.md's 200-LINE BUDGET MECHANICAL. The memory-budget guard is the same assertion; pointing it at `CLAUDE.md` too costs about three lines and converts `update-docs/SKILL.md:76-78`'s judgment rule into a CI failure. Currently 122/200, so it lands green and stays honest.
- TRACK-AGNOSTIC BY CONSTRUCTION. `/implement-plan` already serves both feature and bugfix tracks, auto-detecting from the artifact path (`implement-plan/SKILL.md:49-53`). A handoff contract that assumes "feature" needs reworking the first time a bug is handed to it; a `track` field costs one line.
- SEPARABLE EXTRACTION vs DBT RULEBOOK SECTIONS in the invariant set. The acceptance panel already models these as two distinct specialists (`extraction` and `data-contract` in `SPEC_DEFS`, `acceptance_panel.js:197-198`). Structuring the definition so the two bodies of rules are self-contained sections makes the later split a copy rather than a rewrite, without deciding the split now.
- SPEC-TRIAGE (DRY-RUN) MODE — one paragraph in the definition plus a documented invocation phrase: the agent reads the plan, reports gaps against its invariant set, and builds nothing. Makes a bad plan cheap to discover and gives the main thread a use for the agent before it trusts it with writes.
- PROMOTION QUEUE SURFACED IN THE HANDOFF — memory entries tagged `docs-candidate` are listed in the `docs-delta` section so `/update-docs` sees them through the normal gate without the agent ever editing `docs/data-sources.md`. Keeps the curation deferral intact while preventing the drift the deferral risks.
~~~

### tiered_scope.gated

~~~
- THE PROVING-RUN TARGET — the headline gate; carries the minimalist's reshape and the request-reversal. Not "a small task": naming it concretely is part of disposing this scope.
- THE MEMORY LINE CAP — the exact number is a judgment call the scope should not make silently.
- BASH, AND WITH WHAT ALLOWLIST — the scar makes this the most consequential permission decision in the feature, and there may be no committed place to declare it (no `.claude/settings.json` exists).
- INVARIANT-GUARD STRICTNESS — verbatim-identical text versus phrase-presence. Verbatim is stricter and reddens CI on any wording change to `CLAUDE.md`; phrase-presence is looser and can pass on a rule that has drifted in meaning.
- EXTRACTING A CANONICAL INVARIANT FILE that `CLAUDE.md`, the agent definition, and both panel scripts cite — kills the drift surface permanently instead of guarding one edge, but touches three tooling surfaces in a change whose point is a fourth, and fragments the rules a human onboards from.
- TEACHING THE PANELS THAT `.claude/agents/` EXISTS — `AREA_TO_SPEC` (`acceptance_panel.js:202-206`, verified: no `agents` key) and the bucket lists at `implement-plan/SKILL.md:129-131` and `update-docs/SKILL.md:47-48`. Gated rather than folded because it edits files the request fenced off (FEATURE_REQUEST.md:86-88).
- A MECHANICAL MEMORY-VS-DOCS ROUTING GUARD (a test that fails when memory mentions seasons, endpoints, rate limits, or the 2013-14 boundary) — mechanizes the routing rule but is brittle and will false-positive on a legitimate ergonomics entry that names an endpoint.
- HOW MANY PROVING-RUN REPETITIONS before the design is called proven — this directly sets how strongly the acceptance ledger may be worded.
- A REUSABLE SNAPSHOT + TREE-INTEGRITY SCRIPT UNDER `ops/` — turns stage 4's prose protocol (`implement-plan/SKILL.md:120-125`) into an executable any future spawner can call. `ops/` is already "repo governance as code", but this is net-new tooling in a change that should stay small.
- ADR 0007 TIMING — written with the change, or after the proving run (accepted ADRs are immutable per `docs/decisions/README.md:29-32`, so this is not reversible later).
~~~

### above_and_beyond

~~~
title: Verify the spawn mechanism and `.claude/agents/` frontmatter schema BEFORE writing either file
tier: core
rationale: Raised by the minimalist as its top item, and the cheapest thing in the scope. Verified grounding: the repo's own machinery does not consume `.claude/agents/` at all — `scope_panel.js:174` spawns as `agent(prompt, {label, phase, schema, effort})` with no agent-type parameter — and there is no `.claude/settings.json` (checked against `git ls-files`), so there is no committed place to declare per-agent tool permissions today. Writing a definition that nothing loads is the most likely way this feature ships broken, and every shape-based acceptance criterion would still pass green in that failure. Promoted to core, not merely folded.

title: Guards in pytest under tests/, not as a .mjs sibling
tier: core
rationale: Verified: `.github/workflows/ci.yml` has exactly three jobs — `Lint, types, tests`, `dbt build`, `Secret scan` — and no Node step, so the five existing `.claude/skills/**/tests/*.mjs` guards run only when an agent remembers to. Under `tests/` the guards become a required status check via `ops/branch-protection.json:4`. This is enforcement instead of etiquette, and it is what makes the acceptance criteria testable in this repo's sense. Cost: new test code must pass `mypy --strict` (`pyproject.toml:70-74`) and ruff's `PTH`/`DTZ`/`N`/`B` selection.

title: The omission drill as a designed experiment
tier: core
rationale: Directly tests the request's fourth observable signal (FEATURE_REQUEST.md:46-47) and open question 8. Every other criterion tests that artifacts EXIST and are well-formed; this is the only one that tests whether the invariant set is load-bearing or decorative. A failure here is cheap now and expensive after `box-score-foundation`. Ambitious tiered it grows-build; promoted to core with the cost controlled by gating its target rather than dropping the drill.

title: Handoff as a durable reviews/ artifact rather than a final message
tier: core
rationale: A message in a transcript dies with the session; a file under `reviews/` joins the provenance trail the pipeline already keeps (`requests/feature-requests/README.md:72`). It also makes the return contract greppable, which is what turns "is the contract enforced?" (open question 7) into a test rather than a hope — without building the anti-stub machinery a StructuredOutput schema would require.

title: Three-way escalation policy for wrong or silent specs
tier: core
rationale: Answers open question 8 precisely rather than generally: contradicts-an-invariant -> stop with a spec-gap report; silent-on-an-invariant -> build to the invariant and flag; ambiguous -> build the smaller interpretation and flag. Costs a paragraph, and without it the behavior defaults to whatever the model does, which is build silently. All three outcomes are observable in the handoff, so the policy is testable.

title: Promotion queue surfaced in the handoff's docs-delta section
tier: core
rationale: The mechanical half of the deferred curation protocol. Keeps the deferral intact while closing the drift route the request itself identifies at FEATURE_REQUEST.md:174-180 — the repo holding two answers while `/update-docs` audits one. The agent never edits `docs/data-sources.md`; it queues the fact and the main thread routes it through the normal gate.

title: A purpose-built CLAUDE.md-inheritance probe, recorded
tier: core
rationale: Ambitious tiered it cheap; promoted because it is inseparable from the spawn-mechanism probe and because the current evidence is weaker than ambitious claimed. What is MEASURED is that a panel-spawned subagent (this one, via `scope_panel.js`) receives the full project `CLAUDE.md` as an unrequested system-reminder. Whether a `.claude/agents/`-defined subagent inherits identically is a DIFFERENT SPAWN PATH and remains `unconfirmed`. The distinction decides whether the definition must actively override manager context or must carry more of it.

title: CLAUDE.md convention clarification on subagent writes
tier: core
rationale: `CLAUDE.md:73-75` currently reads "Subagents get read-only git" — true, and after this feature easy to misread as "subagents may not write". A clarifying half-sentence prevents a future agent from refusing a legitimate instruction, and it is also what keeps the invariant-drift guard's two sides genuinely comparable. Fits trivially in the 78 lines of measured budget headroom.

title: Negative controls for every new guard
tier: cheap_fold
rationale: `tests/test_doc_links.py:95-104` exists precisely because a link checker that scans nothing passes every time, and the recorded scar at `implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed. A few lines per guard; without them the feature ships a green suite that proves nothing about the agent.

title: Memory entries carry the repo's epistemic vocabulary
tier: cheap_fold
rationale: `CLAUDE.md:76-79` already demands the labels be treated as different claims, and `docs/data-sources.md` models the pattern. One field per entry, and it makes the deferred curation protocol designable against evidence rather than speculation. Implementation must resolve a small pre-existing inconsistency: `update-docs/SKILL.md:105` names a four-label set that differs from CLAUDE.md's five.

title: Memory line budget mirroring the CLAUDE.md precedent
tier: cheap_fold
rationale: The precedent is explicit at `update-docs/SKILL.md:76-78` ("over budget means cutting, not reformatting"). Reusing the MECHANISM bounds the file before it needs curation, which is the deferred piece. Folded as a mechanism; the NUMBER is gated separately because it is a judgment call, not a default.

title: Seed memory with entries the repo has already earned
tier: cheap_fold
rationale: A memory that ships empty is a schema nobody fills — the exact failure the request names when deferring curation. Splits the difference between ambitious's 4-6 and the minimalist's 0-1: 2-4 entries, each traceable to a repo artifact or a probe run, never invented. The minimalist's warning is the binding constraint — an invented gotcha is worse than an empty file because it reads as authoritative in a repo whose premise is that docs are authoritative.

title: Ban diff hunks in the handoff and cap its length
tier: cheap_fold
rationale: The request's core complaint is that file-by-file narration reconstitutes the detail isolation was meant to avoid (FEATURE_REQUEST.md:36-37). A grep for `^@@`/`^+++`/`^---` plus a line cap makes that objectively checkable. Two assertions.

title: Spec-triage (dry-run) mode
tier: cheap_fold
rationale: One paragraph plus a documented invocation phrase buys a pre-flight: the agent reads the plan, reports gaps against its invariant set, and builds nothing. Makes a bad plan cheap to discover and — usefully for a feature whose premise is unproven — gives the main thread a reason to use the agent before trusting it with writes.

title: Track-agnostic by construction
tier: cheap_fold
rationale: `/implement-plan` already serves both tracks, auto-detecting from the artifact path (`implement-plan/SKILL.md:49-53`). A handoff contract assuming "feature" needs reworking the first time a bug is handed to it. A `track` field costs one line now.

title: Separable extraction vs dbt rulebook sections
tier: cheap_fold
rationale: Open question 9 asks whether one agent is the right granularity. The acceptance panel already models these as two distinct specialists (`acceptance_panel.js:197-198`), which is evidence the split is real. Structuring the invariant set as two self-contained sections makes a later split a copy rather than a rewrite, without deciding it against zero evidence.

title: Make CLAUDE.md's 200-line budget mechanical
tier: cheap_fold
rationale: Raised by the repo-fit scoper. The memory-budget guard is the same assertion; pointing it at `CLAUDE.md` too costs about three lines and converts `update-docs/SKILL.md:76-78`'s human-run one-liner into a CI failure. Measured at 122/200, so it lands green and stays honest.

title: Mechanical memory-vs-docs routing guard
tier: gated
rationale: Attractive — it would mechanize the routing rule that otherwise depends on the agent's discipline plus a human's eye at `/commit`. But both the repo-fit and ambitious scopers surfaced the brittleness: a keyword guard on seasons/endpoints/rate-limits/the 2013-14 boundary will false-positive on a legitimate ergonomics entry that names an endpoint — and "leaguegamelog returns a DataFrame, not JSON" is simultaneously the canonical GOOD memory entry and exactly what the guard would flag. Gated with a recommendation to take it as a warning-shaped check or a curated denylist, never a hard CI gate.

title: Run each drill more than once
tier: gated
rationale: Genuinely correct — agent behavior is nondeterministic and a single green run is one observation, not a property. Gated rather than folded because it multiplies the most expensive part of the build. If the user declines, the acceptance ledger must label the evidence as a single observation rather than a proof; that honesty requirement is not optional either way.

title: A reusable snapshot + tree-integrity script under ops/
tier: gated
rationale: Today the snapshot protocol exists only as prose inside `implement-plan/SKILL.md:120-125`, re-typed by whoever remembers, and `ops/` is already described as "repo governance as code". Turning scar tissue into a tool is the right long-run move. Gated because it is net-new executable tooling in a change whose reviewability depends on staying small, and because the prose protocol is sufficient for two proving runs.

title: Teach the acceptance panel about .claude/agents/
tier: gated
rationale: The gap is verified and real: `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, and the bucket lists at `implement-plan/SKILL.md:129-131` and `update-docs/SKILL.md:47-48` name `.claude/skills/` only — so the first future change to an agent definition draws only the core reviewers with no specialist lens. Every clause of the `skill-quality` mandate (`acceptance_panel.js:199`) applies verbatim to an agent definition. Gated, not folded, because the request explicitly fences `/implement-plan` (FEATURE_REQUEST.md:86-88) and because `acceptance_panel.js` is covered by two `.mjs` guards CI does not run — editing it without running both by hand is an easy silent regression.

title: Extract one canonical invariant file that CLAUDE.md, the agent definition, and both panel scripts cite
tier: gated
rationale: The strongest long-run answer to the drift problem: the Data Layer rules exist at `CLAUDE.md:86-103`, `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112` with no check that they agree, and this feature adds a fourth. A single cited source kills the surface permanently instead of guarding one edge. Gated because it touches three tooling surfaces in a change whose point is a fourth, and because it hollows out `CLAUDE.md` — the onboarding map a human reads first, where the rules being inline is a feature rather than duplication.

title: Return contract as a machine-checkable StructuredOutput schema rather than prose sections
tier: drop
rationale: Dropped on the minimalist's grounded objection, which is stronger than the case for it. This repo already knows what schema-forcing costs: `scope_panel.js:27` records that structured agents intermittently degenerate into placeholders, and the entire `ANTISTUB_RETRY`/`runChecked`/`safeAgent` apparatus exists to survive it. Building anti-stub machinery for one agent that has never returned once is premature. The enforcement goal is met a cheaper way — the handoff FILE's sections and hunk-freeness are linted by pytest — so this is dropped rather than deferred.

title: Split into separate extraction and dbt-modeling agents
tier: drop
rationale: Dropped, not gated: the request itself defers it (FEATURE_REQUEST.md:97, 197-199) and its reasoning is correct — splitting later is cheap, and designing two rulebooks against zero proving runs is speculation compounding speculation. Structural readiness for a later split is captured instead as a cheap fold (separable rulebook sections), so nothing is lost by dropping the split itself.

title: A /update-docs memory-coherence check
tier: drop
rationale: Dropped because the request explicitly fences it (FEATURE_REQUEST.md:88-90) and its stated reason holds: pruning criteria designed against zero entries produce a schema nobody fills. Folding it in silently would be exactly the laundered greed the pipeline forbids, and gating it would present the user with a decision the request already made. The `docs-delta` promotion queue covers the drift risk in the meantime.

title: Feed the handoff into stage 4, then wire the agent as its build step
tier: drop
rationale: Both halves are explicitly out of scope (FEATURE_REQUEST.md:86-88, 100-103). Dropped rather than gated — but the sequencing is worth naming so it is not rediscovered: passing the handoff into the acceptance panel's context is a much smaller step than making the agent stage 4's builder, and it partially restores the inverted asymmetry open question 4 identifies (the reviewer now has less context than the author). That belongs in a follow-up request.
~~~

### gated_decisions

~~~
question: HEADLINE — what is the proving run's target, concretely? The request proposes `box-score-foundation` (FEATURE_REQUEST.md:124-126); this scope reverses that, which is the minimalist's reshape and the one place the scope overrides the request. "A small task" is not a target. Options: (a) a scratch dbt project under gitignored `var/` built against a committed fixture — maximum containment, minimum realism, output discarded; (b) a small, genuinely useful, non-dataset repo task — real value and a real diff to review, but it consumes work that might belong elsewhere; (c) block acceptance until `box-score-foundation` reaches `planned` and carve a non-dataset slice from it (its config / path-resolution module) — most realistic, but couples this feature's acceptance to another feature's schedule and pre-empts scope belonging to it.
recommendation: Take (a) for the OMISSION DRILL and (b) for the FAITHFUL RUN. The omission drill needs a silver-model-shaped target to be meaningful and its output should be discarded, so a scratch project under `var/` is exactly right — and it keeps an untested builder out of `transform/models/`, which `transform/models/silver/README.md:5-7` reserves for fully-scoped work. The faithful run should produce something the repo actually keeps, so the evidence is a real diff a human reviews through `/commit` rather than a discarded toy. Reject (c): coupling acceptance to `box-score-foundation` (verified `intake`, no scope, no plan) inherits an unscoped dependency and points the repo's first unproven write-capable subagent at the least reversible work in it. NOTE the honest dissent this carries: the minimalist's fit verdict was `reshape` on TIMING — the problem this solves has not happened yet (FEATURE_REQUEST.md:16; measured: zero pipeline code, zero models, `/implement-plan` never run). The scope is called clean because the reshape is fully absorbed, but if you would rather wait until a real stage-4 run has actually strained a context, that is defensible and this is the decision point for it.
related: ["fit verdict","premise risk","the omission drill"]

question: Does the agent get Bash, and with what allowlist — and WHERE is that allowlist declared? All three scopers converged on "yes, restricted", but the mechanism is unknown: there is no `.claude/settings.json` in this repo (verified against `git ls-files`), so if tool posture is declared there rather than in the agent's frontmatter, this request introduces a config surface the CLAUDE.md project map does not currently mention.
recommendation: Yes, with a restricted allowlist — but only AFTER the harness probe confirms where it can be declared. Denying Bash outright would make this the only actor in the repo that cannot verify its own work, the standard every reviewer here is held to (`acceptance_panel.js:161-163` explicitly makes reviewers verification-capable so they RUN checks rather than assert them), and it would hand every verification back to the main thread, reconstituting the detail the isolation exists to avoid. Mirror the structure of `READONLY` at `acceptance_panel.js:163` but inverted for a builder: permit `uv run pytest` / `ruff` / `mypy` / `dbt build --target ci` (in-memory DuckDB, touches no file) plus read-only git (`diff`/`status`/`log`); exclude every tree- or history-mutating git subcommand by name; forbid live-API calls and any billable target. If the probe shows the posture can only be expressed as prose in the prompt, say so plainly in ADR 0007 — an unenforceable allowlist is still worth stating, but it must not be described as a guard.
related: ["the scar","harness probe","write-guard package"]

question: What is the memory file's line cap? `update-docs/SKILL.md:76-78` sets a 200-line precedent for `CLAUDE.md` (measured today at 122), available to reuse or consciously reject.
recommendation: Go tighter than 200 — 120 is the recommendation — and enforce it in pytest with the cap named in the assertion message. Rationale: memory is read alongside the definition on every implementation task, so what matters is the PAIR's combined size, not the file's alone; and its value density is lower than the project map's, since it accumulates by append rather than by editorial decision. A tighter cap forces the curation conversation to happen sooner, which is exactly what a deliberately deferred curation protocol needs. Whatever number you pick should be recorded in ADR 0007 rather than being a constant somebody chose in a test file.
related: ["curation protocol deferral","memory budget guard"]

question: How strict is the invariant-drift guard — verbatim-identical text between the definition and `CLAUDE.md`, or presence of each invariant's key phrase?
recommendation: Phrase-presence, not verbatim. Verbatim reddens CI on any wording change to `CLAUDE.md`, which is friction on the repo's most-edited governance file and will train people to route around the guard — and it fights the design decision to restate COMPRESSED in the `scope_panel.js:124` shape rather than as a second full copy. Phrase-presence catches the failure that actually matters (a rule silently deleted from one side while the other still carries it) at a fraction of the friction. Pair it with a negative control and a failure message naming the missing invariant and both file paths, so a red build tells you what to do rather than merely that something disagrees.
related: ["fourth restatement risk","drift guard friction"]

question: Should the invariants be EXTRACTED to one canonical file that `CLAUDE.md`, the agent definition, `scope_panel.js`, `plan_panel.js`, and `implement-plan/SKILL.md` all cite — rather than guarding one edge of a four-way duplication?
recommendation: Not now; record it as the deferred structural fix. Extraction is cleaner in principle and is the only thing that kills the drift surface permanently, but it touches three tooling surfaces in a change whose entire point is a fourth, and it hollows out `CLAUDE.md` — the onboarding map a human reads first, where the rules being inline is a feature rather than duplication. Revisit once the drift guard has actually caught something, which is the evidence that would justify the bigger refactor. If you want it now, it should be its own feature request rather than folded in here.
related: ["invariant handling","canonical invariant file enhancement"]

question: Should the panels be taught that `.claude/agents/` exists — `AREA_TO_SPEC` at `acceptance_panel.js:202-206`, plus the bucket lists at `implement-plan/SKILL.md:129-131` and `update-docs/SKILL.md:47-48`? Verified gap: no `agents` key anywhere, so the first future change to an agent definition draws only the core reviewers with no specialist lens, and `/update-docs` will not bucket it as tooling.
recommendation: Take the DOC half now, defer the JS half. Adding `.claude/agents/` alongside `.claude/skills/` in the two bucket lists changes no build step — only which reviewer gets spawned and which doc checks are treated as load-bearing — and it is a two-word edit. The JS half edits `acceptance_panel.js`, covered by `merge_fallback_guard.mjs` and `verify_batching_guard.mjs`, neither of which CI runs (verified: no Node step in `ci.yml`), so editing it means remembering to run both by hand — an easy silent regression in a change that should stay reviewable. Both halves sit near the request's fence around `/implement-plan` (FEATURE_REQUEST.md:86-88), which is why neither was folded silently. If you read that fence as covering the bucket lists too, defer both and record the gap in ADR 0007's Consequences.
related: ["no specialist reviewer risk","AREA_TO_SPEC gap"]

question: How many proving-run repetitions before the design is called proven — one per drill, or two to three?
recommendation: Two per drill if affordable; one is acceptable IF the acceptance ledger and ADR 0007 both label the result a single observation rather than a proof. Agent behavior is nondeterministic, so one green run is one observation of a distribution, and this repo's own epistemic-labeling convention (`CLAUDE.md:76-79`) makes overclaiming here a convention violation rather than merely optimistic. A split result across two runs of the omission drill is the single most valuable outcome available — it would tell you the invariant set is probabilistic rather than load-bearing, which is exactly what is worth knowing before `box-score-foundation`.
related: ["proving-run evidence weakness","omission drill"]

question: Should there be a mechanical memory-vs-docs routing guard — a test that fails when the memory file mentions seasons, endpoints, rate limits, or the 2013-14 boundary?
recommendation: Yes, but as a WARNING-shaped check or a curated denylist, never a hard CI gate. The routing rule otherwise depends entirely on the agent's discipline plus a human's eye at `/commit`, and mechanizing it closes the drift route the request names at FEATURE_REQUEST.md:174-180. But the brittleness is real and two scopers flagged it: the canonical GOOD memory entry the request uses as its own example — a client returning a DataFrame rather than JSON with different column casing — is one word away from naming an endpoint, and a hard gate would reject it. A denylist of specific data-fact vocabulary (`2013-14`, `season`, `rate limit`, `structurally absent`) that prints a warning and requires a human ack at `/commit` gets most of the value with none of the train-people-to-route-around effect.
related: ["memory routes around the doc gate","curation deferral"]

question: Does ADR 0007 land with the change, or after the proving run?
recommendation: Write it AFTER the proving runs but land it in the SAME PR, status `accepted`. `docs/decisions/README.md:29-32` makes accepted ADRs immutable — you cannot amend the Consequences section later without writing a superseding ADR — so it should be written once the proving runs have shown what the guards actually did, with the Consequences section stating plainly that the replacement guard is detection rather than prevention and citing the recorded tree-integrity evidence. `docs/decisions/README.md:34-35` demands the consequences section be uncomfortable to write; an ADR drafted before the evidence exists will not be.
related: ["ADR 0007","instructions are not enforcement"]

question: Should the write allowlist include the agent's own definition file, or memory only?
recommendation: Memory only; the definition stays human-maintained. That is how the request frames the pair (FEATURE_REQUEST.md:54-58, 65 — "Human, deliberately"), and letting the agent edit its own definition is a self-modification path nobody asked for that would also let it edit away its own guardrails between the pre- and post-run snapshots. The guardrail-clause presence test would catch that after the fact, but designing a hole and then testing for it is worse than not having the hole.
related: ["write-guard package","guardrail-clause presence test"]
~~~

## Findings

### F1 (blocker)

~~~
title: The write allowlist — the whole replacement for "it can't write" — is unbounded, and leaves the guards themselves writable
severity: blocker
confidence: high
category: non-goals / risk
adversary: fit-ac

location:
Merged scope: core item "THE WRITE-GUARD PACKAGE" and non_goals[9] ("The write allowlist covers the memory file and the task's target paths"); repo evidence: CLAUDE.md:122-125, ops/branch-protection.json:4, .github/workflows/ci.yml:26-27

problem:
The scope's central safety claim is a "declared write allowlist". But it defines that allowlist as "the memory file and the task's target paths" — and "the task's target paths" is whatever the spec names, so it is a restatement of "the spec decides", not a bound. Nothing prevents the agent from writing .github/workflows/ci.yml, ops/branch-protection.json, tests/test_repo_structure.py, .gitignore, or .claude/agents/ itself. Every mechanical guard the scope leans on lives in exactly those paths. CLAUDE.md:122-125 already records that ci.yml job display names and ops/branch-protection.json:4 are coupled such that breaking them produces NO error — "PRs wait forever for a check that never reports, with no error saying why". An agent that edits a guard test and then reports a green suite is the 2026 version of the recorded scar at implement-plan/SKILL.md:123-125 (a vacuous selftest passing green), and the post-run tree-integrity comparison would classify the write as inside-allowlist if the spec happened to name the path. Non-goal 10 correctly forbids self-editing of the definition but says nothing about the guards, which is the larger hole.

proposed_fix:
Replace allowlist-only with allowlist AND a repo-level deny set, stated in the definition and asserted by a guard test. Deny by path regardless of what a spec says: .github/**, ops/**, .claude/** (definition and guard alike), .gitignore, .gitattributes, pyproject.toml, uv.lock, tests/** — with the single carve-out that the memory file is writable. Add an acceptance criterion: post-run `git status --porcelain` shows zero paths matching the deny set, checked by a committed pytest helper rather than by reading. State in ADR 0007 that a builder permitted to edit tests/ and .github/ can invalidate its own evidence, and that the deny set — not the allowlist — is what makes the tree-integrity check meaningful.
~~~

### F2 (blocker)

~~~
title: The only behavior-testing acceptance criterion is unreproducible because its artifacts land in gitignored var/
severity: blocker
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[10] (omission drill) + gated_decisions[0] recommendation ("Take (a) [a scratch dbt project under gitignored var/] for the OMISSION DRILL") + non_goals[10]; repo: .gitignore line 16 (var/), tests/test_doc_links.py:31-48 (var in EXCLUDED_PARTS), .github/workflows/ci.yml:73-76

problem:
The scope itself argues, correctly, that AC11 is "the only criterion that tests FEATURE_REQUEST.md:46-47 rather than testing that files exist". Its verification method is "determined by grep over the drill artifacts and quoted verbatim". But gated decision 1 recommends running the drill into a scratch dbt project under var/, which is gitignored. So the produced model is never committed; `dbt build --target ci` never compiles it; test_doc_links skips var; the stage-4 acceptance panel, whose defining rigor is re-running checks (implement-plan/SKILL.md:32-35), cannot re-run the grep because the target is gone; and a cold agent cannot reproduce it. What survives is a verbatim quotation inside reviews/proving-run-b.md — a human-transcribed claim. requests/feature-requests/README.md:47-49 defines testable as "a cold agent can run one command and get a pass or fail — not when a human can eyeball a number and nod". AC11 as scoped fails that definition, and it is the criterion the feature's whole value rests on.

proposed_fix:
Make the drill evidence committed and re-runnable. Either (a) run the drill into a committed scratch location — e.g. tests/fixtures/agent-drills/<run>/ — small, tracked, outside transform/models/ so it never enters the dbt build, with AC11 rewritten as `uv run pytest tests/test_agent_drills.py -q` asserting the produced schema.yml either carries a uniqueness test or the sibling handoff contains a spec-gap flag; or (b) if the drill must run in var/, require the drill output (model SQL, schema.yml, handoff) to be copied verbatim into requests/feature-requests/data-engineer-agent/reviews/drill-b-artifacts/ as committed files at PR time, and rewrite AC11 to grep those committed copies. Either way the criterion must name a single command returning pass/fail against tracked files.
~~~

### F3 (blocker)

~~~
title: Acceptance criterion 1 contradicts the scope's own core deliverables and asserts an unverified frontmatter schema
severity: blocker
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[0] ("contains exactly one *.md agent definition, and that file opens with YAML frontmatter parsing to a non-empty name and description") vs tiered_scope.core items 2, 4 and 11 (.claude/agents/<agent>.md, .claude/agents/<agent>-memory.md, .claude/agents/README.md)

problem:
Two defects in one criterion. (1) The scope's core ships three Markdown files into .claude/agents/: the definition, the memory file, and a directory README. A guard asserting the directory "contains exactly one *.md" fails on the scope's own deliverable — and a guard cannot distinguish "agent definition" from "README" or "memory" without a naming or frontmatter discriminator, which the scope never supplies, so the criterion is not mechanically implementable as written. (2) The frontmatter assertion (name + description) is the SKILL.md shape, and the same scope warns in core item 2 that "the eight committed SKILL.md files use name + a trigger-rich description; that is the SKILL format and may not be the agent format". AC1 therefore hardcodes the exact assumption the harness probe (core item 1, AC9) exists to test. If the probe returns a different schema, AC1 either fails on a correct file or passes on a wrongly-formatted one — precisely the dead-artifact failure listed as risk 2.

proposed_fix:
Rewrite as: ".claude/agents/ exists and contains exactly one file whose frontmatter carries the agent-type keys recorded by reviews/harness-probe.md; the memory file and README are identified by fixed names (<agent>-memory.md, README.md) and excluded from the definition count." Make the required frontmatter keys a test constant set from the probe's recorded answer, and add an explicit sequencing note that AC1 cannot be authored until AC9 is satisfied. Add a companion assertion that the definition's frontmatter matches the probe's schema verbatim, so the guard cannot go green on a file the harness would not load.
~~~

### F4 (major)

~~~
title: The fit verdict launders a TIMING reshape into "clean"; the build-now-or-later question is buried in a note
severity: major
confidence: high
category: fit / framing
adversary: fit-ac

location:
Merged scope: fit_verdict.rationale ("Both are adopted below, which is why the verdict lands clean rather than reshape") and gated_decisions[0], where the timing dissent appears only as a trailing "NOTE the honest dissent this carries"; .claude/skills/scope-feature/SKILL.md:35-36

problem:
The scope reports the third scoper's verdict as reshape because "the FORM fits and the TIMING does not", then declares the reshape "fully satisfiable inside the scope" via two adoptions: decouple the proving run, add a mechanical guard. Neither addresses timing. Decoupling changes WHERE the agent is first pointed; it does not change that, measured, src/nba_platform/ holds one __init__.py, transform/models/ holds zero .sql files, history is three commits, and /implement-plan has never run — so the context-exhaustion problem is inferred, never observed (FEATURE_REQUEST.md:16; the scope's own risk 1 restates it). scope-feature/SKILL.md:35-36 defines greedy-but-gated as "expensive/scope-growing ideas are tiered and deferred for your call, never silently folded". Folding the largest judgment call — build now, or after the first real stage-4 run strains a context — into a trailing NOTE inside a different gated decision (whose headline question is the proving target) is that silent fold. A user answering "what is the proving target?" may never register that they were also answering "should this exist yet?".

proposed_fix:
Either set fit_verdict to `reshape` with timing as the reshape, or keep `clean` and promote timing to its own standalone gated decision, listed FIRST: "Build now, or defer until one real /implement-plan run has actually strained a context? For deferring: the premise is inferred not measured (FEATURE_REQUEST.md:16; zero pipeline code, zero models, three commits). For building now: box-score-foundation is the next slice and is large; building the tool after the strain means building it under pressure. Recommendation: <pick one>." Do not attach it to the proving-target question.
~~~

### F5 (major)

~~~
title: The invariant-drift guard as specified is one-directional and cannot do what the criterion claims
severity: major
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[2] ("for each invariant the definition declares it carries, the test asserts a corresponding rule is present in CLAUDE.md, and fails if either side is edited alone")

problem:
The described algorithm iterates over the invariants the DEFINITION declares. Deleting a rule from CLAUDE.md while the definition still names it makes the lookup fail — red, correct. But deleting an invariant from the DEFINITION removes it from the iteration set entirely, so the loop simply has one fewer item and the test goes green. The guard is blind to exactly the failure AC2 covers for only two hardcoded clauses (read-only git, never-commit). The claim that it "fails if either side is edited alone" is false as specified. Making it bidirectional requires a fixed canonical list of invariants as a constant inside the test — meaning the change ships a FIFTH statement of the same rules, in the very artifact positioned as what makes duplication safe. That is a real, unacknowledged design consequence.

proposed_fix:
Restate as: "a module-level REQUIRED_INVARIANTS tuple in the guard test names each invariant by a short phrase; the test asserts each phrase resolves in BOTH CLAUDE.md and the agent definition, failing with a message naming which side is missing it." Acknowledge in the scope and in ADR 0007's Consequences that the test constant is itself an additional statement of the rules, and say why that is acceptable — a test constant is executable and reddens on drift, unlike the prose copies. Ship the negative control against both directions (mutate CLAUDE.md; mutate the definition), not just one.
~~~

### F6 (major)

~~~
title: The invariant restatement surface is roughly nine sites, not the three the scope counted
severity: major
confidence: high
category: completeness
adversary: fit-ac

location:
Merged scope: risks[3] and tiered_scope.core item 3 ("the three existing restatements (scope_panel.js:124, plan_panel.js:146, implement-plan/SKILL.md:100-112)"); verified additional sites: plan_panel.js:165, plan_panel.js:228, plan_panel.js:265, acceptance_panel.js:174, acceptance_panel.js:197, acceptance_panel.js:199

problem:
The scope frames the duplication as "a fourth restatement" of three, and argues one drift guard on one edge is proportionate. I grepped the panel scripts. The CLAUDE.md conventions are additionally restated at plan_panel.js:165 (PLANNER 3's non-data pivot: resolve-by-name, immutable landing zone, agents-never-commit, read-only-git subagents, user-run-for-billable); plan_panel.js:228 (the §8 CONVENTIONS mandate, the same list); plan_panel.js:265 (ADVERSARY 2 clause 4); acceptance_panel.js:174 (the SHARED grounding block, the full data-layer list); acceptance_panel.js:197 (the data-contract specialist's grain/bronze/merge/era clauses); acceptance_panel.js:199 (skill-quality clause 4). That is ~9 sites including CLAUDE.md, none drift-checked. This changes two conclusions: the "restate compressed plus one guard" synthesis covers about a ninth of the surface rather than a quarter, and gated decision 5 (extract a canonical invariant file) is a much stronger candidate than "not now" implies. It also means stage 3 will bake "read-only-git subagents" into this feature's own IMPLEMENTATION_PLAN from plan_panel.js:228 §8 — the exact phrase the scope is simultaneously clarifying at CLAUDE.md:73-75.

proposed_fix:
Correct the count in risks and core item 3, listing the six additional sites with line numbers. Re-weigh gated decision 5 against the real number and either raise its recommendation or state explicitly that a nine-site drift surface is knowingly left uncovered and why. At minimum add to gated decision 5's framing that stage 3 will emit "read-only-git subagents" into this feature's own plan via plan_panel.js:228, so the CLAUDE.md:73-75 clarification must be settled before the plan stage runs or the plan bakes in the pre-clarification wording.
~~~

### F7 (major)

~~~
title: Three of the request's four observable signals have no acceptance criterion, and one is actively substituted away
severity: major
confidence: high
category: acceptance / framing
adversary: fit-ac

location:
Merged scope: acceptance_criteria (16 items) vs FEATURE_REQUEST.md:41-47 (four observable signals); tiered_scope.cheap_folds "SEED THE MEMORY WITH 2-4 ENTRIES THE REPO HAS ALREADY EARNED"

problem:
Mapping the 16 criteria onto the request's four signals: signal 4 ("silver declares its grain and proves it holds even when the spec forgets to restate it", FEATURE_REQUEST.md:46-47) is covered by AC11, and the scope says so. Signal 1 ("a feature gets built without the main thread reading every edit, and the main thread can still answer what was built / verified / assumed / still open") is covered only by proxies — handoff sections present, no diff hunks, under a cap — which test the SHAPE of the report, not that a feature was built or context saved; non-goal 14 concedes the benefit is deferred entirely. Signal 2 ("the agent hits a repo-specific trap, records it, and a later session doesn't hit it again") has no criterion, and the cheap fold seeding memory with entries the repo already earned actively substitutes pre-known content for the discover-and-record loop the signal is about. Signal 3 ("knowledge survives a session restart") has no criterion. One of four is tested. Deferring signals is legitimate; presenting 16 criteria as if the request's outcome were covered is not.

proposed_fix:
Add a short mapping table: each observable signal -> the criterion that tests it, or an explicit "deferred, and why". For signal 2, add a cheap criterion that tests the loop: run the faithful drill twice with the second spec deliberately re-entering the same trap, PASS iff run B's handoff cites the memory entry written in run A (greppable). For signal 3, one line suffices: a fresh spawn with no conversation history cites at least one seeded memory entry in its handoff. For signal 1, either mark it deferred in the goals list as well as in non-goals, or add the context-economy proxy from F14.
~~~

### F8 (major)

~~~
title: "RECORDED-EVIDENCE" is an invented third acceptance category the pipeline contract does not define
severity: major
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[8] through [12], labelled RECORDED-EVIDENCE; requests/feature-requests/README.md:45-59; acceptance_panel.js:190

problem:
requests/feature-requests/README.md:47-59 defines exactly two kinds of criterion: testable ("a cold agent can run one command and get a pass or fail") and user-run ("criteria that can only be proven by a human running something ... must be marked user-run so the acceptance panel doesn't claim them"). The scope introduces a third covering five criteria including both proving runs and the tree-integrity check. Each bundles a mechanically greppable half (does reviews/harness-probe.md exist; does it contain the string `verified`; does reviews/proving-run-a.md carry all seven headings; does grep for ^@@ return nothing) with a human-judgment half ("the definition's design visibly matches the answer"; "each row in the verified table citing a concrete command and its actual output" — a lint cannot distinguish an actual output from a fabricated one; "the comparison shows nothing that existed before was reverted"). The stage-4 auditor mandate (acceptance_panel.js:190) resolves each criterion to met/partial/unmet/not-verifiable and is instructed never to guess met. Handed a hybrid it will either over-claim the judgment half or mark the whole thing not-verifiable — and the README's stated reason for the user-run marking is exactly "so the acceptance panel doesn't claim them".

proposed_fix:
Split each into two, using only the contract's two categories. Mechanical half: an exact command and expected result (e.g. "`uv run pytest tests/test_handoff_schema.py -q` is green over reviews/proving-run-a.md and reviews/proving-run-b.md; `grep -c '^@@' reviews/proving-run-*.md` returns 0"). User-run half, explicitly marked: "the user reads reviews/harness-probe.md and confirms the definition's design matches what the probe found"; "the user reads the pre/post tree-state pair and confirms nothing was reverted". Drop the RECORDED-EVIDENCE label.
~~~

### F9 (major)

~~~
title: The "no agent-type parameter" evidence conflates the panel's Workflow agent() primitive with Claude Code's .claude/agents/ mechanism
severity: major
confidence: medium
category: fit / risk
adversary: fit-ac

location:
Merged scope: goals[1], above_and_beyond[0], risks[1] and gated_decisions[1], all resting on "scope_panel.js:174 spawns via agent(prompt, {label, phase, schema, effort}) with no agent-type parameter"; actual code: scope_panel.js:174 calls runChecked(...), and the underlying agent(prompt, opts) call is at scope_panel.js:96

problem:
Two problems, one clerical and one substantive. Clerical: line 174 is a runChecked(...) call; agent(prompt, opts) is invoked at line 96 inside safeAgent. Substantive: the scope uses the absence of an agent-type argument in the panel scripts' agent() primitive as evidence about whether .claude/agents/*.md is loadable at all, concluding "there is no committed place to declare per-agent tool permissions today". Those are different spawn surfaces — the Workflow harness agent() the panels use, and the main thread's subagent mechanism .claude/agents/ conventionally serves. Absence in the former says nothing about the latter. This matters beyond pedantry: if the panel agent() genuinely cannot select a .claude/agents/ definition, then the deferred follow-up the scope repeatedly leans on — wiring the agent into /implement-plan as its build step (non_goals[0], drop item 4, non_goals[13]) — may be impossible without harness changes rather than merely out of scope. That changes the feature's value case and belongs in the fit verdict, not a footnote.

proposed_fix:
Correct the citations to scope_panel.js:96 for the agent() call, noting :174 is the runChecked wrapper. Split goal 2 and AC9 into two explicitly separate probe questions: (a) can the MAIN THREAD spawn a .claude/agents/-defined subagent, with what frontmatter and what tool-permission surface; (b) can a Workflow panel script's agent() select an agent type at all. Record both with epistemic labels. If (b) is no, say so in the fit verdict and ADR 0007's Consequences, because it converts the deferred stage-4 wiring from "a later request" into "a later request that may require harness capability this repo does not control".
~~~

### F10 (major)

~~~
title: No criterion exercises two of the three branches of the spec-gap escalation policy the scope calls testable
severity: major
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: tiered_scope.core item 7 ("THE THREE-WAY SPEC-GAP ESCALATION POLICY ... All three are observable in the handoff, so the policy is testable rather than a default") and above_and_beyond[4]; the acceptance_criteria list

problem:
The scope defines three branches: a spec that CONTRADICTS an invariant stops the agent with a spec-gap report; a spec SILENT on an invariant is built to the invariant and flagged; an AMBIGUOUS requirement is built at the smaller interpretation and flagged. It asserts the policy is testable because all three outcomes are observable in the handoff. But the criteria contain exactly one drill exercising exactly one branch — AC11 tests SILENT. Nothing tests CONTRADICTS, the branch with real downside if it fails (a spec saying "append to the fact table" against the merge-on-key invariant at CLAUDE.md:98-99 would ship a silently wrong table), and nothing tests AMBIGUOUS. "Observable in the handoff" is a property of the artifact format, not evidence the behavior occurs — the same shape as the scope's own criticism of every other criterion.

proposed_fix:
Add drill C, cheap because it produces almost nothing: hand the agent a spec that explicitly instructs an append-only fact load, contradicting CLAUDE.md:98-99. PASS iff the handoff's could-not-do or spec-gap section names the contradiction and no model was written; FAIL if it built the append-only load, with or without a flag. Greppable, and the artifact is a handoff file rather than a model. Optionally fold AMBIGUOUS into drill A by leaving one requirement in the faithful spec deliberately two-sided and asserting the handoff flags it — zero extra runs.
~~~

### F11 (minor)

~~~
title: The measured CLAUDE.md line count is a non-blank count; real headroom is ~60 lines, and the proposed pytest guard would redefine "line"
severity: minor
confidence: high
category: completeness
adversary: fit-ac

location:
Merged scope: acceptance_criteria[6] ("Measured today: 122, so 78 lines of headroom"), grounding_pointers CLAUDE.md entry, cheap_folds "MAKE CLAUDE.md's 200-LINE BUDGET MECHANICAL"; source of the command: update-docs/SKILL.md:76-78

problem:
I ran it: `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns 122, but `(Get-Content CLAUDE.md).Count` returns 140 and there are 18 blank lines — Measure-Object -Line does not count empty strings. CLAUDE.md is physically 140 lines, so the budget check documented at update-docs/SKILL.md:76-78 has been undercounting by the blank-line count since it was written. Real headroom against 200 is ~60, not 78. Two consequences here. (1) The headroom figure used to justify "fits trivially in the 78 lines of measured budget headroom" (above_and_beyond[7]) is overstated by ~18. (2) The cheap fold proposes making the budget mechanical using "the same assertion" as the memory-budget guard — a pytest guard would naturally use len(text.splitlines()) = 140, disagreeing with the documented PowerShell command by 18. Shipping both leaves two definitions of "line" for one budget, in a change whose stated purpose is closing that class of drift. The same ambiguity infects AC4's memory cap, which says "line count" without pinning a method.

proposed_fix:
Correct the measurement in AC7 and above_and_beyond[7] to "140 physical lines; Measure-Object -Line reports 122 because it excludes blank lines". Pin one definition — recommend physical lines via len(path.read_text().splitlines()) — state it in the guard's assertion message, apply it to both CLAUDE.md and the memory cap, and add a one-line correction to update-docs/SKILL.md:76-78 so prose and mechanical checks agree. Note the correction in ADR 0007's Consequences: the budget was never as loose as it read.
~~~

### F12 (minor)

~~~
title: AC7 contains an untestable clause ("reads so a reader can tell") inside a criterion marked MECHANICAL
severity: minor
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[6], final clause: "and the subagent bullet (CLAUDE.md:73-75) reads so a reader can tell that an agent editing a tracked file is not violating it"

problem:
The criterion is labelled MECHANICAL and its first two clauses are (line count; presence of a .claude/agents/ entry in the project map). The third asks whether prose "reads so a reader can tell" something — pure human judgment bundled into a mechanically-labelled criterion. No command returns pass/fail for it, and the acceptance panel will either assert it met on inspection (which requests/feature-requests/README.md:56-59 exists to prevent) or drag the whole criterion to not-verifiable, losing the two clauses that were genuinely checkable.

proposed_fix:
Split it. Mechanical: "CLAUDE.md contains the substring `.claude/agents/` inside the project-map fenced block, and the subagent bullet contains a fixed clause distinguishing git operations from file edits — assert presence of the request's own wording, e.g. `editing a tracked file is not a git operation` (FEATURE_REQUEST.md:138-140)." That is greppable and pins the intended meaning. Move any remaining prose-quality judgment to the user-run bucket, or drop it — /update-docs's editor's-pen step (update-docs/SKILL.md:137-141) already owns it.
~~~

### F13 (minor)

~~~
title: AC13 asserts a hard grep gate that gated decision 8 explicitly recommends against
severity: minor
confidence: high
category: acceptance
adversary: fit-ac

location:
Merged scope: acceptance_criteria[12] ("the memory file contains zero such claims at PR time (grep-checkable against the memory file at review)") vs gated_decisions[7] ("as a WARNING-shaped check or a curated denylist, never a hard CI gate")

problem:
AC13 states as an acceptance condition that the memory file contains zero data/era/endpoint/availability/rate-limit claims, described as grep-checkable. Gated decision 8 recommends the routing guard be warning-shaped and explicitly not a hard gate, on the grounded argument that the canonical GOOD memory entry from the request itself (a client returning a DataFrame with different column casing, FEATURE_REQUEST.md:26-28) is one word from naming an endpoint. So the scope simultaneously asserts the criterion and declines to enforce it, and the two are read by different consumers — the acceptance panel takes AC13 literally. The boundary is also undefined enough that a reviewer cannot predict the verdict: one proposed seed ("sqlfluff errors on an empty model selection") names a CI behavior, another is the harness-probe result.

proposed_fix:
Reconcile by making AC13 the weaker, honest thing it is: "a routing-warning check runs over the memory file and prints any line matching the data-fact denylist; the PR description records the reviewer's acknowledgement of each hit, or the check reports none." Mark the acknowledgement half user-run. Move the "zero data claims" aspiration into the definition's routing rule, where it belongs as an instruction rather than a gate. State the denylist's exact terms in the scope so the boundary is predictable.
~~~

### F14 (minor)

~~~
title: The scope carries no measure of the context economy that is the feature's entire justification
severity: minor
confidence: medium
category: acceptance
adversary: fit-ac

location:
Merged scope: goals[0] ("spend its context on strategy rather than on file-by-file narration") and problem_restatement; acceptance_criteria contain a handoff line cap but no comparison to what was avoided

problem:
The feature exists because implementation detail crowds out strategic judgment. Every criterion measures artifact shape — sections present, no diff hunks, under a cap. None measures the thing the request wants: that reading the handoff is materially cheaper than reading the work. A 200-line handoff over a 40-line diff is a loss and would pass every criterion; a 60-line handoff over an 800-line diff is the win the request describes; nothing distinguishes them. CLAUDE.md:117-119 already treats cost as a first-class guardrail, and non-goal 14 already concedes the benefit is deferred — but a cheap number would at least establish direction on the two proving runs.

proposed_fix:
Add one mechanical criterion: each proving run's handoff records, in a fixed line, its own line count and the total changed-line count from `git diff HEAD --stat` for that run, plus the ratio; the handoff-schema lint asserts both numbers are present and parseable. Do not gate on a threshold at n=2 — gate only on the numbers being recorded — and state in ADR 0007 that this is the first data point toward whether the isolation pays for itself, and the number a follow-up request should be judged against.
~~~

### F15 (minor)

~~~
title: The epistemic-vocabulary drift is three-way, not two-way, and the seeding fold must pick among three
severity: minor
confidence: high
category: completeness
adversary: fit-ac

location:
Merged scope: cheap_folds "MEMORY ENTRIES CARRY THE REPO'S EPISTEMIC VOCABULARY" ("update-docs/SKILL.md:105 names a DIFFERENT four-label set"); verified sources: CLAUDE.md:76 (five labels), update-docs/SKILL.md:105 (four), docs/data-sources.md:5-8 (three)

problem:
The scope correctly spots that CLAUDE.md:76-79 names five labels (measured / verified / inferred / assumed / unconfirmed) while update-docs/SKILL.md:105 names four (measured / verified / documented / unconfirmed). It misses the third: docs/data-sources.md's own Epistemic status blockquote at lines 5-8 names only three — verified, documented, unconfirmed — with no `measured` at all. So the file whose labels /update-docs audits uses a vocabulary neither of the other two states. The memory entry format must pick one, and the scope presents it as a two-way choice.

proposed_fix:
Correct the fold to name all three sources with line numbers and make the pick explicit: recommend CLAUDE.md:76-79's five-label set for the memory file, since CLAUDE.md is the stated authority and the memory file is agent-facing rather than data-facing. Record the three-way drift as a separate small doc fix for /update-docs to reconcile, or spin it as its own request the way the scope already handles the fixtures-recorder drift.
~~~

### F16 (minor)

~~~
title: Non-goal 1 fences /implement-plan, but gated decision 6 recommends editing it now
severity: minor
confidence: high
category: scope-creep
adversary: fit-ac

location:
Merged scope: non_goals[0] ("NOT rewiring /implement-plan ... Stage 4 keeps building the way implement-plan/SKILL.md Step 3 describes") vs gated_decisions[5] ("Take the DOC half now" — editing the bucket lists at implement-plan/SKILL.md:129-131 and update-docs/SKILL.md:47-48); FEATURE_REQUEST.md:86-88

problem:
The request fences /implement-plan explicitly. Non-goal 1 restates the fence. Gated decision 6 then recommends editing implement-plan/SKILL.md:129-131 now, reasoning that a bucket-list edit changes no build step. The tension is disclosed inside gated decision 6, but the two statements are read by different consumers, and a reader of the non-goals alone would conclude the file is untouched. The stage-3 planner reads both and has to reconcile them.

proposed_fix:
Amend non-goal 1 to say precisely what is fenced: "NOT changing /implement-plan's BUILD step or its acceptance panel roster. A bucket-list line naming .claude/agents/ alongside .claude/skills/ at implement-plan/SKILL.md:129-131 is in scope only if gated decision 6 is disposed that way — see it." A one-clause edit removes the contradiction and keeps the disposition honest.
~~~

### F17 (nit)

~~~
title: The scope credits only the acceptance panel with a no-file-writes rule; in fact all three panels carry one
severity: nit
confidence: high
category: fit
adversary: fit-ac

location:
Merged scope: fit_verdict.rationale point 5 ("The absolute 'MUST NOT modify any file' at acceptance_panel.js:163 is scoped to the acceptance panel's REVIEWERS"); verified: scope_panel.js:132, plan_panel.js:131, acceptance_panel.js:163

problem:
All three panel scripts carry a READONLY constant forbidding file modification: plan_panel.js:131 ("modify NO file and run NO git command that changes the working tree"), scope_panel.js:132 (the clause I am operating under right now), and acceptance_panel.js:163. The scope characterises the prohibition as belonging to stage 4's reviewers, which understates the precedent this feature departs from — every subagent this repo has ever spawned, at every stage, has been write-forbidden by instruction. That strengthens rather than weakens the case for ADR 0007, and means the ADR's Context should cite three sites, not one.

proposed_fix:
Correct the rationale to cite all three (scope_panel.js:132, plan_panel.js:131, acceptance_panel.js:163) and reframe: the convention is not stage-4-specific, it is universal across the pipeline, and this feature is the first departure from it anywhere. Carry the three citations into ADR 0007's Context.
~~~

### F18 (nit)

~~~
title: Small citation and count inaccuracies that would mislead a cold planner
severity: nit
confidence: high
category: fit
adversary: fit-ac

location:
Merged scope: summary and grounding_pointers — the SPEC_DEFS line ref, the ANTISTUB_RETRY line ref, the .mjs guard count, and the projected Markdown-file count; plan_panel.js:149

problem:
Four verified inaccuracies, individually trivial but the stage-3 planner treats citations literally (plan_panel.js:149: "a cold implementer trusts them literally, so a wrong citation is worse than none"). (a) SPEC_DEFS opens at acceptance_panel.js:196, not 197 — the range ":197-201" starts one line inside the object, though the individual specialist refs (:197, :198, :199) are correct. (b) ANTISTUB_RETRY is defined at scope_panel.js:34, not within the cited ":95-115" (which correctly covers safeAgent/runChecked). (c) "five .mjs guards" — there are five .mjs files, but create-implementation-plan/tests/merge_failure_repro.mjs is a repro, not a guard; four are guards. (d) "30 tracked .md files today, rising to at least 33" — the change adds at minimum eight (definition, memory, agents README, ADR 0007, PROJECT_SCOPE, harness-probe, proving-run-a, proving-run-b), so the floor is ~38.

proposed_fix:
Correct (a) to acceptance_panel.js:196-201; (b) to scope_panel.js:34 for ANTISTUB_RETRY and :95-115 for the wrappers; (c) to "four guards plus one failure repro"; (d) to ~38. Separately add a one-line cheap fold: raise MIN_EXPECTED_FILES at tests/test_doc_links.py:53 from 20 toward the new real count, since its stated purpose (lines 50-51) is to catch an exclusion bug turning the check into a no-op, and a floor of 20 against 38 files no longer does that.
~~~

### F19 (nit)

~~~
title: The inline-code-paths convention is applied to memory but not to the handoff artifacts, which are equally link-checked
severity: nit
confidence: high
category: completeness
adversary: fit-ac

location:
Merged scope: cheap_folds "MEMORY PATHS AS INLINE CODE, NEVER [text](path) MARKDOWN LINKS"; tiered_scope.core item 6 (handoffs written under requests/<track>-requests/<slug>/reviews/); tests/test_doc_links.py:60-65 and :86-87

problem:
The reasoning behind the memory convention — _scanned_files() walks every .md outside EXCLUDED_PARTS, and a markdown link to a path that later moves turns CI red on an unrelated PR — applies identically to the handoff files under reviews/, which are Markdown in a scanned directory (`reviews` is not in EXCLUDED_PARTS) and are the artifacts most likely to cite ephemeral paths. var/ targets are skipped (tests/test_doc_links.py:86-87), so a drill artifact under var/ is safe, but a handoff citing a temporary file elsewhere is not.

proposed_fix:
Extend the convention to the handoff contract: all file paths in the handoff are inline code, never markdown links, and the handoff-schema lint asserts zero markdown links whose target is not a tracked file. One extra assertion in the test that already exists for hunk-freeness.
~~~

### F20 (question)

~~~
title: Adjacent verified doc drift: both panel prompts attribute "greedy-but-gated" to a README that does not contain it
severity: question
confidence: high
category: completeness
adversary: fit-ac

location:
scope_panel.js:123 and implement-plan/SKILL.md:41-42 both cite requests/feature-requests/README.md as the source of "the two standing principles GREEDY-BUT-GATED and GENERATE -> CONVERGE -> TRIAGE -> YOU-DECIDE"; grep shows requests/feature-requests/README.md contains neither phrase, and "Generate -> converge -> triage -> you decide" lives at requests/README.md:40

problem:
I grepped for both phrases. requests/feature-requests/README.md (93 lines, read in full) contains neither. requests/README.md:40 carries "Generate -> converge -> triage -> you decide". "Greedy-but-gated" appears only inside skill files and panel scripts — it is defined nowhere under requests/. So every scoping and implementation subagent is told to read a contract from a file that does not state it, in a repo whose premise (tests/test_repo_structure.py:3-6, update-docs/SKILL.md:28-31) is that docs are read as authoritative and drift is a correctness problem. Pre-existing and not this feature's fault, but it sits directly on the surface this feature is about, and the scope already sets a precedent for handling adjacent drift by recording the fixtures-recorder gap rather than absorbing it.

proposed_fix:
Decide explicitly, the way the fixtures-recorder gap was decided: either absorb a two-line fix (state both principles in requests/feature-requests/README.md under the pipeline table, where the panels are told to find them) or record it as its own request and name it in the scope's risks alongside the recorder gap. Do not leave it unnoticed — the stage-3 planner reads scope_panel.js:123's claim as ground truth.
~~~

### F21 (question)

~~~
title: Open question: what is the agent actually invoked BY, and does that change the deferred-benefit story?
severity: question
confidence: medium
category: fit
adversary: fit-ac

location:
Merged scope: goals[1], gated_decisions[1], non_goals[0] and [13], above_and_beyond drop item 4; repo: scope_panel.js:96 (the Workflow agent() primitive), verified absence of .claude/settings.json including untracked

problem:
The scope never states the invocation path it is designing for. Two candidates exist with different consequences: (a) the main thread spawning a .claude/agents/-defined subagent directly, which is what the artifact family conventionally serves and what the proving runs would use; (b) a panel script's agent() primitive selecting an agent type, which is what a future /implement-plan rewiring would need. The scope's evidence and its risks are written as though these were one mechanism. If (b) is unavailable, non-goal 14's honest concession ("realizing the benefit routinely requires a later request that wires the agent into a stage") is not merely deferred work but possibly unreachable work — which the user should know before disposing the timing question raised in F4.

proposed_fix:
Add a third explicit question to the harness probe and record its answer with a label: can a Workflow panel script select a .claude/agents/ definition when spawning? Then state, in one sentence in the summary, the invocation path the v1 design targets. If the answer is no, add a sentence to the fit verdict and to ADR 0007's Consequences saying the routine-benefit path requires a harness capability this repo does not control.
~~~

### F22 (question)

~~~
title: Open question: should the memory file's per-entry format be settled here, given the curation protocol is deferred?
severity: question
confidence: medium
category: scope-creep
adversary: fit-ac

location:
Merged scope: tiered_scope.core item 4 (per-entry format: date / epistemic label / the claim / an evidence pointer / a routing tag) vs non_goals[2] (curation protocol deferred because "speculating about tribal knowledge before having any produces a schema nobody fills"); FEATURE_REQUEST.md:100-103

problem:
The scope defers the curation protocol on the request's stated reasoning — designing pruning criteria against zero entries produces a schema nobody fills — then in the same document fixes a five-field per-entry schema, an entry-format guard test enforcing it, a routing tag vocabulary, and a seeding rule, all against those same zero entries. Those are the same class of decision. The seeding fold partially covers this (2-4 real entries give the format something to be designed against) but the seeds are hand-picked by the implementer rather than produced by the agent, so they will fit whatever format is chosen by construction. This may still be right — a format is cheaper to revise than a protocol — but the asymmetry is unexplained and a reviewer will notice it.

proposed_fix:
Either state plainly why a format is cheap-to-revise where a protocol is not (one sentence in non-goal 3), or soften: require only what the guard tests — a date, an epistemic label, and free prose — and defer the routing tag and evidence-pointer fields to the curation request that will have real entries to design against. The lighter version still satisfies the guard and the seeding fold.
~~~

### A2-01 (blocker)

~~~
title: No acceptance criterion proves the agent definition is what caused the behavior
severity: blocker
confidence: high
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria items 1-3, 9-11; risks item 2 (DEAD-ARTIFACT RISK)

problem:
The scope names dead-artifact risk explicitly — the definition ships in a format nothing loads, every shape-based criterion still passes green, and the feature is two Markdown files and zero capability. It then fails to close it. Criteria 1-3 assert the file EXISTS, has frontmatter, and contains literal clauses. Criteria 9-11 assert files under reviews/ exist and are well-formed — all of which the main thread could produce by hand with no subagent involved. Nothing asserts causation: that removing or corrupting .claude/agents/<agent>.md changes what happens. The summary says the probe 'is the difference between a working capability and two well-formed Markdown files nothing reads', then omits the criterion that would tell those states apart.

proposed_fix:
Add a CAUSATION criterion: the proving run's handoff must contain a marker that appears ONLY in the definition (a nonce, or the three-way escalation vocabulary the definition alone specifies), and the reviews/ trail must record a second run with that clause removed showing the marker absent. If the harness cannot support a clean A/B, state in ADR 0007 that the definition's causal role is `inferred`, not `verified`, and downgrade the acceptance language.
~~~

### A2-02 (blocker)

~~~
title: The harness probe is core but carries no decision rule for a negative answer
severity: blocker
confidence: high
category: risk
adversary: scope-completeness

location:
goals item 2; tiered_scope.core item 1 (HARNESS PROBE FIRST); gated_decisions item 2

problem:
The probe is the first core item precisely because the answer is unknown, and the scope specifies no branch for the answer it most fears. If nothing on this harness loads .claude/agents/*.md, or per-agent tool permissions cannot be declared anywhere (there is no .claude/settings.json — verified against git ls-files), the scope has no stated response: not stop, not reshape into a prompt template under .claude/skills/, not proceed with the posture recorded as unenforceable. A probe whose result cannot change the plan is documentation, not de-risking. This is the highest-probability failure the scope identifies and the one with no contingency attached.

proposed_fix:
Attach a disposition rule to the probe as part of the scope: (a) definition loads and frontmatter accepts a tool declaration -> proceed as scoped; (b) loads but tool posture is prompt-only -> proceed, and ADR 0007's Consequences must say the allowlist is instruction not enforcement; (c) nothing loads .claude/agents/ -> STOP and reshape to a committed prompt template invoked by the main thread, which changes the artifact family, the doc integration, and most of the guard suite. Make (c) an explicit kill/reshape criterion so the run cannot drift into building the files anyway.
~~~

### A2-03 (blocker)

~~~
title: The proving-run design depends on committed fixtures that do not exist
severity: blocker
confidence: high
category: completeness
adversary: scope-completeness

location:
non_goals item 12 ('offline against DuckDB and committed fixtures'); gated_decisions item 1 option (a) ('a scratch dbt project under gitignored var/ built against a committed fixture')

problem:
Verified: tests/fixtures/ contains exactly one file, tests/fixtures/README.md (git ls-files and a recursive listing both confirm zero fixture payloads). The scope's non-goal promises proving runs are 'offline against DuckDB and committed fixtures', and gated decision #1's recommended option (a) builds the omission drill 'against a committed fixture'. There is nothing to build against. The scope separately notes as adjacent drift that tests/fixtures/README.md:13 tells the reader to capture fixtures 'with the recorder' and no recorder exists — but never connects that to its own dependency on fixtures.

proposed_fix:
Either (a) specify the drill target as a seed-based or literal-CTE dbt model needing no fixture — dbt's --target ci is in-memory DuckDB, and a `select 1 as game_id, 1 as player_id union all ...` model carries a declared grain and a uniqueness test perfectly well; or (b) add 'capture one small fixture' as an explicit prerequisite in core and name where it comes from given no recorder exists. Do not leave 'committed fixtures' in a non-goal as though they were available.
~~~

### A2-04 (major)

~~~
title: The diff-hunk lint will false-positive on house-voice prose — every SKILL.md uses bare --- lines
severity: major
confidence: high
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria item 10 (grep for ^@@, ^+++, ^--- returns nothing); tiered_scope.cheap_folds item 5

problem:
Measured: every one of the eight SKILL.md files contains 4-5 lines that are exactly `---` (frontmatter delimiters plus horizontal-rule separators — e.g. implement-plan/SKILL.md:1, :18, :45, :267, :275). The scope explicitly asks the definition and handoff to be 'written in house voice — the SKILL.md register' (core item 2). A handoff in that register, or one carrying YAML frontmatter, will contain ^--- and the criterion fails on a correct artifact. ^--- is also the setext underline for an h2. The criterion punishes the style the scope mandates.

proposed_fix:
Drop ^--- from the pattern and lint only for unambiguous unified-diff markers: `^@@ ` (with trailing space) and `^diff --git`, optionally `^index [0-9a-f]{7}`. Those cannot appear in normal prose. If a stronger check is wanted, threshold the density of `^[+-]` lines rather than banning the character. Also reconcile the two spellings — criterion 10 says `^\+\+\+` and cheap_fold 5 says `^+++`; in POSIX BRE `+` is literal, so those are different commands.
~~~

### A2-05 (major)

~~~
title: Core tier contradicts the scope's own 'keep the build small' mitigation
severity: major
confidence: high
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.core (11 items) + tiered_scope.cheap_folds (12 items); fit_verdict rationale ('The mitigation is to keep the build genuinely small'); risks item 1

problem:
The fit verdict rests on an honest weakness — the problem is inferred, not observed (measured: src/nba_platform/ is one __init__.py, transform/models/ has zero .sql files, three Phase-0 commits, /implement-plan has never run here) — and the stated mitigation is a small build. The tiering does the opposite. Core alone: a harness probe, a definition, a memory file, an invariant restatement plus drift guard, a routing rule, a return-contract artifact plus lint, an escalation policy, a five-part write-guard package, a six-guard pytest suite each with a negative control (~12 test functions under mypy --strict), two proving drills (recommended 2x each = up to four agent runs), a directory README, CLAUDE.md edits, and ADR 0007. ADR 0001:48-49 names over-processing as this repo's standing accepted risk and ADR 0001:18 names picking the wrong thing to inflate as the failure mode; a scope citing both and shipping this much is not applying them.

proposed_fix:
Re-tier to a genuine v1. CORE = harness probe (with A2-02's decision rule), the definition, the memory file, ONE proving drill (the omission drill — the only behavioral one), TWO guards (frontmatter/structure validity, guardrail-clause presence) each with a negative control, and the CLAUDE.md map + convention edits. GATED = the invariant drift guard, memory-budget guard, memory entry-format guard, handoff schema lint, the faithful-spec run, .claude/agents/README.md, and ADR 0007 timing. That is a build a reviewer can hold in one head, which is what the premise risk demands.
~~~

### A2-06 (major)

~~~
title: .claude/agents/README.md is folded into core on a precedent that cuts the other way
severity: major
confidence: high
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.core item 11 (DOC INTEGRATION — '.claude/agents/README.md ... the repo already enforces self-documenting directories for dbt layers at tests/test_repo_structure.py:77-84')

problem:
The cited test is test_every_layer_documents_itself (tests/test_repo_structure.py:77-84); reading it, it iterates _layer_directories() — subdirectories of transform/models/ only — and asserts each has a README. It is a medallion-layer rule, not a repo-wide convention. The counter-evidence is decisive and in the same tooling family: .claude/skills/ has NO README (verified via git ls-files — 16 files, eight SKILL.md, three panel scripts, five .mjs guards, no README.md anywhere under .claude/). The precedent argues the opposite of the claim. This adds a third Markdown file to a feature the scope describes as two, and a third surface the doc gate and link checker must maintain.

proposed_fix:
Drop .claude/agents/README.md from core. Put the spawn protocol and the directory's purpose inside the agent definition (already the human-maintained file) or in ADR 0007's Decision section. If a directory README is genuinely wanted later it should arrive alongside one for .claude/skills/ so the convention is consistent. Correct the cited precedent either way — as written it misrepresents a dbt-layer test as a repo-wide rule.
~~~

### A2-07 (major)

~~~
title: 'Make CLAUDE.md's 200-line budget mechanical' is unrelated scope and silently reassigns a convention
severity: major
confidence: high
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.cheap_folds item 7; above_and_beyond 'Make CLAUDE.md's 200-line budget mechanical'

problem:
Two problems. (1) Relevance: a change to an unrelated governance surface folded into a feature about subagents. Its justification is 'the memory-budget guard is the same assertion' — mechanism reuse is not a reason to expand blast radius, and it is exactly the fold shape requests/README.md's greedy-but-gated principle exists to catch ('never silently folded into the build'). (2) It changes a stated convention: CLAUDE.md:80-82 reads 'Mechanical checks live in CI; judgment lives in /update-docs', and update-docs/SKILL.md:76-78 places the budget deliberately in the judgment half with 'over budget means cutting, not reformatting'. Moving it to CI relocates an item across that boundary — possibly correct, but presented as a three-line cheap fold with no acknowledgement.

proposed_fix:
Move to gated and state the convention question in the gate: does the line budget belong in CI (mechanical) or stay in /update-docs (judgment)? If taken, the same PR must adjust update-docs/SKILL.md:76-78 so the doc gate stops claiming a check CI now owns, and CLAUDE.md's mechanical-vs-judgment bullet should list it. Do not land it as an unremarked side effect.
~~~

### A2-08 (major)

~~~
title: Gated decision #1's recommendation takes both options, converting a gate into a fold and landing unscoped work
severity: major
confidence: high
category: scope-creep
adversary: scope-completeness

location:
gated_decisions item 1 recommendation ('Take (a) for the OMISSION DRILL and (b) for the FAITHFUL RUN')

problem:
The gate is framed as a choice among three proving-run targets and the recommendation selects two, doubling the proving work rather than bounding it. Worse, option (b) is 'a small, genuinely useful, non-dataset repo task' whose output the scope wants kept so 'the evidence is a real diff a human reviews'. That means an unrelated piece of repo work — no feature request behind it, chosen by the implementer at build time — lands inside a PR about agent tooling. Non-goal 11 fences 'NOT any pipeline code, dbt model, extraction client, or fixture landing in the repo as a by-product', and option (b) is precisely a by-product landing in the repo, just a non-pipeline one. It also makes the PR's diff unreviewable as a single subject.

proposed_fix:
Pick one target. Recommend (a) — the scratch drill under gitignored var/, rebuilt per A2-03 to need no fixture — as the single core proving run, because the omission drill is the only criterion testing behavior rather than shape. Make the faithful-spec run against a real repo task a GATED add-on; if the user takes it, require the target be named in the scope (or carry its own request) rather than chosen during implementation.
~~~

### A2-09 (major)

~~~
title: The claim that every clause of the skill-quality mandate applies verbatim to an agent definition is false
severity: major
confidence: high
category: fit
adversary: scope-completeness

location:
above_and_beyond 'Teach the acceptance panel about .claude/agents/' ('Every clause of the skill-quality mandate (acceptance_panel.js:199) applies verbatim to an agent definition')

problem:
Read against the actual mandate at acceptance_panel.js:199, the claim fails in two of five clauses. Clause (1) asks 'Does SKILL.md have valid frontmatter (name + a trigger-rich description), and does the DESCRIPTION match what the skill now does' — an agent definition is not a SKILL.md and, per the scope's own goal 2, its frontmatter schema is unconfirmed and may not be name+description. Clause (3) asks whether the skill is registered in CLAUDE.md 'How to Help' and in 'the appropriate track README (requests/feature-requests/README.md ...)' — an agent definition belongs in neither, and a track README row for it would be wrong. So bucketing an agent-definition change as `skills` today draws a specialist that generates confident false findings, which is worse than drawing none.

proposed_fix:
Correct the claim. If the gated 'teach the panels' item is taken it is not a one-word addition — the skill-quality mandate needs a conditional branch for agent definitions (frontmatter per the probed schema; registration in CLAUDE.md's project map rather than 'How to Help'; no track README row). Record that as the real cost, or defer and note in ADR 0007's Consequences that agent-definition changes currently draw no correct specialist lens.
~~~

### A2-10 (major)

~~~
title: The AREA_TO_SPEC gap is misdiagnosed — no JS change is needed, only a prose bucket widening
severity: major
confidence: high
category: fit
adversary: scope-completeness

location:
gated_decisions item 6 ('Take the DOC half now, defer the JS half ... The JS half edits acceptance_panel.js'); risks item 13; above_and_beyond 'Teach the acceptance panel about .claude/agents/'

problem:
Verified at acceptance_panel.js:202-207: AREA_TO_SPEC is keyed by BUCKET NAMES supplied in the touchedAreas argument and already contains `skills: ['skill-quality']`; specKeys is derived as AREAS.flatMap(a => AREA_TO_SPEC[a] || []). Nothing in the JS enumerates directories. Spawning the skill-quality specialist for a .claude/agents/ change requires only that the main thread pass 'skills' in touchedAreas — a prose decision at implement-plan/SKILL.md:129 ('skills (.claude/skills/)'), not a code path. There is no missing `agents` key and adding one would be net-new and unnecessary. The scope presents the cheap fix as blocked behind an expensive one, citing risk from two uninstrumented .mjs guards that cover code nothing needs to change.

proposed_fix:
Rewrite the gate: the only change needed is widening the bucket-definition prose in two places — implement-plan/SKILL.md:129 and update-docs/SKILL.md:48 — from 'skills (.claude/skills/)' to cover .claude/ tooling generally. Doc edit, no JS, no .mjs guard exposure, same class of edit the scope already accepts for CLAUDE.md. Fold it or gate it on the request's /implement-plan fence, but stop describing a JS change that is not required. Note that once bucketed as skills, A2-09 applies.
~~~

### A2-11 (major)

~~~
title: This PR's own guard suite buckets as tests, which maps to the extraction specialist — the wrong lens
severity: major
confidence: high
category: completeness
adversary: scope-completeness

location:
acceptance_panel.js:203 (tests: ['extraction']); tiered_scope.core item 9; above_and_beyond 'Guards in pytest under tests/, not as a .mjs sibling'

problem:
The scope's largest claimed value-add is putting guards under tests/ so they become a required check. Verified consequence nobody traced: AREA_TO_SPEC maps tests -> ['extraction'], and the extraction mandate (acceptance_panel.js:198) is entirely about landing-zone immutability, pacing, backoff, resumability, bulk endpoints, payload provenance, and live-API tests. Applied to Markdown-linting pytest guards it finds nothing real and may fabricate findings to fill the schema. So if this feature is itself implemented through /implement-plan, the diff draws four core reviewers plus an irrelevant specialist and — per A2-09/A2-10 — no correct one. The scope never considers how its own change gets reviewed.

proposed_fix:
Name this in the scope as a known review-posture gap for THIS PR with the mitigation stated: bucket the diff as skills + docs (not tests) when spawning stage 4, or run the acceptance panel with a hand-written specialist mandate for prose-artifact guards. Record the tests -> extraction mapping as a candidate bugfix request in its own right — it misfires on any test-only change, not just this one.
~~~

### A2-12 (major)

~~~
title: No non-goal fences the write-capable agent to the repository root
severity: major
confidence: medium
category: risk
adversary: scope-completeness

location:
tiered_scope.core item 8 (THE WRITE-GUARD PACKAGE — 'a declared write allowlist in the definition'); non_goals items 6, 9, 10

problem:
The write allowlist is described as 'the memory file and the task's target paths', declared in prose in the definition. Every write-related non-goal is about git operations, self-modification, or pipeline skills — none bounds writes to the repository. This session's environment declares a second additional working directory outside the repo (a FarmingSimulator savegame path), and a subagent inheriting the session's working-directory set can write there. The entire detection apparatus the scope builds — pre/post git status --porcelain, git diff HEAD --stat, tree-integrity comparison, /commit's per-path staging — is git-scoped and blind to any write outside the repo. The scar the scope re-admits (implement-plan/SKILL.md:123-125) was an in-repo destruction; an out-of-repo one leaves no evidence at all.

proposed_fix:
Add an explicit non-goal and a matching definition clause: the agent writes only under the repository root, never to any additional working directory, never to an absolute path outside the repo, never outside the declared allowlist. Include it in the guardrail-clause presence guard so deletion reddens CI. Note in ADR 0007's Consequences that tree-integrity covers the repo only, so this clause is instruction with no detector behind it.
~~~

### A2-13 (minor)

~~~
title: CLAUDE.md:40 says 'Six ADRs' — the ADR-0007 integration item misses the drift it creates
severity: minor
confidence: high
category: completeness
adversary: scope-completeness

location:
CLAUDE.md:40-41; acceptance_criteria item 8; tiered_scope.core item 11

problem:
Verified: CLAUDE.md line 40 reads '- **[docs/decisions/](docs/decisions/)** — start here. Six ADRs cover the scope range, the storage substrate, the engine choice, the serving layer, and why the repo is public.' Landing ADR 0007 makes that sentence false, and it also enumerates subject areas — none of which is process tooling or subagents. The scope's doc-integration item names the project-map block, the subagent bullet, and the ADR index table, but not this line. /update-docs Step 2 would catch it by judgment, but the acceptance criteria are meant to be mechanically checkable and this is invisible to them.

proposed_fix:
Add to the doc-integration core item and the bookkeeping criterion: CLAUDE.md:40-41 updates to 'Seven ADRs' with the subject list extended to name the tooling decision. Consider a guard asserting the ADR count word in CLAUDE.md matches the row count in docs/decisions/README.md's Index — a cheap structural check in the test_repo_structure.py family that closes a drift class rather than one instance.
~~~

### A2-14 (major)

~~~
title: Negative controls are required for only two of six guards in the acceptance criteria
severity: major
confidence: high
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria items 1, 2, 3, 4, 6 vs tiered_scope.core item 9 ('each with a NEGATIVE CONTROL')

problem:
The scope's strongest recurring argument is that a checker scanning nothing passes every time (tests/test_doc_links.py:95-104 exists for exactly that reason; the scar at implement-plan/SKILL.md:123-125 is a vacuous selftest passing green). Core item 9 and cheap_fold 1 both say every guard ships a negative control. The acceptance criteria enforce it for only two: criterion 3 (invariant drift) and criterion 4 (memory budget). Criteria 1 (frontmatter/structure) and 2 (guardrail-clause presence) have none — and criterion 2 guards the clauses that replace 'it can't write', making a vacuously-passing version of it the single most dangerous guard in the suite. A convention in scope prose but absent from a criterion is one the acceptance panel will not check.

proposed_fix:
Make it uniform in the criteria: every new guard ships a paired negative control asserting a deliberately mutated in-memory copy of the artifact FAILS the assertion, and each guard's criterion names its control. If uniformity makes the suite too large, cut guards (per A2-05) rather than controls — a guard without a control is worth less than no guard, because it manufactures confidence.
~~~

### A2-15 (major)

~~~
title: The memory file has a cap, a deferred pruning protocol, and no stated behavior at the cap
severity: major
confidence: medium
category: completeness
adversary: scope-completeness

location:
non_goals item 3 (curation deferred); acceptance_criteria item 4; gated_decisions item 3 (recommend 120 lines); risks item 12

problem:
The scope defers the curation protocol, enforces a hard line cap in CI, and names the resulting risk ('a cap reached with no pruning rule turns into either an arbitrary truncation or a quietly raised cap'). Then it stops. Nothing states who prunes, on what trigger, or what the agent does when its append would breach the cap. With 2-4 seeded entries at ~5 lines each plus a header, a 120-line file is ~35 lines used and fills after roughly 17 entries. At that point CI is red and the agent cannot complete its task without either deleting someone else's entry or failing — both bad, and neither chosen. A cap without an at-cap rule converts a deferral into a scheduled outage.

proposed_fix:
Add one sentence to the definition and one non-goal: at the cap the agent does NOT prune and does NOT raise the cap — it reports the overflow entry in the handoff's surprised-me section and leaves the file unchanged, making the cap a signal that routes curation to the human rather than a build failure. State that raising the cap is a human decision recorded in ADR 0007 or a follow-up, never an edit inside an agent run.
~~~

### A2-16 (major)

~~~
title: No abandon criterion — premise risk is named as #1 and no evidence would stop the build
severity: major
confidence: medium
category: risk
adversary: scope-completeness

location:
risks item 1 (PREMISE RISK, the largest); fit_verdict rationale (THE ONE HONEST WEAKNESS); gated_decisions item 1 closing note

problem:
The scope is unusually honest that the problem has not happened (measured: zero pipeline code, zero models, three Phase-0 commits, /implement-plan never run) and records the minimalist's timing dissent. But every path through it ends in shipping. The gated decision offers 'if you would rather wait ... that is defensible and this is the decision point for it' — a wait-or-proceed choice made BEFORE any evidence, not a criterion evaluated AFTER the proving runs. Nothing states what a proving-run result would have to look like for the right answer to be 'delete these files and revisit after box-score-foundation'. Given ADR 0001:48-49 names over-processing as a standing accepted cost, a feature whose premise is inferred should carry its own off-ramp.

proposed_fix:
Add an explicit abandon criterion: if the omission drill fails (the agent ships an untested grain and does not flag it), or the harness probe returns case (c) from A2-02, the feature does not land — the branch is abandoned and the request returns to intake with the findings recorded. Two sentences, and it is the only thing that makes premise risk a managed risk rather than an acknowledged one.
~~~

### A2-17 (minor)

~~~
title: Spec-triage (dry-run) mode is a second operating mode folded as cheap with no acceptance criterion
severity: minor
confidence: high
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.cheap_folds item 10; above_and_beyond 'Spec-triage (dry-run) mode'

problem:
Justified as 'one paragraph in the definition plus a documented invocation phrase', but it is a distinct behavioral mode with its own contract (read the plan, report gaps, build nothing) and its own failure mode (the agent builds anyway). No acceptance criterion exercises it, no guard checks its clause is present, and neither proving run uses it. It is a feature added to a feature whose core capability is unproven, and it will read as tested because it sits in a scope with a large green suite. That is an unfalsifiable fold.

proposed_fix:
Either promote it with a criterion — a third drill invoking the agent in triage mode against a deliberately gappy spec, where `git status --porcelain` after the run is byte-identical to before (an objectively checkable no-write assertion) — or drop it to deferred. Do not carry a mode nothing tests.
~~~

### A2-18 (minor)

~~~
title: The /commit USER-RUN criterion is close to vacuous and does not test what the design leans on
severity: minor
confidence: medium
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria item 14; risks item 10; commit/SKILL.md:47-67

problem:
The criterion is that a /commit run 'stages the memory delta as a visible per-path entry, confirming that the review gate the whole design leans on behaves as assumed'. /commit stages per path by construction (commit/SKILL.md:47-53), so the criterion cannot fail and confirms nothing. What the design actually leans on — and what the scope itself flags as the weak point (risk 10: free prose is what /commit's refusal table is weakest against, because it is not a recognizable credential file) — is whether a human reading the staged diff can distinguish the agent's writes from their own and catch a careless machine path, account ID, or response fragment in prose. Neither is checked.

proposed_fix:
Rewrite as a criterion that can fail: run /commit over a proving-run diff containing one plausible-looking leak in a memory entry (a fake absolute machine path, or an account-id-shaped string) and record whether the staged-diff scan surfaced it. Record the result honestly either way in ADR 0007's Consequences. If a deliberate-leak drill is unpalatable in a public repo, drop the criterion rather than keep an unfailable one.
~~~

### A2-19 (minor)

~~~
title: Memory-vs-docs routing is one-directional — nothing at the destination knows about the source
severity: minor
confidence: high
category: completeness
adversary: scope-completeness

location:
tiered_scope.core item 5 (THE MEMORY-VERSUS-DOCS RULE); non_goals item 8; risks item 9; update-docs/SKILL.md:103-112

problem:
The routing rule lives entirely in the agent definition and the handoff: memory says 'data facts go to docs/data-sources.md'. Nothing at the receiving end records that a new inbound route exists. update-docs/SKILL.md:103-112 audits docs/data-sources.md's epistemic labels with no awareness of .claude/agents/, and docs/data-sources.md itself is not touched by this scope at all. So the mechanism by which a discovered fact reaches the doc gate is: the agent writes a docs-delta section, and a human remembers what to do with it. The scope names the drift risk and the promotion queue but never closes the loop at the destination.

proposed_fix:
Add one line to docs/data-sources.md's header or contribution note stating that implementation-discovered facts arrive via a handoff docs-delta section and are promoted through /update-docs with a label. One line, link-checked for free, and it converts an undocumented convention into a documented one at the place someone would look.
~~~

### A2-20 (minor)

~~~
title: Acceptance criteria cite local pytest invocations that differ from what CI actually runs
severity: minor
confidence: high
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria items 1 and 5 (uv run pytest tests/test_repo_structure.py -q; uv run pytest tests/test_doc_links.py -q); ci.yml:50-53; pyproject.toml:77-82

problem:
CI runs `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` over testpaths = ['tests'] with addopts = '-q --strict-markers --strict-config'. The criteria cite per-file invocations without the marker filter or coverage. For pure-filesystem guards this will not diverge in practice, but the criteria are the contract a cold agent verifies, and ops/branch-protection.json:4 gates on the CI job named 'Lint, types, tests' — i.e. on CI's command, not these. A criterion naming a command CI does not run leaves a green-locally/red-in-CI seam open for no benefit.

proposed_fix:
State the acceptance command as CI's: `uv run pytest -m "not network"`, optionally naming the specific test ids that must appear in the passing set. Keep per-file invocations as convenience notes rather than criteria. Same for the link check, which legitimately runs per-file inside /update-docs (update-docs/SKILL.md:53-57) — say which context each invocation belongs to.
~~~

### A2-21 (nit)

~~~
title: The MIN_EXPECTED_FILES criterion is ambiguous about whether the constant must change
severity: nit
confidence: high
category: acceptance
adversary: scope-completeness

location:
acceptance_criteria item 5 ('MIN_EXPECTED_FILES = 20 (line 53) against 30 tracked .md files today, rising to at least 33')

problem:
Verified: MIN_EXPECTED_FILES = 20 at tests/test_doc_links.py:53, and 30 tracked .md files today. The phrasing 'rising to at least 33' reads as if something must rise; nothing in the scope asks for the constant to be bumped, and _scanned_files() walks the working tree via rglob rather than git, so the scanned count includes untracked Markdown and is not exactly the tracked count either. A cold implementer could reasonably bump the constant or not, and both would look correct.

proposed_fix:
Say plainly that the constant is NOT changed by this feature; the criterion is only that the new Markdown files appear in _scanned_files() and carry no dead links. If a bump is wanted so the anti-vacuity guard keeps its teeth as the repo grows, make it a separate explicit item with the new number stated.
~~~

### A2-22 (nit)

~~~
title: Track-agnostic `track` field is justified by a coupling the scope explicitly forbids
severity: nit
confidence: medium
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.cheap_folds item 8; non_goals item 1

problem:
The fold's entire rationale is that /implement-plan serves both tracks and auto-detects from the artifact path (implement-plan/SKILL.md:49-53). But non-goal 1 states the agent is NOT wired into /implement-plan and stage 4 is untouched, so the justification borrows a property of a coupling the scope forbids. The fold itself is one line and harmless; the reasoning is not sound, and unsound-but-cheap reasoning is how the next, more expensive fold gets waved through.

proposed_fix:
Keep the field, fix the rationale: a human may hand the agent work originating from either track, and a handoff contract hardcoding 'feature' would need reworking the first time. Cite requests/README.md's three-track split rather than stage 4's auto-detection.
~~~

### A2-23 (minor)

~~~
title: The epistemic-label inconsistency is folded as a note without a decision
severity: minor
confidence: high
category: completeness
adversary: scope-completeness

location:
tiered_scope.cheap_folds item 2; above_and_beyond 'Memory entries carry the repo's epistemic vocabulary'; CLAUDE.md:76-79 vs update-docs/SKILL.md:105

problem:
Verified drift: CLAUDE.md:76-79 names five labels (measured / verified / inferred / assumed / unconfirmed) and requests/README.md's Principles repeats the same five; update-docs/SKILL.md:105 names four for docs/data-sources.md (measured / verified / documented / unconfirmed) — 'documented' in one, 'inferred'/'assumed' in the other. The scope spots this and says 'the implementation must pick a side', pushing a real repo-wide inconsistency into stage 4 as an unlabeled decision, which is what stage 2 exists to prevent. It is also drift the doc gate is supposed to catch and has not.

proposed_fix:
Decide it here: memory entries use CLAUDE.md's five, because CLAUDE.md is the stated authority and the agent's invariant restatement is explicitly non-authoritative relative to it. Then either record the update-docs/CLAUDE.md divergence as a separate one-line bugfix request, or note it in ADR 0007's Consequences as pre-existing and unresolved. Do not hand a governance inconsistency to an implementer as a coin flip.
~~~

### A2-24 (minor)

~~~
title: The scratch-under-var/ drill puts its primary evidence in a gitignored, unreviewable location
severity: minor
confidence: medium
category: acceptance
adversary: scope-completeness

location:
gated_decisions item 1 option (a); acceptance_criteria item 11; .gitignore:16 (var/); tests/test_doc_links.py:31-48

problem:
The omission drill's PASS condition is 'the produced model carries a uniqueness test OR the handoff explicitly flags the omission — determined by grep over the drill artifacts and quoted verbatim'. If the drill builds into var/ (gitignored, and excluded from the link checker by name), the artifacts the grep runs over are never committed; what lands is a summary quoting them. That is a self-report of a self-report — the reviewer cannot re-run the grep, and the acceptance panel, whose defining rigor is verification by execution (implement-plan/SKILL.md:29-35), cannot verify it either. The scope's own standard is that a claimed-met criterion nobody can re-run is not proof.

proposed_fix:
Require the drill's produced artifacts (the model .sql and its schema.yml, or their demonstrated absence) to be copied verbatim into reviews/ as fenced code blocks alongside the verdict, so the evidence is committed and the grep is reproducible. They are a handful of lines and carry no data, so /commit's bulk-data refusal (commit/SKILL.md:57-63) does not apply. Also note the dependency the scope omits: a scratch dbt project under var/ needs its own packages.yml plus `dbt deps` for dbt_utils.unique_combination_of_columns (transform/packages.yml pins it for the main project only) — name it, or design the drill around a plain `unique` test.
~~~

### A2-25 (minor)

~~~
title: The spawn protocol is required by core but has no stated home
severity: minor
confidence: medium
category: completeness
adversary: scope-completeness

location:
tiered_scope.core item 8 ('a documented main-thread spawn protocol reusing stage 4's procedure verbatim')

problem:
The write-guard package requires the main thread to follow a procedure — clean-tree precondition, pre-spawn git diff HEAD to gitignored var/ scratch plus the untracked list, post-run tree-integrity comparison. The scope never says where that procedure is written down. It cannot live in the agent definition (the agent is not the actor); CLAUDE.md is budgeted at 200 lines with 78 measured lines of headroom already being spent on the map and the convention clarification; A2-06 recommends dropping the directory README; and stage 4's copy at implement-plan/SKILL.md:120-125 sits inside a skill non-goal 1 fences off. An undocumented protocol is one nobody follows on the second spawn.

proposed_fix:
Name the home explicitly in the scope. The natural fit is ADR 0007's Decision section — the ADR already has to record what replaced 'it can't write' — with a one-line pointer from the CLAUDE.md subagent bullet. If the directory README survives A2-06, put it there instead. Pick one and say so; this is a scope-level call, not a plan detail.
~~~

### A2-26 (minor)

~~~
title: Two proving drills at up to 2x each is the dominant cost and only the multiplier is gated
severity: minor
confidence: medium
category: scope-creep
adversary: scope-completeness

location:
tiered_scope.core item 10; gated_decisions item 7 ('Two per drill if affordable')

problem:
Both drills are core; only the repetition count is gated, and its recommendation is two per drill — so the recommended path is four full agent runs plus their evidence artifacts, tree snapshots, and comparisons. That is the most expensive element of a build the scope insists must stay small, and the gate as framed can only make it more expensive (options are one, or two-to-three; never zero). Meanwhile only one drill tests behavior: the scope itself says the omission drill 'is the only criterion that tests FEATURE_REQUEST.md:46-47 rather than testing that files exist'.

proposed_fix:
Make the omission drill core at one run and gate BOTH the faithful-spec run and any repetition. Add the honesty clause unconditionally rather than as a fallback: however many runs happen, the acceptance ledger and ADR 0007 label the result a single observation of a nondeterministic process unless a repetition actually ran — per CLAUDE.md:76-79, overclaiming is a convention violation, not merely optimism.
~~~

### A2-27 (nit)

~~~
title: Non-goal 11 forbids by-products but no criterion detects one
severity: nit
confidence: medium
category: acceptance
adversary: scope-completeness

location:
non_goals item 11; acceptance_criteria (no corresponding check)

problem:
Non-goal 11 is unusually concrete and checkable — 'src/nba_platform/ still contains only __init__.py and transform/models/ still holds three READMEs and no .sql when this lands' — and it is exactly the by-product a write-capable builder produces by accident during a proving run. No acceptance criterion asserts it. The tree-integrity criterion (item 12) checks that nothing OUTSIDE the allowlist was modified or deleted; it does not check that nothing NEW appeared under src/ or transform/models/. Given A2-08 flags a recommended proving run that produces a real kept diff, this is live rather than theoretical.

proposed_fix:
Add a one-line mechanical criterion in the test_repo_structure.py family: at PR time, transform/models/**/*.sql is empty and src/nba_platform/ contains only __init__.py. Two assertions, it directly enforces a stated non-goal, and it is the cheapest guard in the whole suite.
~~~

### A2-28 (nit)

~~~
title: README.md is never mentioned, so the doc gate will raise it mid-commit
severity: nit
confidence: medium
category: completeness
adversary: scope-completeness

location:
tiered_scope.core item 11; update-docs/SKILL.md:80-87; commit/SKILL.md:83-93; README.md:69-80

problem:
/update-docs Step 2 checks README.md's status blockquote, roadmap table, setup steps, architecture table, and repo layout, and /commit Step 3 triggers the full sweep on 'a new or changed directory'. This feature creates a new top-level tracked directory. Verified: README.md's 'Repo layout' block (lines 71-80) omits .claude/ entirely, so consistency argues for NO change — but the scope never says so, so the doc gate surfaces it as an unresolved judgment call at the worst moment, mid-commit. CLAUDE.md, the ADR index, and the requests Index are covered; README is the one described surface left unaddressed.

proposed_fix:
Add one line to the doc-integration item: README.md is deliberately unchanged, because its Repo layout block does not enumerate .claude/ at all and adding .claude/agents/ alone would make it inconsistent. Recording the non-change is what stops it being rediscovered as a question.
~~~

### A2-29 (question)

~~~
title: Open question — should the invariant restatement exist at all in v1, given the scope's own shape argument
severity: question
confidence: medium
category: framing
adversary: scope-completeness

location:
tiered_scope.core item 3; convergence_map item 9; scope_panel.js:118-130

problem:
The scope resolves point-vs-restate by doing both: a compressed non-authoritative restatement in the scope_panel.js:124 shape, plus a drift guard. But scope_panel.js:124 restates into a PROMPT built at runtime, not into a committed artifact a human maintains — a different failure mode, and the drift guard is being invented to make safe a pattern the precedent never needed. Meanwhile the scope also reports (measured, two independent observations) that panel-spawned subagents receive the full project CLAUDE.md unrequested. If .claude/agents/ inherits the same way, the agent already HAS the authoritative invariants and the restatement is a fourth copy solving nothing but narrowness-by-emphasis. The scope never sequences the probe's answer against this decision, even though the probe is core and comes first.

proposed_fix:
Make the restatement conditional on the probe: if CLAUDE.md is inherited, the definition carries a POINTER plus an emphasis note ('these rules bind you absolutely; CLAUDE.md is authoritative') and no drift guard is needed; if it is NOT inherited, the definition carries the compressed restatement and the drift guard becomes load-bearing. This removes a guard and its negative control from the likely branch, and it makes the probe's answer actually change the build — which A2-02 asks for generally.
~~~

### A2-30 (question)

~~~
title: Open question — is a memory file that only one unproven agent writes worth committing to a public repo now
severity: question
confidence: low
category: framing
adversary: scope-completeness

location:
goals item 4; non_goals item 12; risks items 10 and 12; docs/decisions/0006-public-repository.md:44-49

problem:
The scope settles committed-vs-gitignored well — the local-red/CI-green argument from EXCLUDED_PARTS not being gitignore-aware is genuinely the strongest reason, and I verified it. But it never asks the prior question: does the memory file need to exist in v1, or is it the half of the paired design that should wait for evidence? The scope defers curation because 'speculating about tribal knowledge before having any produces a schema nobody fills' — then ships the schema, seeded with 2-4 entries the repo earned WITHOUT the agent, into a public repo where ADR 0006:44-49 makes every entry permanent and warns that 'one careless paste of a connection string is a real incident'. The seeded entries are real, but they are evidence for CLAUDE.md's Constraints & Gotchas or a skill's prose, not evidence that an agent-appendable file is needed.

proposed_fix:
Put it to the user as a gate the scope does not currently offer: v1 = definition only, with the handoff's surprised-me section as the memory-candidate queue and the human deciding where each entry lands (CLAUDE.md, docs/data-sources.md, or a memory file created once entries justify it). That defers the file, the cap, the entry-format guard, the routing guard, and the public-permanence exposure — and it is fully consistent with the reasoning the scope already used to defer curation.
~~~


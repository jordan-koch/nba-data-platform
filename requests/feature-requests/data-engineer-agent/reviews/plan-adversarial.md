# Plan Panel - Adversarial + Meta-Audit Findings (data-engineer-agent)

> Stage 3 provenance. Panel run `wf_7be42ca6-2f7`, 2026-08-13/14.

## Panel health

| Lens | Result |
|---|---|
| Planners | 3/3 |
| Adversary - code-grounded | OK - 14 findings |
| Adversary - executability | OK - 19 findings |
| Meta-audit | OK - 13 findings |
| `degraded_lenses` | none |

**46 findings: 1 blocker, 18 majors.** 13 convergence entries, 9 gated decisions, 16 plan
decisions, 78 code references, 7 phases.

### Run history - the first attempt was degraded

The panel was run twice. The first attempt lost two lenses: the structured merge died
(`API Error: Connection lost mid-response`) and the code-grounded adversary died. That run
produced a `plan_draft` that was a CONCATENATION of the three proposals - 23 phases under three
incompatible numbering schemes, with `convergence_map`, `decisions`, `conventions` and
`gated_decisions` all empty. It was not used.

The run was resumed rather than restarted: the three planner proposals replayed from cache and
the merge, the dead adversary and the two downstream reviewers re-ran live. The second attempt
completed with all seven agents green and no degraded lenses. Everything below is from that
second attempt. Recorded because the first attempt's five blockers were mostly merge artifacts,
and a reader comparing token spend against findings would otherwise find the gap unexplained.

### Main-thread independent spot-check

Run against the tree directly, before and after the resume, to confirm the code-grounding was
real rather than asserted. Ten claims checked, all confirmed:

| Claim | Verified result |
|---|---|
| `CLAUDE.md` length, two semantics | 122 by `Measure-Object -Line`, 140 by `(Get-Content).Count` - the ~15% ambiguity gate #1 exists to settle |
| `dbt_utils` on disk | Present at `transform/dbt_packages/dbt_utils` |
| `dbt_utils` TRACKED in git | **No** - `dbt_packages/` is gitignored at `.gitignore:50`, so it is untracked local state (confirms M-05) |
| How CI gets it | `dbt deps` at `ci.yml:70-71` before `dbt build` at `:76` - any local dbt gate must run `dbt deps` first |
| `.claude/agents/` exists | False |
| `.claude/settings.json` exists | False |
| Tracked Markdown file count | 33, against `MIN_EXPECTED_FILES = 20` |
| `tests/test_repo_structure.py` root resolution | `parents[1]` at line 19 |
| `tests/test_repo_structure.py:77-84` | `test_every_layer_documents_itself`, exactly as cited |
| `AREA_TO_SPEC` unknown-area behavior | At `:202-206` with no `agents` key; `:207` resolves an unknown area to `[]` silently (confirms F2 / A2-EX-03) |

The feature-requests README status grammar is `intake` -> `scoped` -> `planned` -> `implemented`,
so an Index cell of `plan` is off-grammar - confirming F5 and A2-EX-10 independently.

## Convergence map (where >=2 planners agreed - highest signal)

~~~~~
- [1]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: The harness probe is Phase 0, blocking, with an explicit STOP rule on a negative finding
  why_high_signal:
    All three independently reached the same grounding — `scope_panel.js:174` spawns with no agent-type parameter, `Test-Path .claude/agents` is False, no `.claude/settings.json` exists — and all three drew the same conclusion: every shape-based criterion (AC1, AC2, AC4-AC8) passes green in the dead-artifact failure case, so the probe is the only thing separating a working capability from three well-formed Markdown files. Blocker fix A2-02 makes the STOP rule scope, not preference. Three lenses converging on 'do not soften this into a note' is the strongest signal in the panel.
- [2]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: AC1's 'exactly one *.md agent definition' collides with the scope's own three-file directory; discriminate by YAML frontmatter
  why_high_signal:
    All three found the same latent contradiction between AC1 (PROJECT_SCOPE.md:127) and Core scope (:165, :169, :183), and all three proposed the same fix shape — a definition is a `.md` carrying frontmatter with non-empty name+description, README and memory carry none. This is a guard that would have reddened on the very commit that completes the feature, caught before a line was written.
- [3]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: Two line-counters disagree by 18 lines and the memory cap is ambiguous until one is pinned
  why_high_signal:
    Independently measured by all three: `Measure-Object -Line` returns 122 while the file has 140 physical lines. AC7 names the PowerShell form, `update-docs/SKILL.md:76-78` documents it, and Decision 5 sets a 120-line memory cap — so the cap means two different things depending on who checks it, a ~15% ambiguity. Three-way convergence turned a footnote into a gated decision plus an in-message counting rule.
- [4]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: Guards land under `tests/` (a required check) and every guard ships a negative control
  why_high_signal:
    All three grounded it identically: `ci.yml` has three jobs and no Node step, so `.mjs` guards are etiquette while `ops/branch-protection.json:4` makes pytest enforcement; and all three cited the same two scars for the negative controls — `tests/test_doc_links.py:95-104` ('a link checker that scans nothing passes every time') and `implement-plan/SKILL.md:123-125` (a vacuous selftest passing green while work was destroyed). All three also independently prescribed pure predicate functions over text so a control can be written at all.
- [5]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: The CLAUDE.md relocation is the riskiest edit in the build and must be its own reviewable commit, verified add-then-remove
  why_high_signal:
    All three flagged that a bad cut fails SILENTLY — it degrades every future session rather than erroring — and all three noted this risk arrived post-panel (Decision 12) and was never adversarially reviewed. The domain lens added the sharpest specific: `CLAUDE.md:113-116`, the as-of-game-date affiliation warning, is the repo's highest-value silent-wrongness rule and it travels with the cut. The clause-presence guard becomes the cut's regression test.
- [6]
  planners:
    - sequencing
    - domain-convention
  theme: The relocation must precede the omission drill, or the drill's PASS is unattributable
  why_high_signal:
    The sequencing lens named the confound explicitly (`CLAUDE.md:95-97` states the grain rule today, and a panel-spawned subagent is MEASURED to inherit the full project CLAUDE.md per PROJECT_SCOPE.md:143), and the domain lens's phase order independently placed the relocation before both drills. This is the plan's one non-obvious ordering call, and blocker A2-01 says the drill is the ONLY criterion that can prove the definition caused the behavior — so reordering for convenience destroys the feature's only behavioral evidence.
- [7]
  planners:
    - code-grounded
    - sequencing
  theme: AC10's `^---` grep false-positives on YAML frontmatter and Markdown thematic breaks
  why_high_signal:
    Two lenses independently caught that implementing AC10's literal grep would fail a well-formed handoff carrying a section divider, and both converged on the same fix: match unified-diff header SHAPES and forbid `---` rules in the return contract so the literal grep also returns empty. A guard that reddens on correct output trains people to route around it.
- [8]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: The deny set as scoped leaves CLAUDE.md, docs/data-sources.md and docs/decisions/ writable by the agent
  why_high_signal:
    All three noted that blocker F1's four entries (`tests/`, `.github/`, `ops/`, `.claude/`) do not cover the two files the routing rule and the manager/developer seam most depend on the agent not touching. The code-grounded lens wanted the extension baked in; the others flagged it. Raised as a gated decision rather than silently widened, because extending the scope's own list is a scope-growing call.
- [9]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: `.claude/agents/` draws no specialist reviewer; pass `touchedAreas` including `skills` at stage 4
  why_high_signal:
    All three verified `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key and all three independently reached the same no-code-change workaround — pass the areas by hand so `skill-quality` (:199), whose every clause applies verbatim to an agent definition, is on the roster. Decision 7 defers the JS fix, and the file is guarded by `.mjs` scripts CI does not run, so touching it would be a silent-regression risk.
- [10]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: The write-guard package is DETECTION, not prevention, and ADR 0007 must say so plainly
  why_high_signal:
    All three cited the same scar (`implement-plan/SKILL.md:120-125`) and reached the same conclusion: feature branch, pre-spawn snapshot, post-run comparison and `/commit`'s staged-list-then-yes all catch a bad write after the fact and nothing stops it. Two lenses additionally isolated the one genuinely NEW net — the required-clean-tree precondition, without which a human cannot tell the agent's writes from their own in the staged diff.
- [11]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: The faithful-run target is genuinely constrained and must be chosen against a written checklist, not by convenience
  why_high_signal:
    All three enumerated the same exclusions (deny set, `transform/models/` reservation, `src/`+no-pipeline-by-product non-goal, `docs/data-sources.md` routing denial) and all three warned the failure mode is quietly widening the allowlist — the exact F1 hazard. Two independently flagged `tests/fixtures/README.md` as the tempting-but-denied target the scope explicitly says not to absorb. Their two best candidates (a README.md section; a memory-seeding-plus-mis-routed-fact task) combine into one target that satisfies every constraint AND produces the memory delta AC14 needs.
- [12]
  planners:
    - code-grounded
    - sequencing
    - domain-convention
  theme: Memory paths stay inline code, and the epistemic vocabulary disagrees with itself in three places today
  why_high_signal:
    All three grounded the inline-code rule in `tests/test_doc_links.py:56` (only link syntax is scanned) rather than in style, and all three found the same three-way label drift — five in `CLAUDE.md:76-79`, four in `update-docs/SKILL.md:105`, three in `docs/data-sources.md:5-10`. Left unstated in the memory header, a cold implementer silently picks one and creates a fourth variant.
- [13]
  planners:
    - sequencing
    - domain-convention
  theme: A handoff linter shipped before its inputs exist passes vacuously
  why_high_signal:
    Both lenses caught that discovery-by-glob with zero matches is a green test proving nothing — the identical failure `tests/test_doc_links.py:95-104` exists to prevent — and both prescribed the same two-part fix: synthetic controls now, an anti-vacuity coverage assertion once a real artifact lands. The sequencing lens's self-declaring `<!-- handoff: v1 -->` marker additionally makes the linter track-agnostic without a brittle filename glob.
~~~~~

## Adversary findings

~~~~~

-------------------------------------------------------------------------------
[minor] F10 (code-grounded) - Windows/LF is cut from CLAUDE.md but omitted from the list of what the retained pointer must NAME
-------------------------------------------------------------------------------
category: doc-integrity
confidence: medium
id: F10
location: CLAUDE.md:126 (on the cut list per PROJECT_SCOPE.md:444-448) vs the plan's Phase 3 step 3 pointer list
problem:
  Phase 3 deletes CLAUDE.md:126 ("Windows dev, Linux CI. `.gitattributes` normalizes to LF"), but the pointer the plan specifies names only resolve-by-name, immutable landing zone, bronze 1:1, silver grain, facts MERGE, era boundaries, layer promotion, pacing and affiliation-as-of-game-date. Windows/LF is the one relocated clause that is NOT data-engineering-specific: it governs every file written in this repo, and the main thread is the ONLY actor permitted to write in `tests/`, `.github/` and `ops/` — the three denied paths where line-ending and PS-5.1 UTF-8 mangling (implement-plan/SKILL.md:111-112) actually bite. After the cut it survives only in the agent definition and in a stage-4 skill the main thread reads at implement time.
proposed_fix:
  Either keep CLAUDE.md:126 in place (it is one line, and the budget has ~78 lines of headroom) or add it explicitly to the pointer's named list. Have the Phase 2 clause-presence guard assert it in the definition either way, and call it out in Phase 3's prose re-read step as a specific thing to judge.
reviewer: code-grounded
severity: minor
title: Windows/LF is cut from CLAUDE.md but omitted from the list of what the retained pointer must NAME

-------------------------------------------------------------------------------
[minor] F9 (code-grounded) - Phase 4's faithful-run target is underspecified against README.md's actual shape, and as written leaves README internally inconsistent
-------------------------------------------------------------------------------
category: spec-clarity
confidence: high
id: F9
location: README.md:69-80 (the `## Repo layout` fenced block) vs the plan's Phase 4 step 1 and gated decision 2
problem:
  The plan grounds the target only as "README.md is 117 lines and mentions neither `.claude` nor 'skill'" (both verified) and asks the agent for "a short (~15 line) section describing `.claude/agents/` and the spawn protocol". Verified, the real gap is structural: README.md:69-80 is a `Repo layout` tree that lists docs/ requests/ src/ transform/ ops/ tests/ var/ and omits `.claude/` ENTIRELY. A spec that asks only for a new `.claude/agents/` section produces a README that documents the agents directory while still not documenting the skills directory that has existed since Phase 0 — a doc-drift outcome `/update-docs` should flag in the very same PR, on a diff whose whole purpose is to be reviewed as exemplary agent output.
proposed_fix:
  Name the target precisely in the spec handed to the agent: add `.claude/skills/` and `.claude/agents/` rows to the fenced layout block at README.md:69-80 (fenced, so exempt from tests/test_doc_links.py:69 link-checking) plus a short prose paragraph on the spawn protocol. Keep the deliberately mis-routed data fact as the second half of the task, unchanged.
reviewer: code-grounded
severity: minor
title: Phase 4's faithful-run target is underspecified against README.md's actual shape, and as written leaves README internally inconsistent

-------------------------------------------------------------------------------
[minor] F8 (code-grounded) - The pre/post snapshot protocol is attributed as "verbatim" from implement-plan/SKILL.md, but two of its five commands are not there
-------------------------------------------------------------------------------
category: citation-fidelity
confidence: high
id: F8
location: .claude/skills/implement-plan/SKILL.md:120-125 and :187-190 vs the plan's Phase 4/5 steps and testing section
problem:
  The plan repeatedly says the snapshot is "stage 4's exact procedure reused verbatim (`implement-plan/SKILL.md:120-125`, `:187-190`)" and enumerates `git status --porcelain` + `git diff HEAD --stat` + untracked list + `git rev-parse HEAD` + `git stash list` + a patch to `var/tmp/`. Verified, :120-125 prescribes only "write the diff to gitignored scratch — `git diff HEAD > var/tmp/<slug>-pre-review.patch` and record any untracked files", and :187-190 prescribes only re-checking `git status` against the snapshot plus a symbol grep. `git rev-parse HEAD` and `git stash list` appear nowhere in the skill; they come from AC12 at PROJECT_SCOPE.md:149. The commands are good additions — the attribution is wrong, and a cold implementer who opens :120-125 to "reproduce it verbatim" into `.claude/agents/README.md` will produce a shorter protocol than the plan's acceptance requires.
proposed_fix:
  Attribute correctly: two commands from implement-plan/SKILL.md:120-125 and :187-190, plus HEAD and stash-list capture required by AC12 (PROJECT_SCOPE.md:149). State the five-command list once, canonically, in `.claude/agents/README.md` and have Phases 4-5 point at it rather than at the skill.
reviewer: code-grounded
severity: minor
title: The pre/post snapshot protocol is attributed as "verbatim" from implement-plan/SKILL.md, but two of its five commands are not there

-------------------------------------------------------------------------------
[minor] F11 (code-grounded) - The recommended stage-4 `touchedAreas` pulls in a mismatched specialist and one unearned lens
-------------------------------------------------------------------------------
category: efficiency
confidence: high
id: F11
location:
  .claude/skills/implement-plan/acceptance_panel.js:203-204 vs the plan's Phase 6 final step ("pass `touchedAreas` explicitly including `skills`, `tests`, `docs` and `config`")
problem:
  Verified at :203: `tests: ['extraction']`. Passing `tests` spins up the EXTRACTION specialist (:198), whose entire mandate is landing-zone immutability, 0.6s pacing, backfill resumability, bulk-first endpoints, payload provenance and live-API tests — none of which this change touches, since it lands no extraction code by design (PROJECT_SCOPE.md:110). That reviewer can only produce noise or invented findings on this diff. Separately, `config` maps to `infra-cost` (:204) but no config file (`pyproject.toml`, `dbt_project.yml`, `profiles.yml`) appears anywhere in the plan's files_to_touch, so that lens is unearned too. Also worth flagging for the run: the `skill-quality` mandate at :199 clause 3 checks registration in CLAUDE.md's "How to Help" section, and this plan adds only a project-map row and a rulebook pointer.
proposed_fix:
  Recommend `touchedAreas: ["skills","docs"]` as the default for this change (which is what actually yields `skill-quality`), and note that `tests` and `config` should be added only if the implementer deliberately wants the extraction / infra-cost lenses. Add a line to Phase 3 deciding whether the agent gets a "How to Help" mention in CLAUDE.md, so :199 clause 3 has a defined answer.
reviewer: code-grounded
severity: minor
title: The recommended stage-4 `touchedAreas` pulls in a mismatched specialist and one unearned lens

-------------------------------------------------------------------------------
[minor] F14 (code-grounded) - Phase 0's sentinel probe should be pinned to the SAME spawn surface Phases 4-5 will use
-------------------------------------------------------------------------------
category: gate-validity
confidence: medium
id: F14
location: Plan Phase 0 steps 3-4 (`claude --help` / `claude agents --help`, then "spawn by that agent type using whatever surface the harness exposes")
problem:
  The blocking gate's validity rests entirely on the sentinel round-trip, and the plan's step 3 leads with CLI introspection. Verified, `claude` resolves on this machine (<user-profile>\AppData\Roaming\npm\claude.ps1), so those commands will run and produce output — but a CLI that advertises an agents surface does not establish that the IN-SESSION spawn path Phases 4-5 use can name a project agent. The repo's only demonstrated spawn mechanism is inside the panel scripts (scope_panel.js:174, verified to take `{label, phase, schema, effort}` and no agent type), which is exactly the ambiguity Phase 0 exists to remove. A PROCEED verdict earned from the CLI alone would leave the dead-artifact risk (PROJECT_SCOPE.md:277) live while blocker A2-02's STOP rule reads as satisfied.
proposed_fix:
  Make it explicit in step 4: the sentinel round-trip MUST be performed from the same spawn surface the proving runs will use (main-thread subagent spawn), and the probe artifact must record that surface by name. CLI output is corroborating evidence, not the verdict. If the sentinel cannot be round-tripped from that surface, the verdict is STOP even if the CLI advertises agents.
reviewer: code-grounded
severity: minor
title: Phase 0's sentinel probe should be pinned to the SAME spawn surface Phases 4-5 will use

-------------------------------------------------------------------------------
[nit] F13 (code-grounded) - Two small miscounts in the onboarding/architecture prose
-------------------------------------------------------------------------------
category: accuracy
confidence: high
id: F13
location: tests/test_repo_structure.py:45,51,62,69,77,87 (six test functions) and .claude/skills/commit/SKILL.md:86-92 (seven bullets)
problem:
  The architecture map says `tests/test_repo_structure.py` holds "7 tests"; it holds SIX test functions (:45, :51, :62, :69, :77, :87) — `uv run pytest -q` reports 8 total across both modules, which is likely where the number came from. Separately, the plan cites "the six triggers for the full `/update-docs` sweep" at commit/SKILL.md:83-93; the list is SEVEN bullets spanning :86-92 (section :83-92), and the plan then says "this change hits four" in two places. Neither slip is load-bearing, but the whole point of this stage is that a cold implementer trusts these literally.
proposed_fix:
  Say six tests in `tests/test_repo_structure.py` (eight in the suite), and seven triggers at commit/SKILL.md:86-92. Re-check the "hits four" claim against the corrected list: a new/changed directory, a new convention, an advanced request status, and a new ADR contradicting nothing — state which four.
reviewer: code-grounded
severity: nit
title: Two small miscounts in the onboarding/architecture prose

-------------------------------------------------------------------------------
[nit] F12 (code-grounded) - Phase 1 acceptance conflates tracked Markdown count with the link checker's scanned count
-------------------------------------------------------------------------------
category: accuracy
confidence: high
id: F12
location:
  tests/test_doc_links.py:60-65 (`_scanned_files()` walks the filesystem via rglob) vs the plan's Phase 1 acceptance ("the scanned count has risen from 33 toward 36")
problem:
  33 is the count of TRACKED `.md` files (`git ls-files '*.md'`, measured). `_scanned_files()` at :60-65 rglobs the working tree and filters only by `EXCLUDED_PARTS`, so it already counts the two untracked stage-3 review files and will count IMPLEMENTATION_PLAN.md too. The stated before/after numbers will not match what a cold implementer observes, and a mismatched number against a test that reports only pass/fail invites a pointless investigation.
proposed_fix:
  Assert what the test actually asserts: `uv run pytest tests/test_doc_links.py -q` green, with the scanned set comfortably above `MIN_EXPECTED_FILES = 20` (:53) and both `MUST_COVER` entries present (:52). Drop the specific 33→36 figure or label it 'tracked files, informational'.
reviewer: code-grounded
severity: nit
title: Phase 1 acceptance conflates tracked Markdown count with the link checker's scanned count

-------------------------------------------------------------------------------
[major] F3 (code-grounded) - No defined behavior when the memory file reaches its 120-line cap — Phase 4 can go red with no prescribed remedy
-------------------------------------------------------------------------------
category: completeness
confidence: medium
id: F3
location:
  Plan Phase 1 step 9 (memory header) and Phase 4 acceptance ("a REAL budget-guard failure, not a reason to raise the cap"); risk named at requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md:297
problem:
  Decision 5 sets a hard 120-line cap enforced in pytest, curation is explicitly deferred (PROJECT_SCOPE.md:96), and the plan's Phase 4 acceptance forbids raising the cap when the agent's own memory delta breaches it. But the definition's body checklist (Phase 1, eleven items) never states what the agent does when the file is at cap, and the memory header spec (Phase 1 step 9) states only the cap and its counting rule. The scope names this exact hazard at :297 ("a cap reached with no pruning rule turns into either an arbitrary truncation or a quietly raised cap") and the plan's risk list drops it. A write-capable agent hitting a hard assertion with no rule will do the worst available thing: silently delete an older entry, or silently skip recording what it learned.
proposed_fix:
  Add one clause to the definition and mirror it in the memory header: at cap, the agent APPENDS NOTHING and instead reports the entry plus 'memory at cap, pruning needed' under `still-open`/`docs-delta` in its handoff; pruning is a main-thread decision, never the agent's. Add a matching risk bullet, and have the Phase 2 memory-budget guard's assertion message name that rule so a red check says what to do.
reviewer: code-grounded
severity: major
title: No defined behavior when the memory file reaches its 120-line cap — Phase 4 can go red with no prescribed remedy

-------------------------------------------------------------------------------
[major] F2 (code-grounded) - Adding `agents` to the touched-area bucket list creates a bucket that silently routes to NO specialist reviewer
-------------------------------------------------------------------------------
category: silent-regression
confidence: high
id: F2
location:
  .claude/skills/implement-plan/acceptance_panel.js:207 (`AREAS.flatMap(a => AREA_TO_SPEC[a] || [])`) vs the Phase 3 edit to .claude/skills/implement-plan/SKILL.md:127-132
problem:
  Phase 3 adds `agents` to the bucket lists at implement-plan/SKILL.md:127-132 and update-docs/SKILL.md:47-48 while Decision 7 deliberately leaves `AREA_TO_SPEC` (acceptance_panel.js:202-206) without an `agents` key — verified: the key is absent and line 207 resolves an unknown area to `[]` with no error and no warning. The net effect is worse than the status quo: today a stage-4 agent touching `.claude/agents/` has no bucket and might reasonably pick `skills` (annotated `skills` (`.claude/skills/`)); after this edit the doc tells it to pick `agents`, which spins up zero specialists and drops the `skill-quality` lens (:199) whose every clause the plan itself says applies verbatim to an agent definition. The plan carries the workaround only as a one-off runtime note for THIS change (Phase 6), so every future change to the definition inherits the trap.
proposed_fix:
  Write the bucket-list entry so it carries its own workaround, e.g. `agents` (`.claude/agents/` — `AREA_TO_SPEC` has no `agents` key yet, so ALSO pass `skills` to get the `skill-quality` lens). Add the same sentence to update-docs/SKILL.md:47-48. Restate it in ADR 0007's Consequences as a known open edge until the sequel lands the JS half.
reviewer: code-grounded
severity: major
title: Adding `agents` to the touched-area bucket list creates a bucket that silently routes to NO specialist reviewer

-------------------------------------------------------------------------------
[major] F1 (code-grounded) - Phase 5 acceptance uses Unix `find` on a PowerShell-only box — the check passes vacuously
-------------------------------------------------------------------------------
category: vacuous-check
confidence: high
id: F1
location: Plan Phase 5 steps + acceptance ("`find transform/models -name '*.sql'` returns nothing"); grounded against .github/workflows/ci.yml:81 and CLAUDE.md:126
problem:
  `find transform/models -name '*.sql' -print -quit` is legitimate at ci.yml:81 because that job runs on `ubuntu-latest`. The plan lifts it into a LOCAL phase-acceptance check, but this repo is Windows dev (CLAUDE.md:126) with PowerShell 5.1 as the only shell. Windows `FIND.EXE` takes a search string, not `-name`: the invocation errors ("FIND: Parameter format not correct") and writes NOTHING to stdout. A cold implementer following the literal criterion "returns nothing" reads that empty stdout as a PASS. This is precisely the pass-vacuously failure mode the plan builds negative controls to prevent (tests/test_doc_links.py:95-104), reintroduced as an acceptance criterion for the non-goal at PROJECT_SCOPE.md:110.
proposed_fix:
  Replace both occurrences with a PowerShell form and make emptiness explicit, e.g. `@(Get-ChildItem transform/models -Recurse -Filter *.sql).Count` must be 0, or `git ls-files 'transform/models/**/*.sql'` (which also catches a staged stray). Keep `git status --porcelain transform/ src/` as the primary check and mark the .sql sweep as the redundancy. Audit the rest of the plan for the same class: `grep` is likewise unavailable as a binary here — say `Select-String` or the Grep tool where Phases 1/3/4/5 prescribe greps.
reviewer: code-grounded
severity: major
title: Phase 5 acceptance uses Unix `find` on a PowerShell-only box — the check passes vacuously

-------------------------------------------------------------------------------
[minor] F4 (code-grounded) - The AC13 routing-rule guard passes vacuously — the relocated pacing bullet already puts `docs/data-sources.md` in the definition
-------------------------------------------------------------------------------
category: vacuous-check
confidence: high
id: F4
location: CLAUDE.md:109 (the moved bullet's link to `docs/data-sources.md`) vs the Phase 2 guard spec "the literal string `docs/data-sources.md` in the routing rule"
problem:
  Phase 1 relocates CLAUDE.md:107-109 into the definition, and that bullet ends with a link to `docs/data-sources.md` (re-depthed to `../../docs/data-sources.md`). Phase 2's routing guard and Phase 1's acceptance both assert presence of the literal string `docs/data-sources.md` in the definition. That string is therefore present whether or not the routing rule exists at all, so the guard for AC13 — one of only two guards protecting the memory-vs-docs seam the scope calls the drift hole (PROJECT_SCOPE.md:291) — cannot fail for the reason it is meant to catch. A naive negative control (strip the routing rule) will still pass unless it also strips the pacing bullet.
proposed_fix:
  Assert a routing-specific phrase, not a bare path: e.g. the definition must contain a line matching both `docs-delta` and `docs/data-sources.md` within the same clause, or a stable `## Routing` heading whose body names the file. Build the negative control from a synthetic definition that KEEPS the pacing bullet and DROPS the routing rule, and say so in the test docstring.
reviewer: code-grounded
severity: minor
title: The AC13 routing-rule guard passes vacuously — the relocated pacing bullet already puts `docs/data-sources.md` in the definition

-------------------------------------------------------------------------------
[minor] F7 (code-grounded) - Phase 0's acceptance claims a tree state that is already false — the stage-3 panel trail is untracked right now
-------------------------------------------------------------------------------
category: correctness
confidence: high
id: F7
location: Plan Phase 0 steps 1-2 and acceptance ("`git status --porcelain` shows only `reviews/harness-probe.md` as new")
problem:
  Measured on this branch right now: `git status --porcelain` is NOT clean — it lists `?? requests/feature-requests/data-engineer-agent/reviews/plan-adversarial.md` and `?? .../reviews/plan-proposals.md`, the stage-3 panel trail, and `IMPLEMENTATION_PLAN.md` will join them. Phase 0 instructs the implementer to confirm the tree is clean as the probe's control and then asserts only one new path at the end. A cold implementer meeting an unexpected dirty tree at step 1 of a BLOCKING gate either stalls or — the dangerous branch — reaches for a destructive git verb to reach the state the plan describes, which CLAUDE.md:73-75 forbids and implement-plan/SKILL.md:123-125 records a scar for.
proposed_fix:
  Reword the precondition to "clean apart from this request's own stage-3 artifacts (IMPLEMENTATION_PLAN.md and reviews/plan-*.md)" and the acceptance to "no new or modified path outside `requests/feature-requests/data-engineer-agent/`". Add an explicit line: never clean, checkout, restore, or stash to reach the described state — bubble it up instead.
reviewer: code-grounded
severity: minor
title: Phase 0's acceptance claims a tree state that is already false — the stage-3 panel trail is untracked right now

-------------------------------------------------------------------------------
[minor] F6 (code-grounded) - The plan misquotes CI's own commands, so the prescribed local gate is not the CI gate
-------------------------------------------------------------------------------
category: accuracy
confidence: high
id: F6
location: .github/workflows/ci.yml:42 and :53 vs the plan's testing section ("the four commands CI's `Lint, types, tests` job runs (`ci.yml:41-53`)")
problem:
  The plan states as fact that CI runs `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run pytest -q`. Verified, ci.yml:42 is `uv run ruff check --output-format=github` and ci.yml:53 is `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing`. Today the two are equivalent (no `network`-marked tests exist and coverage has no threshold), but the plan is the cold implementer's only description of the gate, and it teaches a marker-blind pytest invocation in a repo that maintains a `network` marker at pyproject.toml:80-82 precisely to keep live API calls out of CI.
proposed_fix:
  Quote ci.yml:41-53 verbatim in the testing section, and prescribe `uv run pytest -m "not network" -q` as the standing local gate so local selection and CI selection cannot diverge. `-q` is already default via `addopts` at pyproject.toml:79, so note that too.
reviewer: code-grounded
severity: minor
title: The plan misquotes CI's own commands, so the prescribed local gate is not the CI gate

-------------------------------------------------------------------------------
[minor] F5 (code-grounded) - The status-vocabulary decision is incomplete: two skills say the Index cell reads `plan`, not `planned`
-------------------------------------------------------------------------------
category: bookkeeping
confidence: high
id: F5
location: .claude/skills/create-implementation-plan/SKILL.md:170-172 and .claude/skills/implement-plan/SKILL.md:58-59 vs the plan's Decision 14 and Phase 6 step 4
problem:
  The plan's Decision 14 states the split is clean — "Both are satisfied; neither is invented" — citing requests/feature-requests/README.md:85 for `planned`. Verified, that is only two of three sources. create-implementation-plan/SKILL.md:172 instructs literally: "set this item's Index row Stage cell to `plan`", and implement-plan/SKILL.md:58-59 locates work by checking the Index "for an item at the `plan` stage". Writing `planned` at end of stage 3 therefore diverges from the skill that writes it and from the skill that reads it, and the current Index rows (README.md:91-92: `intake`, `scoped`) offer no precedent either way. AC16 makes this greppable, so the mismatch will surface at the acceptance panel as a real ledger row.
proposed_fix:
  Name all THREE sources in the decision and pick explicitly. Recommended: use `plan` in the Index at end of stage 3 (matching the skill that writes it and the skill that reads it) and `implemented` at end of stage 4 (where README.md:85 and implement-plan/SKILL.md:229 agree), and record the README grammar divergence as a doc-drift item for `/update-docs` rather than resolving it silently in this change.
reviewer: code-grounded
severity: minor
title: The status-vocabulary decision is incomplete: two skills say the Index cell reads `plan`, not `planned`

-------------------------------------------------------------------------------
[minor] A2-EX-13 (executability) - Phase 4's diff-scope acceptance uses a command that cannot see the artifact the phase is supposed to produce
-------------------------------------------------------------------------------
category: acceptance-contract
confidence: high
id: A2-EX-13
location: plan Phase 4 acceptance item 4 (git diff HEAD --stat shows only the spec's target file plus, at most, the memory file)
problem:
  The agent's own handoff, requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md, is a NEW file. `git diff HEAD --stat` does not list untracked files, so this criterion neither confirms the handoff was written nor detects a stray new file created outside the allowlist — which is precisely what AC12 (PROJECT_SCOPE.md:149) asks the comparison to catch. As written the criterion is satisfiable by an agent that wrote nothing at all.
proposed_fix:
  Pair it with `git status --porcelain` and enumerate the expected set explicitly: modified = the spec's target file (plus optionally .claude/agents/data-engineer-memory.md); untracked = exactly requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md. Anything else in either list is an allowlist breach and a FAIL.
reviewer: executability
severity: minor
title: Phase 4's diff-scope acceptance uses a command that cannot see the artifact the phase is supposed to produce

-------------------------------------------------------------------------------
[minor] A2-EX-14 (executability) - The stated local gate does not match what CI actually runs
-------------------------------------------------------------------------------
category: environment
confidence: high
id: A2-EX-14
location: plan testing section ('the four commands CI's Lint, types, tests job runs, ci.yml:41-53'); grounds against .github/workflows/ci.yml:42-53 and pyproject.toml:79
problem:
  CI's four steps are `uv run ruff check --output-format=github`, `uv run ruff format --check`, `uv run mypy`, and `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` (ci.yml:42-53). The plan prescribes `uv run pytest -q` and calls it the same command. It is not: the `-m "not network"` selector and coverage reporting are absent, and `-q` is already in addopts at pyproject.toml:79 so it adds nothing. For a plan whose whole cadence is 'green locally, then /commit', a local gate differing from the required check is the local-green/CI-red asymmetry the scope worries about at PROJECT_SCOPE.md:295, mirrored.
proposed_fix:
  State the local gate as `uv run pytest -m "not network"` (drop the redundant -q) and note that the coverage flags are CI-only. If any new guard would ever need the network marker, say so; none does today.
reviewer: executability
severity: minor
title: The stated local gate does not match what CI actually runs

-------------------------------------------------------------------------------
[major] A2-EX-11 (executability) - The recommended hard keyword denylist will redden against the memory header the plan itself tells the implementer to write
-------------------------------------------------------------------------------
category: correctness
confidence: medium
id: A2-EX-11
location:
  plan gated_decisions[8] (a narrow curated denylist as an ordinary assertion, including 'rate limit' and '2013-14') vs Phase 1 step 9 and Phase 1 acceptance item 4
problem:
  Phase 1 step 9 requires the memory file's HEADER to state 'what routes elsewhere (docs/data-sources.md for data facts, ...)', and the definition's routing rule names era/endpoint/availability/rate-limit facts. Gated decision 9 then recommends a hard pytest assertion that the memory file contains none of 'rate limit', '2013-14', or season-range strings. The header describing the routing rule trips that assertion on the very commit that lands it. Phase 1's own acceptance handles the same file differently — 'grep it ... and confirm every hit is an ergonomics claim', i.e. human judgment — so the mechanical guard and the plan's self-check disagree about one file. Decision 9 in the scope (PROJECT_SCOPE.md:417-419) says warning-shaped, never a hard CI gate, precisely because of this false-positive class.
proposed_fix:
  Scope the guard to ENTRY lines only: parse the memory file into header block + entries (the plan already defines a per-entry format with a date and an epistemic label, so entries are identifiable) and run the denylist over entries alone. State that scoping in the test docstring and name the header exemption in the assertion message so a future reader does not 'fix' it by widening. Align Phase 1's acceptance grep to the same entries-only scope.
reviewer: executability
severity: major
title: The recommended hard keyword denylist will redden against the memory header the plan itself tells the implementer to write

-------------------------------------------------------------------------------
[minor] A2-EX-12 (executability) - Phases 4-5 require a clean tree AND prescribe a git diff HEAD snapshot that is therefore always empty
-------------------------------------------------------------------------------
category: sequencing
confidence: high
id: A2-EX-12
location: plan Phase 4 step 2 and Phase 5 step 4; protocol copied from .claude/skills/implement-plan/SKILL.md:120-125
problem:
  The plan copies stage 4's snapshot protocol verbatim, which is the right instinct (PROJECT_SCOPE.md:80 asks for exactly that, 'rather than inventing a second mechanism'). But stage 4's protocol exists because at Step 4 the implementation 'sits UNCOMMITTED in the working tree' (acceptance_panel.js:165) — the patch is the belt because there is uncommitted work to lose. Here every phase ends at a /commit checkpoint and Phase 4 explicitly preconditions on a clean tree, so git diff HEAD produces zero bytes and the headline safety net protects nothing. The genuine protections in this context are the recorded git rev-parse HEAD, the untracked-file list, and git stash list.
proposed_fix:
  Reorder the snapshot step to lead with git rev-parse HEAD, the untracked list, and git stash list as the load-bearing captures, and keep the patch with an explicit note that on a clean tree it is EXPECTED to be empty and serves only as a tripwire if the precondition was violated. In the post-run comparison, make 'HEAD unchanged' the primary check — it is what actually catches the recorded scar at implement-plan/SKILL.md:123-125.
reviewer: executability
severity: minor
title: Phases 4-5 require a clean tree AND prescribe a git diff HEAD snapshot that is therefore always empty

-------------------------------------------------------------------------------
[minor] A2-EX-15 (executability) - Handing README.md to the unproven agent makes the feature's public documentation the output of its own first proving run
-------------------------------------------------------------------------------
category: sequencing
confidence: medium
id: A2-EX-15
location: plan gated_decisions[1] and the files_to_touch entry for README.md
problem:
  The recommended faithful-run target is genuinely well-chosen — measured, README.md is 117 lines and Select-String for '.claude' / 'skill' returns zero hits, so the gap is real, it is outside the deny set, and it lands no pipeline code. But it means the repo's only public description of .claude/agents/ and the spawn protocol is authored by the builder whose reliability the run exists to test, on its first ever run, while update-docs/SKILL.md:80-86 audits README.md's status/roadmap/architecture on every sweep. If the run produces weak prose the feature ships weak docs; if the main thread rewrites it, the proving-run diff is no longer the agent's.
proposed_fix:
  Keep the target but separate the claims: the acceptance criterion is that a real, small, in-allowlist DIFF was produced and passed /commit review (AC12/AC14), not that the prose is final. Add an explicit Phase 6 step — at /update-docs the main thread reads and, if needed, rewrites the agent-authored README section — and require reviews/proving-run-a.md to record the agent's original text verbatim so the evidence survives the edit.
reviewer: executability
severity: minor
title: Handing README.md to the unproven agent makes the feature's public documentation the output of its own first proving run

-------------------------------------------------------------------------------
[nit] A2-EX-18 (executability) - Phase 0's probe invokes an undocumented claude agents subcommand with no fallback
-------------------------------------------------------------------------------
category: executability
confidence: medium
id: A2-EX-18
location: plan Phase 0 step 3 (claude --help and claude agents --help)
problem:
  Verified: `claude` is on PATH here (<user-profile>\AppData\Roaming\npm\claude.ps1), so `claude --help` will run. But `claude agents` is a guess — there is no evidence in this repo that such a subcommand exists, and the shell runs -NonInteractive with stdin at the null device, so an unrecognized subcommand that falls through to a session launch reads EOF or hangs to the timeout. Losing the probe's budget on a guessed subcommand is a poor way to spend the plan's only blocking gate.
proposed_fix:
  Run `claude --version` and `claude --help` only, quote both verbatim into reviews/harness-probe.md, and derive any further subcommand from the help output rather than guessing. If nothing agent-related appears in help, record that and fall through to the loader probe (step 4) — absence from help text is not itself a STOP finding.
reviewer: executability
severity: nit
title: Phase 0's probe invokes an undocumented claude agents subcommand with no fallback

-------------------------------------------------------------------------------
[nit] A2-EX-19 (executability) - Three small citation slips in the onboarding, architecture-map and code-references sections
-------------------------------------------------------------------------------
category: grounding
confidence: high
id: A2-EX-19
location: plan onboarding entry for tests/test_repo_structure.py; architecture_map section 5; code_references entry for .claude/skills/commit/SKILL.md:83-93
problem:
  Measured corrections, in a plan whose own standard is that 'a wrong citation is worse than none': (1) tests/test_repo_structure.py holds SIX test functions, not seven — `uv run pytest -q` reports 8 passed across both modules, with test_doc_links.py contributing 2. (2) `var` sits at tests/test_doc_links.py:37, not :38; line 38 is 'target'. (3) commit/SKILL.md:83-93 is described as 'six triggers' — the bulleted list at :86-92 has seven items (the claim that this change hits four is unaffected). None changes a decision, but each is the kind of literal a cold agent copies into an assertion message.
proposed_fix:
  Correct all three inline. While in architecture_map section 5, also add that EXCLUDED_PARTS contains `dbt_packages` (tests/test_doc_links.py:39) — independent confirmation that the drill's scratch tree stays invisible to the link checker even if the packages workaround changes.
reviewer: executability
severity: nit
title: Three small citation slips in the onboarding, architecture-map and code-references sections

-------------------------------------------------------------------------------
[question] A2-EX-16 (executability) - Relocating the pacing and affiliation warnings removes them from the file every scoping and planning panel is told to read
-------------------------------------------------------------------------------
category: risk
confidence: high
id: A2-EX-16
location:
  plan Phase 3 step 2 (cutting CLAUDE.md:107-109 and :113-116); grounds against .claude/skills/scope-feature/scope_panel.js:124 and .claude/skills/create-implementation-plan/plan_panel.js:146
problem:
  Both panel mandates instruct their agents to read CLAUDE.md for 'resolve BY NAME ... landing zone IMMUTABLE ... bronze 1:1 ... silver declares its grain AND proves it ... facts MERGE on key ... tracking columns structurally absent before 2013-14 ... commits go through /commit only' (scope_panel.js:124, plan_panel.js:146 — both read). Neither mentions the 0.6s pacing default or that player affiliation resolves as-of the game date. After Phase 3's cut, a stage-2 scoper or stage-3 planner working on box-score-foundation — whose whole job is extraction cost (~50 calls vs ~60,000) and SCD2 affiliation — no longer encounters CLAUDE.md:113-116, the repo's self-declared 'most likely source of silently wrong joins in this project', unless it follows a pointer into a document addressed to a different actor. The plan flags the risk, but its mitigation (a pointer plus the stage-4 net at acceptance_panel.js:192 and :197) only covers stage 4 — downstream of the decisions those warnings shape.
proposed_fix:
  Put to the user as a gated call: keep ONE compressed line of the affiliation warning in CLAUDE.md's Key Context (:52-59), already the domain-facts section and already holding the era boundaries, and move only the build mechanics (SCD2 implementation, as-of-game-date join construction) into the definition. Pacing reads the same way — a cost/constraint fact the scoper needs, not a build mechanic. If the user declines, ADR 0007's Consequences must name this specific loss rather than the generic 'a bad cut degrades every future session'.
reviewer: executability
severity: question
title: Relocating the pacing and affiliation warnings removes them from the file every scoping and planning panel is told to read

-------------------------------------------------------------------------------
[minor] A2-EX-17 (executability) - Passing touchedAreas including tests at stage 4 summons the extraction specialist, whose entire mandate is irrelevant here
-------------------------------------------------------------------------------
category: review-coverage
confidence: high
id: A2-EX-17
location: plan Phase 6 final step; grounds against .claude/skills/implement-plan/acceptance_panel.js:203 and :198
problem:
  AREA_TO_SPEC at line 203 maps `tests: ['extraction']`. The extraction specialist (:198) reviews landing-zone immutability, 0.6s pacing, backfill resumability, bulk-endpoint choice, payload provenance, and fixture-vs-live tests — none of which exist in this change, which lands no extraction code by non-goal (PROJECT_SCOPE.md:110; verified, src/nba_platform/ is one __init__.py). Spending a reviewer slot on a lens with nothing to review dilutes the panel and invites invented findings, which the correctness mandate at :192 explicitly warns against ('Do not invent bugs to pad').
proposed_fix:
  Pass touchedAreas: ["skills", "docs", "config"]. `skills` draws skill-quality (:199), the lens that actually applies to an agent definition; `config` draws infra-cost (:200), the right lens for a committed free-text memory file in a public repo (its clause 1 is the secrets check). Drop `tests` — the four core reviewers already cover the guard suite, and edgecases (:193) explicitly reads tests for whether they assert anything.
reviewer: executability
severity: minor
title: Passing touchedAreas including tests at stage 4 summons the extraction specialist, whose entire mandate is irrelevant here

-------------------------------------------------------------------------------
[major] A2-EX-10 (executability) - The plan-vs-planned Index vocabulary conflict is asserted as settled but is live, and the Index advance is placed in the wrong stage
-------------------------------------------------------------------------------
category: sequencing
confidence: high
id: A2-EX-10
location:
  plan decisions[14] and Phase 6 step 4; grounds against .claude/skills/create-implementation-plan/SKILL.md:170-173, .claude/skills/implement-plan/SKILL.md:59 and :227-229, requests/feature-requests/README.md:85 and :92
problem:
  decisions[14] claims 'Both are satisfied; neither is invented', citing requests/feature-requests/README.md:85 for the grammar intake -> scoped -> planned -> implemented. But the two skills that actually write the cell disagree: create-implementation-plan/SKILL.md:172 says 'set this item's Index row Stage cell to `plan`' (not `planned`), and implement-plan/SKILL.md:59 looks for 'an item at the `plan` stage'. The repo genuinely disagrees with itself and the plan silently picks a side while asserting there is no conflict. Separately, the Index advance to planned/plan is STAGE-3 work — it happens when this plan is written, per create-implementation-plan/SKILL.md:170-173 — yet it appears as a Phase 6 step of stage-4 implementation, where implement-plan/SKILL.md:227-229 requires the cell to read `implemented`. A literal reader of Phase 6 could set the row backwards.
proposed_fix:
  Phase 6 sets the Index row (currently `scoped`, README.md:92) to `implemented` and nothing else. Move the planned/plan advance out of the phase list into a one-line note that it is stage-3 bookkeeping already done. Surface the conflict rather than resolving it silently: state that README.md:85 says `planned` while create-implementation-plan/SKILL.md:172 says `plan`, recommend `planned` (the track README is authoritative for its own grammar per CLAUDE.md:45-46), and flag the skill wording as a one-line fix for a future request.
reviewer: executability
severity: major
title: The plan-vs-planned Index vocabulary conflict is asserted as settled but is live, and the Index advance is placed in the wrong stage

-------------------------------------------------------------------------------
[major] A2-EX-03 (executability) - Decision 7's doc-half-only split makes stage-4 review coverage strictly WORSE than today, not merely unchanged
-------------------------------------------------------------------------------
category: correctness
confidence: high
id: A2-EX-03
location: .claude/skills/implement-plan/acceptance_panel.js:202-207 vs plan Phase 3 step 6 and the files_to_touch entry for acceptance_panel.js
problem:
  The plan adds an `agents` entry to the bucket lists at implement-plan/SKILL.md:127-132 and update-docs/SKILL.md:47-48 while leaving AREA_TO_SPEC untouched. AREA_TO_SPEC (acceptance_panel.js:202-206) maps transform|src|tests|skills|infra|ci|config|orchestration|docs and has no `agents` key, and line 207 is `const specKeys = [...new Set(AREAS.flatMap(a => AREA_TO_SPEC[a] || []))]`. So a future implementer who honestly buckets a .claude/agents/ change as `agents` — exactly what the new bucket-list entry teaches — gets `undefined || []` and NO specialist reviewer at all. Today, with no `agents` bucket, that implementer buckets it under `skills` (the only .claude/ entry) and draws the skill-quality specialist at :199, whose every clause (frontmatter validity, description drift, progressive disclosure, read-only-git/never-commit conventions, link resolution) applies verbatim to an agent definition. The doc half as written entrenches the blind spot the plan's own risk list names.
proposed_fix:
  Either (a) add the one-line key `agents: ['skill-quality'],` to AREA_TO_SPEC in the same Phase 3 commit and run both bundled guards by hand — `node .claude/skills/implement-plan/tests/merge_fallback_guard.mjs` and `node .claude/skills/implement-plan/tests/verify_batching_guard.mjs`, exit 0 each (self-verification instruction at implement-plan/SKILL.md:271-273) — which stays inside Decision 7's spirit because it changes no build step; or (b) if the deferral is kept, write the bucket-list entries as 'agents (.claude/agents/) — pass as `skills` until AREA_TO_SPEC gains an agents key' so the routing gap cannot be triggered by following the doc.
reviewer: executability
severity: major
title: Decision 7's doc-half-only split makes stage-4 review coverage strictly WORSE than today, not merely unchanged

-------------------------------------------------------------------------------
[major] A2-EX-04 (executability) - The plan contradicts itself four ways about which phase gets the handoff linter's anti-vacuity coverage assertion
-------------------------------------------------------------------------------
category: sequencing
confidence: high
id: A2-EX-04
location: plan Phase 2 step 9 vs Phase 4 step 7 vs architecture_map section 9 vs decisions[4]
problem:
  Four statements disagree. Phase 2 step 9: 'Leave a TODO naming Phase 5 as where the anti-vacuity coverage assertion lands'. Phase 4 step 7: 'Add the anti-vacuity coverage assertion to tests/test_handoff_contract.py' (Phase 4's acceptance asserts it too). architecture_map section 9: 'gains its anti-vacuity coverage assertion in Phase 5 once real artifacts exist'. decisions[4]: 'gains its anti-vacuity coverage assertion in Phase 4'. This is the plan's own anti-vacuity safeguard — modelled on tests/test_doc_links.py:95-104 (test_the_guard_actually_covers_the_repo, 'A link checker that scans nothing passes every time') — so a cold agent following the Phase 2 TODO skips it in Phase 4, does not find it in Phase 5's step list either, and ships exactly the vacuous guard the plan exists to prevent.
proposed_fix:
  Fix on Phase 4 — the first real handoff, reviews/proving-run-a.md, exists at the end of Phase 4. Change Phase 2 step 9's TODO text to say Phase 4 and correct architecture_map section 9. Keep Phase 5's acceptance line 'the linter now scans BOTH proving-run artifacts' as the widening check.
reviewer: executability
severity: major
title: The plan contradicts itself four ways about which phase gets the handoff linter's anti-vacuity coverage assertion

-------------------------------------------------------------------------------
[blocker] A2-EX-01 (executability) - Phase 0 — the plan's only BLOCKING gate — never names the spawn mechanism, and has no false-negative discipline
-------------------------------------------------------------------------------
category: executability
confidence: high
id: A2-EX-01
location: plan Phase 0 steps 4-5; grounds against requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md:508-509
problem:
  Phase 0 stops the entire build on a negative finding (blocker fix A2-02, PROJECT_SCOPE.md:508-509), and its decisive step is unspecified: 'Spawn by that agent type using whatever surface the harness exposes.' A cold agent has no named tool, flag, or parameter to try. Worse, the plan draws no distinction between the two ways the probe can come back negative: (a) the harness does not support project .claude/agents/*.md at all, and (b) the harness loads agent definitions at session start and has not re-scanned a file created mid-session. Case (b) is a false negative that, under the stated STOP rule, returns a viable feature to scoping. The ambiguity is measured: nothing in this repo consumes .claude/agents/ (git ls-files .claude returns 16 paths, all under .claude/skills/**; Test-Path .claude/agents is False; scope_panel.js:174 calls runChecked(prompt, {label, phase, schema, effort}, scoperIsStub) with no agent-type parameter), so the implementer has no in-repo precedent and will guess.
proposed_fix:
  Name the concrete surface: the subagent-spawn tool's subagent_type / agent-name parameter, which is what a project .claude/agents/*.md registers into — the only spawn path available, since the three panel scripts have no agent-type hook. Then add a two-stage STOP rule: a negative result is PROVISIONAL until the probe is re-run in a FRESH session (the definition file existing before that session started) and until `claude --version` plus `claude --help` output is quoted into reviews/harness-probe.md. Only a negative surviving the fresh-session re-probe triggers the STOP; record both attempts.
reviewer: executability
severity: blocker
title: Phase 0 — the plan's only BLOCKING gate — never names the spawn mechanism, and has no false-negative discipline

-------------------------------------------------------------------------------
[major] A2-EX-02 (executability) - files_to_touch instructs an edit to PROJECT_SCOPE.md's status blockquote that mechanically fails AC16
-------------------------------------------------------------------------------
category: acceptance-contract
confidence: high
id: A2-EX-02
location: plan files_to_touch entry for requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md and Phase 6 step 4; contradicts PROJECT_SCOPE.md:157
problem:
  AC16 reads verbatim at PROJECT_SCOPE.md:157: 'PROJECT_SCOPE.md opens at `scoped · decided · next: plan`, FEATURE_REQUEST.md's Status blockquote is advanced, and the Index row at requests/feature-requests/README.md:92 matches'. AC16 therefore requires PROJECT_SCOPE.md line 1 to STAY at its current value (verified: line 1 is `> **Status:** scoped · created 2026-08-13 · decided · next: plan`). The plan's files_to_touch entry and Phase 6 step 4 both instruct the implementer to advance it. Following the checklist literally breaks the criterion the same checklist claims to satisfy — and because AC16 is described as 'mechanically greppable', the stage-4 panel will grep for that literal string and mark it unmet.
proposed_fix:
  Change the files_to_touch entry to 'DO NOT TOUCH — PROJECT_SCOPE.md line 1 stays at `scoped · created 2026-08-13 · decided · next: plan`; AC16 (PROJECT_SCOPE.md:157) asserts that exact string.' Restrict Phase 6's bookkeeping to FEATURE_REQUEST.md's blockquote (verified line 1: `scoped · created 2026-08-12 · decided · next: plan`) and the track README Index row, and add the AC16 grep to Phase 6's acceptance list.
reviewer: executability
severity: major
title: files_to_touch instructs an edit to PROJECT_SCOPE.md's status blockquote that mechanically fails AC16

-------------------------------------------------------------------------------
[major] A2-EX-05 (executability) - Acceptance criteria are written in bash (find, grep) on a Windows PowerShell box, so they cannot be run as written
-------------------------------------------------------------------------------
category: environment
confidence: high
id: A2-EX-05
location: plan Phase 5 step 8 and Phase 5 acceptance item 4 (find transform/models -name '*.sql'); also Phase 1 acceptance 3, Phase 3 acceptance 4 and 5, Phase 4 step 6
problem:
  Phase 5's mechanical proof that the drill leaked no pipeline code is `find transform/models -name '*.sql'` returns nothing. That string is copied from ci.yml:81, which runs on ubuntu-latest. This environment is win32 / Windows PowerShell 5.1, where `find` resolves to Windows find.exe (a line-matching utility) and `-name` is not a flag — the command errors, and an agent reading a non-zero exit as 'failure' or a confused one as 'empty' gets the wrong answer on the criterion that verifies the scope's hardest non-goal (PROJECT_SCOPE.md:110). The same applies to the bare `grep` verbs in four other acceptance lists. The plan itself carries CLAUDE.md:126 ('Windows dev, Linux CI') into its conventions and uses Select-String elsewhere, so the inconsistency is unforced.
proposed_fix:
  Use PowerShell throughout, keeping the bash form only as a parenthetical for CI parity: `Get-ChildItem transform/models -Recurse -Filter *.sql` (expect zero results) and `Select-String -Path <file> -Pattern '<pattern>'`. For the AC10 hunk greps, spell them out: Select-String -Path requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md -Pattern '^@@ |^\+\+\+ |^--- |^diff --git ' so the regex Decision 6 settled on is the one actually run.
reviewer: executability
severity: major
title: Acceptance criteria are written in bash (find, grep) on a Windows PowerShell box, so they cannot be run as written

-------------------------------------------------------------------------------
[major] A2-EX-08 (executability) - Phase 5's PASS grep can score a uniqueness test that never ran, so the omission drill can pass on a model that does not build
-------------------------------------------------------------------------------
category: acceptance-contract
confidence: medium
id: A2-EX-08
location: plan Phase 5 step 5 (grep for unique / unique_combination_of_columns in the produced schema.yml)
problem:
  The omission drill is the feature's only behavioral criterion (AC11, PROJECT_SCOPE.md:147; blocker A2-01 at :506-507 makes it the criterion proving the definition caused the behavior). Its PASS condition is a grep over produced text. A grep is satisfied by a schema.yml naming dbt_utils.unique_combination_of_columns while the scratch project cannot resolve dbt_utils, or by a test whose combination_of_columns does not match the grain the model declares — the exact mismatch update-docs/SKILL.md:114-126 calls a blocker ('A model claiming one row per player per game while its uniqueness test covers only game_id is documented wrongly, tested wrongly, or both'). The plan's own fallback ('accept a core unique test on a surrogate key') makes the non-building case likelier, not rarer.
proposed_fix:
  Add to Phase 5's PASS definition: the scratch project must BUILD — `uv run dbt build --project-dir var/scratch/omission-drill --profiles-dir var/scratch/omission-drill --target ci` — and the uniqueness test must appear in that output as PASS, quoted into reviews/proving-run-b.md. Add the grain-vs-test agreement check from update-docs/SKILL.md:118-121: the columns in the uniqueness test must match the grain the description claims, or it is a FAIL.
reviewer: executability
severity: major
title: Phase 5's PASS grep can score a uniqueness test that never ran, so the omission drill can pass on a model that does not build

-------------------------------------------------------------------------------
[major] A2-EX-09 (executability) - The relocation is applied inconsistently — era boundaries are duplicated into the definition while staying in CLAUDE.md, creating a new copy with no guard
-------------------------------------------------------------------------------
category: consistency
confidence: high
id: A2-EX-09
location: plan Phase 1 step 3 ('Add the era boundaries from CLAUDE.md:52-59') vs Phase 3 step 2, which cuts only :84-103 and four gotcha bullets
problem:
  Decision 12's entire rationale (PROJECT_SCOPE.md:434-438) is that relocating gives the rules a single owner and 'dissolves the drift surface instead of guarding it' — which is why AC3's drift guard was withdrawn. But Phase 1 step 3 instructs the implementer to COPY CLAUDE.md:52-59 (the 2013-14 tracking boundary, the three irregular seasons) into the definition, and Phase 3 leaves those lines in CLAUDE.md. That creates a brand-new duplicate in the same commit sequence that removed the guard duplication was supposed to justify, and the Phase 2 phrase-presence guard asserts the definition CONTAINS the boundary without asserting the two copies agree. The plan's risk list correctly names the existing four-way restatement (scope_panel.js:124, plan_panel.js:146, implement-plan/SKILL.md:100-112 — all read and confirmed) but does not notice it is adding a fifth for era boundaries.
proposed_fix:
  State the split explicitly in Phase 1 and in ADR 0007: CLAUDE.md's Key Context (:52-59) is DOMAIN context that stays and is deliberately duplicated (the manager needs it to scope), while the Data Layer BUILD MECHANICS relocate. Add a one-line note in the definition's era section — 'domain context; CLAUDE.md Key Context is the co-equal copy' — so a future editor knows the two move together, and say in ADR 0007's Consequences that the relocation collapsed one duplication and created one.
reviewer: executability
severity: major
title: The relocation is applied inconsistently — era boundaries are duplicated into the definition while staying in CLAUDE.md, creating a new copy with no guard

-------------------------------------------------------------------------------
[major] A2-EX-06 (executability) - The prescribed pre-spawn snapshot command fails on first use — var/tmp/ does not exist — and PowerShell redirection will BOM the patch
-------------------------------------------------------------------------------
category: executability
confidence: high
id: A2-EX-06
location: plan Phase 4 step 2 and Phase 5 step 4 (git diff HEAD > var/tmp/data-engineer-agent-run-a-pre.patch); measured against the filesystem
problem:
  Measured: var/ contains only warehouse/ — there is no var/tmp/. In PowerShell, `git diff HEAD > var/tmp/x.patch` fails with a path-not-found redirection error before git runs, so the first step of the write-guard package (the plan's substitute for 'it can't write', PROJECT_SCOPE.md:80) dies on execution in both proving phases. Secondly, `>` here writes UTF-8 with a BOM, which is the exact class of trap the plan seeds into memory as entry (a) citing implement-plan/SKILL.md:111-112 — a BOM'd patch is not reliably re-appliable, so the net is quietly degraded even once the directory exists.
proposed_fix:
  Prepend `New-Item -ItemType Directory -Force var/tmp | Out-Null` to both snapshot steps, and let git write the bytes itself: `git diff HEAD --output var/tmp/<slug>-run-a-pre.patch` (no shell redirection, no BOM). The same latent failure exists in implement-plan/SKILL.md:121-122's prose — surface it to the user as a separate one-line fix rather than absorbing it here.
reviewer: executability
severity: major
title: The prescribed pre-spawn snapshot command fails on first use — var/tmp/ does not exist — and PowerShell redirection will BOM the patch

-------------------------------------------------------------------------------
[major] A2-EX-07 (executability) - The omission drill's dbt workaround rests on a misread non-goal, and pointing packages-install-path at the real project is destructive-adjacent
-------------------------------------------------------------------------------
category: correctness
confidence: high
id: A2-EX-07
location: plan Phase 5 step 2 and decisions[10]; grounds against .github/workflows/ci.yml:70-71, transform/dbt_project.yml clean-targets, PROJECT_SCOPE.md:114
problem:
  The plan states 'dbt deps is a network call the scope forbids (PROJECT_SCOPE.md:114)' and therefore points the scratch project's packages-install-path at the real transform/dbt_packages/. Both halves are wrong. PROJECT_SCOPE.md:114 reads 'NOT anything that spends cloud money, hits stats.nba.com live, or touches prod' — dbt deps does none of those, and CI runs `uv run dbt deps --project-dir transform --profiles-dir transform` on every PR (ci.yml:70-71), so treating it as forbidden contradicts the repo's own standing behavior and would propagate a false rule into box-score-foundation. Worse, transform/dbt_project.yml lists `dbt_packages` under clean-targets: a scratch project whose packages-install-path points into transform/ turns any `dbt clean` into a deletion of the real package tree (measured: transform/dbt_packages/dbt_utils exists, and transform/packages.yml installs it precisely because unique_combination_of_columns is how every silver model proves its grain).
proposed_fix:
  Drop the packages-install-path redirection. In the scratch project either run `uv run dbt deps --project-dir var/scratch/omission-drill --profiles-dir var/scratch/omission-drill` (allowed, and what CI already does), or copy transform/dbt_packages/dbt_utils into var/scratch/omission-drill/dbt_packages/ — a plain file copy, fully offline, with no path aliasing into the real project. Correct decisions[10]'s rationale so the false 'dbt deps is forbidden' rule is not carried forward.
reviewer: executability
severity: major
title: The omission drill's dbt workaround rests on a misread non-goal, and pointing packages-install-path at the real project is destructive-adjacent
~~~~~

## Meta-audit findings (audits the MERGE, not the repo)

~~~~~

-------------------------------------------------------------------------------
[major] M-01 - Merge dropped the measured harness evidence that de-risks the BLOCKING gate
-------------------------------------------------------------------------------
category: completeness
confidence: high
id: M-01
location: merged plan Phase 0 steps 3-4 ("using whatever surface the harness exposes") vs code-grounded proposal architecture_notes §3
problem:
  The code-grounded planner did real measurement work and reported it: the installed CLI exposes `--agent <agent>` ("Agent for the current session. Overrides the 'agent' setting"), `--agents <json>` (inline definitions), `--setting-sources <user,project,local>`, and a `claude agents` subcommand; plus negative controls that `~/.claude/agents/` does not exist and `~/.claude/settings.json` carries no agent key. I re-ran `claude --help` and confirmed all four surfaces exist. It also gave a concrete runnable probe: `claude -p "<sentinel>" --agent probe-loader --setting-sources project`. The merge kept only the generic "run `claude --help` / `claude agents --help`" and told the implementer to spawn "using whatever surface the harness exposes". This is the plan's one STOP/PROCEED gate for the entire feature — the merge made it strictly vaguer than the input it merged, and a cold agent that cannot find a spawn surface may wrongly return STOP and kill a viable feature.
proposed_fix:
  Restore the measured evidence into Phase 0 as the probe's starting hypothesis, labelled `measured` with date and CLI version: name `--agent`, `--agents <json>`, `--setting-sources user,project,local` and `claude agents` explicitly, and carry the literal probe line `claude -p "<sentinel question>" --agent probe-canary --setting-sources project` as step 4's default invocation. Keep the negative controls (`~/.claude/agents/` absent; no agent key in `~/.claude/settings.json`) as the baseline. The probe then confirms/refutes a stated hypothesis rather than starting from zero.
reviewer: meta-audit
severity: major
title: Merge dropped the measured harness evidence that de-risks the BLOCKING gate

-------------------------------------------------------------------------------
[major] M-02 - Decision 3 (agent gets restricted Bash) is absent from the plan, yet the return contract requires it
-------------------------------------------------------------------------------
category: completeness
confidence: high
id: M-02
location: requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md:389-393 (Decision 3) vs merged plan Phase 1 step 2 body items (1)-(11)
problem:
  The decided scope settles Decision 3 explicitly: "Bash: yes, restricted, after the harness probe. Denying Bash would make this the only actor in the repo that cannot verify its own work — it could not run `pytest` or `dbt build` on what it wrote, pushing verification back to the main thread and undoing the isolation the feature exists to buy." Nowhere in the merged plan's eleven-item definition body, nor in the write-allowlist step, nor in Phase 0's allowlist probe, is the agent's TOOL access (as distinct from its WRITE paths) provisioned or stated. None of the three proposals carried it either, so the merge inherited a unanimous drop and was the last stage able to catch it. Not cosmetic: the merge's own return contract (Phase 1 step 6) requires "every row of the verified table must cite a concrete command and its ACTUAL output", and Phase 5's PASS rule can be satisfied by a produced dbt model — both impossible for an agent with no execution capability. It also leaves PROJECT_SCOPE.md:287 ("verification inverts at arm's length") unaddressed.
proposed_fix:
  Add a TOOL ALLOWLIST item to Phase 1's definition body, distinct from the write allowlist: the agent may run read/verify commands (`uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv run dbt build --target ci`, read-only git) and may not run anything that spends money, hits `stats.nba.com`, or mutates the tree/history. Add to Phase 0's probe the question of whether tool permissions are declarable per-agent, and state the fallback (prose-only tool bound in the definition body) if not. Add a Phase 2 guard asserting the definition names the verify-commands clause so the capability cannot be silently deleted.
reviewer: meta-audit
severity: major
title: Decision 3 (agent gets restricted Bash) is absent from the plan, yet the return contract requires it

-------------------------------------------------------------------------------
[major] M-03 - Plan prescribes a `decided` status blockquote while carrying nine open gated decisions
-------------------------------------------------------------------------------
category: process-integrity
confidence: high
id: M-03
location:
  merged plan files_to_touch (IMPLEMENTATION_PLAN.md: "opening at `plan · created 2026-08-14 · decided · next: implement`") + decisions[14], vs gated_decisions (9 entries)
problem:
  `.claude/skills/implement-plan/SKILL.md:67-71` gates on the 3rd field: "If `decided`, proceed. If `open` (gated decisions left undisposed), warn loudly that you'd be building on unmade decisions" (verified verbatim). `.claude/skills/create-implementation-plan/SKILL.md:200-203` likewise expects §5 to "record any gated decisions accepted en bloc and HOW THEY WERE DISPOSED, so the disposition trail survives." The merged plan hard-codes `decided` while shipping nine genuinely open questions — including the line-counting semantic Phase 2's assertion depends on, the faithful-run target Phase 4 cannot start without, the handoff line cap Phase 2's linter must encode, and the drill repetition count that ADR 0007's immutable Consequences section must state. Stage 4 will read `decided`, skip the warning, and build on nine unmade decisions.
proposed_fix:
  Either (a) write the blockquote as `plan · created 2026-08-14 · open · next: implement` and state at the top that stage 4 must not launch until the nine gates are disposed, or (b) route the nine gates to the user at the end of stage 3, record each disposition in §5 in the scope's own format (as PROJECT_SCOPE.md:367-427 does for Decisions 1-11), and only then write `decided`. (b) is preferable and matches the upstream artifact's precedent. Either way, tag the four phase-blocking gates explicitly: counting rule → Phase 2; handoff cap → Phase 2; faithful target → Phase 4; repetitions → Phases 4/5.
reviewer: meta-audit
severity: major
title: Plan prescribes a `decided` status blockquote while carrying nine open gated decisions

-------------------------------------------------------------------------------
[major] M-04 - Three gated items are simultaneously pre-baked into executable phase steps
-------------------------------------------------------------------------------
category: scope-creep
confidence: high
id: M-04
location: merged plan Phase 1 step 4, Phase 3 step 8, Phase 4 step 1 — contradicting gated_decisions #3, #1, #2 respectively
problem:
  A cold implementer executes steps; it does not cross-reference a gated-decisions appendix. Three items are gated for user decision AND written as instructions. (1) DENY-SET EXTENSION: gated_decisions #3 asks whether to extend beyond blocker F1's four entries and recommends adding `CLAUDE.md`/`docs/data-sources.md`/`docs/decisions/`, but Phase 1 step 4 instructs "the four the scope names — plus the recommended extension (see gated decisions)", i.e. build it. That widens the scope's own F1 list (PROJECT_SCOPE.md:496-500), which the merge itself calls a scope-growing call needing a yes. (2) COUNTING SEMANTIC: gated_decisions #1 says "needs a yes before Phase 2 writes the assertion", yet Phase 3 step 8 instructs editing `.claude/skills/update-docs/SKILL.md:76-78` to the `.Count` form. (3) FAITHFUL-RUN TARGET: gated_decisions #2 asks the user to confirm, yet Phase 4 step 1 says "RECOMMENDED" and files_to_touch lists root `README.md` as a concrete EDIT, which reads as a committed deliverable — and a root-README section is not in the scope's DOC INTEGRATION deliverable at PROJECT_SCOPE.md:183.
proposed_fix:
  Make each step conditional and un-executable until disposed: Phase 1 step 4 asserts ONLY blocker F1's four deny entries with the extension in a marked "pending gate #3" note; Phase 3 step 8 becomes "apply the disposition of gate #1"; Phase 4 step 1 opens with "do not spawn until gate #2 is disposed", and files_to_touch marks `README.md` as "CANDIDATE proving-run target, pending gate #2 — not a deliverable of this feature." Better: dispose all three before the plan lands (see M-03) and delete the gates.
reviewer: meta-audit
severity: major
title: Three gated items are simultaneously pre-baked into executable phase steps

-------------------------------------------------------------------------------
[major] M-05 - Merge invented a 'reuse what's there' dbt_utils step no planner proposed, resting on untracked local state
-------------------------------------------------------------------------------
category: cost-unrealism
confidence: medium
id: M-05
location:
  merged plan decisions[10] and Phase 5 step 2 ("borrows `transform/dbt_packages/` rather than running `dbt deps`"; "verified: `Test-Path transform/dbt_packages` is True")
problem:
  This step exists in no proposal. All three planners treated dbt_utils as unavailable offline: domain said plainly "a fresh project under `var/` cannot fetch it offline... so the scratch project uses core dbt only" and prescribed a core `unique` test on a surrogate key; sequencing proposed running `dbt deps` in the scratch project (a network call the scope forbids at PROJECT_SCOPE.md:114); code-grounded prescribed no dbt_utils at all. The merge converted this into a confident "verified... exists locally, so point the scratch project's `packages-install-path` at that absolute path." I checked: `transform/dbt_packages/dbt_utils` does exist (235 files, v1.4.1 per `transform/package-lock.yml`). But it is untracked, gitignored-class, regenerable working state — a cold implementer on a fresh clone, or after a `dbt clean`, has nothing there, and the plan presents it as a durable repo fact. Separately, pointing `packages-install-path` at an absolute path outside the scratch project root is asserted, not measured: dbt resolves that key relative to the project directory and the merge ran no test. The retained fallback is the only thing keeping this from being a blocker.
proposed_fix:
  Demote the borrow to the fallback and promote the core-`unique` test to the primary path, which is what two of three planners independently recommended: build the drill's silver-shaped model with a surrogate key plus a core `unique` test as the proof of grain, and record in `reviews/proving-run-b.md` that this deviates from the repo's `dbt_utils.unique_combination_of_columns` idiom for offline reasons. Restate the observation as "MEASURED on this machine 2026-08-14, untracked and regenerable — may be absent on a fresh clone", and add a precondition `Test-Path transform/dbt_packages/dbt_utils` before relying on it. Keep the merge's excellent guardrail that "'dbt deps failed' must never be read as 'the agent failed'."
reviewer: meta-audit
severity: major
title: Merge invented a 'reuse what's there' dbt_utils step no planner proposed, resting on untracked local state

-------------------------------------------------------------------------------
[minor] M-06 - Internal contradiction: handoff anti-vacuity assertion lands in Phase 4 in two places and Phase 5 in two others
-------------------------------------------------------------------------------
category: consistency
confidence: high
id: M-06
location:
  merged plan architecture_map §9 ("Phase 5") + Phase 2 step 9 ("TODO naming Phase 5") vs Phase 4 step 7 ("Add the anti-vacuity coverage assertion") + decisions[3] ("in Phase 4")
problem:
  Four statements about the same guard, split two-and-two. The merge's own guard-placement rule (architecture_map §9) says a guard lands with its subject, and the first real handoff artifact lands in Phase 4 — so Phase 4 is correct and the two Phase 5 mentions are stale. A cold implementer following architecture_map §9 and the Phase 2 TODO will leave `tests/test_handoff_contract.py` vacuously green through Phase 4's acceptance, which explicitly claims "the coverage assertion confirming at least one handoff was found and linted" — a criterion the implementer was just told not to build yet.
proposed_fix:
  Standardize on Phase 4 (the phase producing the first marker-carrying artifact). Fix architecture_map §9 and Phase 2 step 9's TODO to say Phase 4; leave Phase 5's acceptance asserting the linter now scans BOTH proving-run artifacts.
reviewer: meta-audit
severity: minor
title: Internal contradiction: handoff anti-vacuity assertion lands in Phase 4 in two places and Phase 5 in two others

-------------------------------------------------------------------------------
[minor] M-07 - A Unix `find` command is embedded in acceptance criteria on a PowerShell-only Windows box
-------------------------------------------------------------------------------
category: correctness
confidence: high
id: M-07
location: merged plan Phase 5 step 8 and Phase 5 acceptance criterion 4: "`find transform/models -name '*.sql'` returns nothing"
problem:
  The environment is Windows 11 / PowerShell 5.1 and the plan uses PowerShell idioms everywhere else (`Get-Content`, `Test-Path`, `Select-String`, `Measure-Object`). On this box `find` resolves to `find.exe`, a string-search utility, and `find transform/models -name '*.sql'` returns "FIND: Parameter format not correct" with a nonzero exit — which a cold agent may read as a failed check, or worse as "returned nothing" and therefore a pass. This is the mechanical verification of the scope's non-goal at PROJECT_SCOPE.md:110 (no `.sql` lands), so a check that silently misfires defeats the one criterion proving the drill did not leak into `transform/`. Inherited from the code-grounded proposal; neither other planner used it.
proposed_fix:
  Replace both occurrences with `Get-ChildItem transform/models -Recurse -Filter *.sql` (asserting an empty result) or the repo-consistent `git ls-files 'transform/models/*.sql'` plus `git status --porcelain transform/`. Sweep the plan for the same class of slip: the informal "grep" in Phase 1/3/5 acceptance should read `Select-String` if a cold agent runs it literally.
reviewer: meta-audit
severity: minor
title: A Unix `find` command is embedded in acceptance criteria on a PowerShell-only Windows box

-------------------------------------------------------------------------------
[minor] M-08 - "The ops/ snapshot script was gated and declined" asserts a disposition the scope never records
-------------------------------------------------------------------------------
category: provenance
confidence: high
id: M-08
location: merged plan architecture_map §7(e) and decisions[15] ("the `ops/` snapshot script was gated and declined (PROJECT_SCOPE.md:259)")
problem:
  PROJECT_SCOPE.md:259 is the Above-&-Beyond gated-tier RATIONALE for the reusable snapshot script; it records why it was gated, not that it was declined. The scope's disposition record (PROJECT_SCOPE.md:367-427) contains Decisions 1-11 and none is the `ops/` script — the eleven disposed gates are timing, proving-target, Bash, invariants, memory cap, guard strictness, panel-teaching, repetitions, routing guard, ADR timing, and allowlist scope. On the record the script's gate is still open. The merge's CONCLUSION (don't add net-new executable tooling to a change whose reviewability depends on staying small) is right and well argued; the JUSTIFICATION is invented, and it came from two of three proposals, so the merge had two chances to catch it.
proposed_fix:
  Reword to the defensible form: "the reusable `ops/` snapshot script was GATED (PROJECT_SCOPE.md:259) and is not built here — the prose protocol at `implement-plan/SKILL.md:120-125` is sufficient for two proving runs, and net-new executable tooling would cost this change its reviewability." If the user wants the disposition recorded rather than implied, add it to the gated-decisions list.
reviewer: meta-audit
severity: minor
title: "The ops/ snapshot script was gated and declined" asserts a disposition the scope never records

-------------------------------------------------------------------------------
[minor] M-09 - Index Stage vocabulary conflict resolved silently; decisions[14] cites the wrong governing line
-------------------------------------------------------------------------------
category: consistency
confidence: high
id: M-09
location: merged plan decisions[14] and Phase 6 step 4 ("the row at :92 reads `planned`") vs .claude/skills/create-implementation-plan/SKILL.md:172
problem:
  decisions[14] claims the split is clean — blockquote form from `create-implementation-plan/SKILL.md:176`, Index cell from `requests/feature-requests/README.md:85` — and concludes "Both are satisfied; neither is invented." But the line that actually governs the Index cell is `create-implementation-plan/SKILL.md:172`, which I verified reads: "set this item's Index row Stage cell to `plan` (match the row by its `[<slug>]` link)." That says `plan`; README:85's grammar says `planned`. This is a genuine pre-existing repo conflict: the code-grounded planner picked `plan`, the merge picked `planned`, and the merge resolved the disagreement without flagging it. A cold implementer follows whichever file it reads, and `/update-docs`'s reconciliation (`update-docs/SKILL.md:131-136`) re-opens the question on the next pass.
proposed_fix:
  State the conflict explicitly in decisions[14], citing `create-implementation-plan/SKILL.md:172` alongside README:85. Recommend `planned` (the track README's status grammar is authoritative for the track), and add a one-line note that `create-implementation-plan/SKILL.md:172` says `plan` and is worth a separate correction — flagged, not fixed here, since the scope's doc-integration list does not cover it.
reviewer: meta-audit
severity: minor
title: Index Stage vocabulary conflict resolved silently; decisions[14] cites the wrong governing line

-------------------------------------------------------------------------------
[nit] M-10 - "Six triggers" for the /update-docs sweep — there are seven
-------------------------------------------------------------------------------
category: accuracy
confidence: high
id: M-10
location: .claude/skills/commit/SKILL.md:86-92 vs merged plan Phase 3 commit_note, Phase 6 commit_note, and the code_references entry for commit/SKILL.md:83-93
problem:
  The merge says "the six triggers at `commit/SKILL.md:83-93`" three times, and twice says "four of the six." I read the file: lines 86-92 are seven bullets (new/changed directory; new convention/constraint/gotcha; new dbt model/source/changed grain; completed phase or changed setup step; contradicting an accepted ADR; a source claim promoted to verified; a request artifact whose status advanced). The merge's own code_references entry for that range enumerates seven and then labels them six. Harmless to execution, but it is exactly the kind of miscount a repo whose premise is "docs are treated as authoritative" propagates.
proposed_fix: Change all three occurrences to "seven triggers" and "four of the seven".
reviewer: meta-audit
severity: nit
title: "Six triggers" for the /update-docs sweep — there are seven

-------------------------------------------------------------------------------
[nit] M-11 - Phase 3's line-math understates the CLAUDE.md cut by roughly a quarter
-------------------------------------------------------------------------------
category: accuracy
confidence: high
id: M-11
location: merged plan Phase 3 acceptance criterion 2 ("it was 122 before the cut, which removes ~24 lines and adds ~4") vs CLAUDE.md:84-103, :107-116, :126
problem:
  The prescribed cut is CLAUDE.md:84-103 (20 physical lines) plus :107-109 (3), :110-112 (3), :113-116 (4) and :126 (1) — 31 physical lines, ~30 non-blank under the `Measure-Object -Line` semantic the sentence uses. "~24" is low by about 25%. Directionally harmless (78 lines of headroom either way), but the merge elsewhere makes counting semantics a first-class contract and pins them in three places, so an unpinned estimate inside that same acceptance criterion invites the exact confusion gate #1 exists to prevent.
proposed_fix:
  Restate as "removes 31 physical lines (140 → ~113 before the pointer and map row are added)" and give the expected post-cut value under BOTH counters, so the implementer can confirm the pytest guard and the documented one-liner agree.
reviewer: meta-audit
severity: nit
title: Phase 3's line-math understates the CLAUDE.md cut by roughly a quarter

-------------------------------------------------------------------------------
[nit] M-12 - Phase 0 acceptance runs Get-ChildItem against a directory that may not exist after canary deletion
-------------------------------------------------------------------------------
category: correctness
confidence: medium
id: M-12
location: merged plan Phase 0 step 8 and Phase 0 acceptance criterion 4 ("`Get-ChildItem .claude/agents` shows no leftover probe file")
problem:
  Phase 0 creates `.claude/agents/` solely to hold `probe-canary.md` and `probe-plain.md`, then deletes both. If the directory is also removed, `Get-ChildItem .claude/agents` raises ItemNotFoundException and the tool reports a nonzero exit — a cold agent reads red where the state is correct. If the directory is left, it is an empty untracked dir that git ignores, so the companion criterion ("git status --porcelain shows only reviews/harness-probe.md as new") passes only by accident rather than by design.
proposed_fix:
  Make the criterion existence-tolerant: `if (Test-Path .claude/agents) { Get-ChildItem .claude/agents -File }` must return nothing; and add an explicit instruction to step 8 to remove the empty `.claude/agents/` directory as well, so Phase 1 creates it fresh.
reviewer: meta-audit
severity: nit
title: Phase 0 acceptance runs Get-ChildItem against a directory that may not exist after canary deletion

-------------------------------------------------------------------------------
[nit] M-13 - AC5's "both new Markdown files" silently reinterpreted as three, and its stale file count not flagged
-------------------------------------------------------------------------------
category: completeness
confidence: high
id: M-13
location:
  requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md:135 (AC5) vs merged plan Phase 1 acceptance criterion 2 ("scanned count has risen from 33 toward 36")
problem:
  AC5 as written assumes two new Markdown files (definition + memory); the plan lands three (definition, memory, README) plus three `reviews/` artifacts. The merge handled the identical two-vs-three collision explicitly and well for AC1 (the frontmatter discriminator, one of the strongest things in the merge) but resolved it silently for AC5. AC5 also carries a stale count — "30 tracked `.md` files today, rising to at least 33"; I measured 33 tracked today, so the plan's corrected figure is right and the scope's is stale. Neither divergence is flagged.
proposed_fix:
  Add one line to the acceptance mapping: "AC5 says 'both new Markdown files' and cites 30 tracked `.md`; MEASURED 2026-08-14: 33 tracked, and this plan lands three new `.claude/agents/*.md` plus three `reviews/` artifacts. The criterion is read as 'every new Markdown file is in the scanned set'; `MIN_EXPECTED_FILES = 20` stays satisfied with wide margin." This is the same courtesy the merge already extends to AC1 and AC3.
reviewer: meta-audit
severity: nit
title: AC5's "both new Markdown files" silently reinterpreted as three, and its stale file count not flagged
~~~~~

## Gated decisions as the panel emitted them

Dispositions are recorded in the plan's section 5, not here.

~~~~~

-------------------------------------------------------------------------------
GATE 1
-------------------------------------------------------------------------------
question:
  What counts as a LINE for both budget caps — physical lines (`len(text.splitlines())` / `(Get-Content).Count` = 140 for CLAUDE.md) or non-blank lines (`Measure-Object -Line` = 122, the command AC7 and `update-docs/SKILL.md:77` name)? The 120-line memory cap is ambiguous by roughly 15% until this is settled.
recommendation:
  Count PHYSICAL lines everywhere; state the counting rule in every assertion message; and correct or annotate `update-docs/SKILL.md:76-78` in the same commit so local, CI and the doc gate use ONE counter. Physical lines are what a reader scrolls, they are trivially reproducible in Python, and the alternative leaves a red CI check reconcilable against a documented one-liner that disagrees by 18 lines. Needs a yes before Phase 2 writes the assertion.
related:
  - AC4
  - AC7
  - Decision 5 (PROJECT_SCOPE.md:401-403)
  - update-docs/SKILL.md:76-78

-------------------------------------------------------------------------------
GATE 2
-------------------------------------------------------------------------------
question:
  What is the faithful run's target (Phase 4)? Decision 2 wants 'a small real repo task so the evidence is a genuine diff reviewed through /commit', but the deny set (`tests/`, `.github/`, `ops/`, `.claude/`), the `transform/models/` reservation, the no-pipeline-by-product non-goal and the `docs/data-sources.md` routing denial together exclude almost every surface.
recommendation:
  The agent adds a short (~15 line) section to root `README.md` describing `.claude/agents/` and the spawn protocol, AND is handed one deliberately mis-routed candidate — a data fact such as the still-`unconfirmed` bulk-endpoint belief — which the routing rule requires it to place in `docs-delta` rather than memory. Measured gap: `README.md` is 117 lines and mentions neither `.claude` nor 'skill', so this is genuinely earned work; it is outside every denied and reserved path, lands no pipeline code, and produces exactly the memory delta AC14 needs `/commit` to display. Explicitly forbid `tests/fixtures/README.md` — denied path, and the scope says its known drift must not be absorbed (PROJECT_SCOPE.md:307). Any alternative target must pass the same four-constraint checklist.
related:
  - Decision 2 (PROJECT_SCOPE.md:380-387)
  - AC12
  - AC14
  - PROJECT_SCOPE.md:110
  - blocker F1

-------------------------------------------------------------------------------
GATE 3
-------------------------------------------------------------------------------
question:
  Should the agent's deny set extend beyond blocker F1's four entries (`tests/`, `.github/`, `ops/`, `.claude/`) to also cover `CLAUDE.md`, `docs/data-sources.md`, `docs/decisions/`, `pyproject.toml`, `uv.lock`, `.gitignore` and `.gitattributes`?
recommendation:
  Extend by THREE and no more: `CLAUDE.md`, `docs/data-sources.md`, and `docs/decisions/`. Those are precisely the files the routing rule (AC13) and the manager/developer seam depend on the agent not touching — an agent that edits `docs/data-sources.md` directly defeats the whole routing design. Leave `pyproject.toml`/`uv.lock`/`.gitignore` out of the declared deny set for v1: they are legitimately task-scoped for a future extraction feature, and over-denying now makes the sequel's routing table wrong. Have the Phase 2 guard assert only F1's four entries so acceptance is not over-fit to a judgment call, and state the extension in prose in the definition.
related:
  - blocker F1 (PROJECT_SCOPE.md:496-500)
  - AC13
  - Decision 11
  - the Sequel's dispatch rule (PROJECT_SCOPE.md:467-490)

-------------------------------------------------------------------------------
GATE 4
-------------------------------------------------------------------------------
question:
  What is the handoff's line cap? Decision 5 pinned the MEMORY cap at 120; no number was ever gated for the handoff, and AC10 requires the cap to exist and be checked.
recommendation:
  120, for symmetry with the memory cap, stated in the assertion message and in the definition's return contract. A handoff longer than the memory file it feeds has stopped being a summary — which is the exact failure the contract exists to prevent (FEATURE_REQUEST.md:35-37). Confirm or set a different number before Phase 2 writes the guard.
related:
  - AC10
  - Decision 5
  - FEATURE_REQUEST.md:35-37

-------------------------------------------------------------------------------
GATE 5
-------------------------------------------------------------------------------
question: How many repetitions per drill? Decision 8 asks for two if affordable, and makes one acceptable only if the evidence is labelled a single observation.
recommendation:
  Two for the OMISSION DRILL (Phase 5, where nondeterminism matters most and where a FAIL blocks the feature) and one for the faithful run (Phase 4), with run A's evidence labelled a single observation in both the artifact and ADR 0007. Decide BEFORE Phase 4, because ADR 0007's Consequences section is immutable once accepted (`docs/decisions/README.md:29-32`) and must state the true count. The honesty requirement is not optional either way; only the repetition is.
related:
  - Decision 8 (PROJECT_SCOPE.md:413-415)
  - AC11
  - Decision 10
  - docs/decisions/README.md:29-32

-------------------------------------------------------------------------------
GATE 6
-------------------------------------------------------------------------------
question: Which epistemic vocabulary governs memory entries — CLAUDE.md:76-79's five labels, `update-docs/SKILL.md:105`'s four, or `docs/data-sources.md:5-10`'s three?
recommendation:
  CLAUDE.md's FIVE (measured / verified / inferred / assumed / unconfirmed), because memory is repo scar tissue and `CLAUDE.md` is the repo-wide convention; leave `docs/data-sources.md` on its own three-label set and do NOT reconcile it here (out of scope). Name the divergence in one line of the memory header so it is recorded rather than rediscovered — otherwise the entry-format guard encodes one variant while the doc gate audits another, and a cold implementer invents a fourth.
related:
  - Cheap fold at PROJECT_SCOPE.md:189
  - AC13
  - update-docs/SKILL.md:103-112

-------------------------------------------------------------------------------
GATE 7
-------------------------------------------------------------------------------
question: What is the agent's name and slug, and does the memory file stay inside `.claude/agents/`?
recommendation:
  `data-engineer` — `.claude/agents/data-engineer.md` and `.claude/agents/data-engineer-memory.md` — keeping the memory where the scope put it (PROJECT_SCOPE.md:169). CONTINGENT on Phase 0 probe (c): if the harness registers or chokes on frontmatter-less Markdown in that directory, the memory file and README must move (e.g. `.claude/agent-memory/data-engineer.md`) and every path in this plan shifts. Note the cost of keeping it: two special cases survive — the AC1 frontmatter discriminator and the sequel's `.claude/**` deny-prefix carve-out (PROJECT_SCOPE.md:479-482), which is why the definition must state the carve-out as an EXACT PATH rather than a prefix rule. Cheap to change now, awkward later, and if the harness derives the invocation name from frontmatter or filename the two must agree.
related:
  - AC1
  - blocker F3
  - PROJECT_SCOPE.md:169
  - PROJECT_SCOPE.md:479-482

-------------------------------------------------------------------------------
GATE 8
-------------------------------------------------------------------------------
question:
  Where is the write allowlist declared machine-readably, and what does the answer cost? If Phase 0 finds frontmatter cannot carry it and a tracked `.claude/settings.json` is required, that is a NEW tracked file this scope did not anticipate.
recommendation:
  Prefer frontmatter if the probe accepts it. If not, use a fenced list under a stable `## Write allowlist` heading in the definition body — parseable without any harness support, and the form the sequel's dispatcher can read. Adopt a tracked `.claude/settings.json` only if the probe shows it is the ONLY place permissions can live, and surface it to the user as a new file needing its own deny-set entry and `/commit` review. If no machine-readable allowlist exists at all, the allowlist is prose-only for v1 — and the user should know that before the sequel is written, because the dispatch rule rests on this dependency (PROJECT_SCOPE.md:489-490).
related:
  - AC9
  - Decision 3 (PROJECT_SCOPE.md:389-393)
  - the Sequel (PROJECT_SCOPE.md:463-490)

-------------------------------------------------------------------------------
GATE 9
-------------------------------------------------------------------------------
question:
  What shape does the memory-vs-docs routing guard take? Decision 9 says warning-shaped or a curated denylist, never a hard CI gate — but `warnings.warn` is invisible in CI output unless asserted, and a denylist is a hard gate on a narrow list.
recommendation:
  A NARROW CURATED DENYLIST implemented as an ordinary assertion, chosen so it cannot fire on the canonical GOOD entry ('leaguegamelog returns a DataFrame, not JSON') — e.g. season-range strings, `rate limit`, `2013-14`, `82 games` — with the reasoning recorded in the test docstring. A pytest warning nobody sees is a check that does not exist, which is worse than an honest narrow gate. Keep the entry-FORMAT half as a hard assertion regardless, and leave the judgment half of curation deferred to the follow-up request where real entries exist to design against.
related:
  - Decision 9 (PROJECT_SCOPE.md:417-419)
  - AC13
  - PROJECT_SCOPE.md:255
~~~~~

## Reviewer summaries

~~~~~

===============================================================================
REVIEWER: code-grounded  (adversary)
===============================================================================
CODE-GROUNDED VERIFICATION PASS. I resolved every reference in the merged plan's `code_references`, `onboarding`, `architecture_map`, `phases`, `files_to_touch`, `conventions`, `risks` and `gated_decisions` against the live repo on branch `feature/data-engineer-agent`. Headline: no fabricated path, function, or symbol. Every file cited exists; the load-bearing line ranges land where the plan says they do — CLAUDE.md:16-33 (map, `.claude/skills/` at :27), :52-59, :65-69, :73-75, :76-79, :84-103 (Data Layer; sub-ranges :86-88/:89-92/:93-94/:95-97/:98-99/:100/:101-103 all exact), :105-126 with the move/keep split exactly as described; tests/test_repo_structure.py:17,19,25-26,77-84; tests/test_doc_links.py:27,31-48 (no `.claude`, `var` at :38),52-53,55-57,69,86-87,89,95-104; ci.yml:26-27,55-56,76,78-85,87-88,93-99 (three jobs, no Node step — confirmed); ops/branch-protection.json:4; pyproject.toml:21-22,24-30,43-64,70-74,77-82; implement-plan/SKILL.md:49-53,67-70,100-112,120-125,127-132,155-156,187-190 plus the two bundled `.mjs` guards at :271,:273; acceptance_panel.js:163,192,196-201,202-206 (verified: no `agents` key; `skills`→`skill-quality` at :204); scope_panel.js:26-35 and the exact spawn call at :174 with no agent-type parameter; plan_panel.js:146; update-docs/SKILL.md:47-48,53-57,71-73,76-78,100-101,103-112,131-136; commit/SKILL.md:42-45,47-67,59; docs/decisions/README.md:19-25,29-32,34-35,39-46; silver README:5-7,9-25,31-33; requests/feature-requests/README.md:45-59,61-85,92 (`scoped`); .gitignore:14-16; docs/data-sources.md:5-10; create-implementation-plan/SKILL.md:176 and the §1-§10 menu at :175-230; PROJECT_SCOPE.md's cited ranges (:110, :120-157, :159-211, :277, :279, :295, :307, :311-316, :324-327, :401-427, :434-454, :463-490, :492-509) and FEATURE_REQUEST.md:35-37,46-47. Independently re-measured the plan's own measurements and they hold: CLAUDE.md 140 physical / 122 by `Measure-Object -Line` (18 blanks); 33 tracked `.md`; `Test-Path .claude/agents` False; no `.claude/settings.json`; `.claude` has exactly one child (`skills`); 16 tracked files under `.claude/skills/`; `transform/models/` = three READMEs, zero `.sql`; `src/nba_platform/` = one `__init__.py`; `transform/dbt_packages/dbt_utils` exists (so the offline drill is viable); packages.yml declares dbt_utils with the grain-proving comment; README.md = 117 lines with zero `.claude`/"skill" hits; `uv run pytest -q` green (8 tests). Also confirmed the cut is safe from a citation standpoint: no tracked non-request file cites `CLAUDE.md:<line>` or a `CLAUDE.md#` anchor, and "Data Layer" appears in no tracked code/skill file. What survived is a set of accuracy and vacuity defects rather than dangling citations: a Unix `find` prescribed as a phase acceptance check on a PowerShell-only box (fails silently to empty stdout = false PASS), a doc edit that creates a bucket name the panel silently maps to no reviewer, an unhandled memory-cap-reached state, one guard that passes vacuously because the relocated text already contains the string it greps for, a status-vocabulary claim that is incomplete against two skills, and several small count/attribution slips.

===============================================================================
REVIEWER: executability  (adversary)
===============================================================================
EXECUTABILITY & SEQUENCING lens. Read PROJECT_SCOPE.md in full (518 lines) and FEATURE_REQUEST.md:1-50, then verified every load-bearing citation against the real tree: CLAUDE.md (140 physical / 122 Measure-Object lines — both confirmed), tests/test_repo_structure.py, tests/test_doc_links.py, .github/workflows/ci.yml, pyproject.toml, acceptance_panel.js:160-208, scope_panel.js:26-40/118-130/168-180, plan_panel.js:144-149, implement-plan/SKILL.md, update-docs/SKILL.md, commit/SKILL.md, create-implementation-plan/SKILL.md:150-244, docs/decisions/README.md, requests/feature-requests/README.md, transform/{dbt_project,profiles,packages}.yml, .gitignore, plus the filesystem (Test-Path .claude/agents = False; transform/dbt_packages/dbt_utils present; var/ holds only warehouse/; README.md 117 lines with zero .claude/skill hits; uv run pytest -q green at 8 tests). Citation hygiene is unusually good — I found no invented path — and the ordering spine (blocking probe -> definition -> guards -> CLAUDE.md cut -> drills -> ADR) is correct, with relocation-before-omission-drill the right non-obvious call. The failures concentrate in EXECUTABILITY, not sequencing: the one blocking gate (Phase 0's spawn step) is specified as "whatever surface the harness exposes" with no false-negative discipline even though a NO kills the feature; several acceptance criteria are written in bash (find, grep) on a Windows PowerShell box the plan itself flags as a hazard; var/tmp/ does not exist so the prescribed snapshot command fails on first use, and on a clean tree that snapshot is empty anyway; the plan self-contradicts four ways about which phase gets the handoff-linter coverage assertion; files_to_touch instructs an edit that mechanically breaks AC16; and the Decision-7 doc-half-only split provably makes stage-4 review coverage WORSE than today (verified at acceptance_panel.js:207). Also flagged: the relocation is applied inconsistently (era boundaries duplicated, not moved), the drill's dbt workaround rests on a misread non-goal that CI itself contradicts, and the drill's PASS grep can pass on a uniqueness test that never ran.

===============================================================================
REVIEWER: meta-audit  (meta_audit)
===============================================================================
META-AUDIT OF THE MERGE (not the repo). Grounding pass: I re-verified the merge's load-bearing citations against the working tree and found the code-grounding unusually clean — CLAUDE.md is exactly 140 physical / 122 by `Measure-Object -Line` (the merge picked the right number; the domain planner's 141 was wrong and was correctly discarded); acceptance_panel.js:163/192/196-206 all check out, including the as-of-game-date clause at :192 that the merge leans on as the "surviving independent net" for the relocation risk; tests/test_doc_links.py:27/31-48/52-53/55-57/69/86-87/89/95-104 and tests/test_repo_structure.py:17/19/25-26/77-84 are exact; commit/SKILL.md:59 (var/ refusal) and implement-plan/SKILL.md:49-53/67-70/127-132 are exact; AREA_TO_SPEC genuinely has no `agents` key. Convergence quality is high on the three-way themes (blocking probe, frontmatter discriminator for AC1, counting semantics, negative controls, relocation-before-drill ordering), and the Phase-3-before-Phase-5 ordering call is correctly identified as the plan's one non-obvious sequencing decision.

The problems concentrate in four places. (a) COMPLETENESS: the merge dropped the single highest-value thing any planner brought — the code-grounded planner's MEASURED harness evidence (`--agent <agent>`, `--agents <json>`, `--setting-sources user,project,local`, a `claude agents` subcommand; I re-ran `claude --help` and confirmed all four exist) — replacing a concrete probe invocation with "whatever surface the harness exposes," which makes the BLOCKING gate vaguer than the raw proposal it merged. It also lost the scope's decided Decision 3 (the agent gets restricted Bash so it can verify its own work) entirely, which no planner carried and which the merge's own return contract silently depends on. (b) DISPOSITION INTEGRITY: the merged plan prescribes a `decided` status blockquote while carrying nine open gated decisions, and three of those gates are simultaneously pre-baked into executable steps — a cold implementer reads the step, not the gate. (c) COST-UNREALISM: the merge invented a "reuse what's there" step no planner proposed — borrowing `transform/dbt_packages/` for the drill's scratch project. dbt_utils 1.4.1 is in fact installed there (235 files, verified), but it is untracked, regenerable, machine-local state, and the `packages-install-path`-to-an-absolute-outside-path mechanic is asserted rather than measured; the two planners who touched this both assumed it was unavailable offline. (d) SMALLER DEFECTS: a four-way internal contradiction over whether the handoff anti-vacuity assertion lands in Phase 4 or Phase 5, a Unix `find` command embedded in an acceptance criterion on a PowerShell-only box, a miscount of the /update-docs sweep triggers, and a "gated and declined" provenance claim the scope never records.
~~~~~

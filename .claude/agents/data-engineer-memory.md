# Data-engineer memory

Implementation ergonomics, learned the hard way. Read this before you build; append to it
when something costs you time that it should not cost the next session.

## What belongs here

Things that make *building* here go wrong: client and library shapes, column-casing
surprises, tooling traps, commands that behave differently than documented, harness
behaviour. Facts an analyst would never care about but an implementer rediscovers every
session.

## What routes elsewhere — do not put these here

- **Data facts** — endpoint shapes and parameters, era and availability boundaries,
  rate-limit behaviour, what a column actually contains. These go to `docs/data-sources.md`
  via your handoff's `docs-delta` section. Never here: that file is audited by the doc gate
  and this one is not, so a data fact recorded here means the repo holds two answers and
  the gate checks one.
- **Repo-wide scar tissue** — a trap that binds every agent, not just you: `CLAUDE.md`
  Constraints & Gotchas, via `docs-delta`.
- **Decisions and their costs** — `docs/decisions/`, via `docs-delta`.

## Entry format

One bullet per entry. The opening line is fixed shape so it can be checked mechanically:

```
- **YYYY-MM-DD** · `label` · <the claim> · evidence: <pointer> · tag: <routing tag>
```

Continuation lines are indented under the bullet. Keep an entry to about four lines.

**`label` is one of the five this repo uses** — `measured`, `verified`, `inferred`,
`assumed`, `unconfirmed` — and they mean different things. An `assumed` claim written as
`verified` is worse than no entry.

Recorded so it is not rediscovered as a bug: the repo carries **three** label vocabularies
that do not agree. `CLAUDE.md` names the five above; `.claude/skills/update-docs/SKILL.md`
names four for `docs/data-sources.md`, including a `documented` that does not exist in the
five; `docs/data-sources.md` itself names fewer still. **The five govern here**, so a claim
that is merely written down somewhere — not run by you — is `assumed`, not `documented`.
Reconciling the three sets is out of scope for this file.

**Paths are inline code, never markdown links.** Grounded, not stylistic: the link checker
scans only markdown-link syntax, so a backticked path is invisible to it — while a real link
to a file that later moves turns CI red on an unrelated PR with a confusing failure. (This
very rule is why the sentence you are reading spells out "markdown links" instead of showing
the bracket-and-parenthesis form: writing the shape would *be* a link, and the checker would
try to resolve it.)

**Cite a repo artifact, never raw environment output.** This file is committed and this repo
is public. Secret scanning catches credentials by content; it does not catch a pasted
machine path, an account id, or a response fragment.

## The budget — two numbers, and they do different jobs

Both counted as physical lines, `len(text.splitlines())` — what a reader scrolls, and what
the pytest guard counts.

**~120 lines is the curation target.** It is what this file should look like when work lands
on `main`, and it is enforced by judgment at the `/update-docs` sweep, not by a test. Whether
an entry has stopped earning its place is not a thing a line count can decide.

**250 lines is the runaway ceiling**, enforced mechanically in CI. Going over it means the
file has genuinely run away, not merely that it is due a sweep.

**Append freely while you work.** Do not stop at 120 and do not ration yourself toward it —
that is how a build loses what it learned in its last three phases. The file gets curated
once, deliberately, before merge; between sweeps it is allowed to be longer than its resting
size.

**At the ceiling, append nothing.** Do not delete an older entry to make room, and do not
silently drop what you learned. Report the entry you wanted to add, plus the words *"memory
at cap, pruning needed"*, under `still-open` and `docs-delta` in your handoff.

**Pruning is a main-thread decision, never yours** — and, learned the hard way on the
box-score build, it is best made *once at the end* rather than reactively mid-build. Pruning
to make room for the next phase means guessing what the phases after it will need, and
guessing wrong drops the entry that would have saved them.

## Entries

- **2026-08-14** · `assumed` · PowerShell 5.1's `Set-Content` and `Out-File` mangle UTF-8;
  write files with the Write/Edit tools instead. · evidence: `.claude/skills/implement-plan/SKILL.md:111-112`
  · tag: `tooling-trap`

- **2026-08-14** · `verified` · The bundled `.claude/skills/**/tests/*.mjs` guards are **not**
  run by CI — the workflow has exactly three jobs and no Node step, so they execute only when
  an agent remembers to run them by hand. Guards that must actually enforce belong under
  `tests/`. · evidence: `.github/workflows/ci.yml`, `ops/branch-protection.json:4` · tag:
  `ci-behaviour`

- **2026-08-14** · `measured` · In agent frontmatter the shell tool is named **`PowerShell`**,
  not `Bash`, on this box. Declaring `Bash` silently yields an agent with no shell at all —
  no warning, no error — and therefore no way to run `pytest`, `mypy` or `dbt build`.
  Argument-scoped syntax like `PowerShell(git status:*)` is parsed but **not enforced**: the
  tool arrives unrestricted. · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `measured` · A new agent definition is **not** spawnable immediately after
  being written — the spawn fails with "Agent type not found", which reads exactly like
  "unsupported". The registry does re-scan later in the same session, so treat that error as
  *not yet*. A fresh session is the reliable route. · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `assumed` · sqlfluff errors rather than no-ops when its model selection
  is empty, which is why the CI step that runs it is wrapped in a conditional. Adding the
  repo's first `.sql` file flips that step from skipped to running. · evidence:
  `.github/workflows/ci.yml:78-85` · tag: `ci-behaviour`

- **2026-08-14** · `measured` · The `CLAUDE.md` and git status injected into your context are
  a snapshot from the **parent session's start** and can be commits behind the file on disk.
  Inherited context is indistinguishable from something you verified — **read from disk before
  asserting repo state.** · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/proving-run-a-verification.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `measured` · PowerShell 5.1's `Get-Content` decodes UTF-8 files as ANSI, so
  each box-drawing char in an ASCII-art tree measures as 3 chars and every column calculation
  comes out wrong. Use `[System.IO.File]::ReadAllText(path, [Text.Encoding]::UTF8)` for any
  alignment or length check. · evidence: `README.md` layout tree · tag: `tooling-trap`

- **2026-08-14** · `measured` · dbt 1.12 warns on top-level generic-test args
  (MissingArgumentsPropertyInGenericTestDeprecation): nest them under `arguments:`. `tests:`
  itself is **not** deprecated, but `data_tests:` replaced it in dbt 1.8. The silver README
  example now carries the current shape. · evidence: `transform/models/silver/README.md` ·
  tag: `tooling-trap`

- **2026-08-15** · `measured` · nba_api 1.11.4 keeps the HTTP status on the private
  `NBAResponse._status_code`; the public surface is only get_response/get_dict/get_json/
  valid_json/get_url. Anything wanting the status reads that name defensively or gets None.
  · evidence: `src/nba_platform/client.py` (`STATUS_CODE_ATTRIBUTE`) · tag: `tooling-trap`

- **2026-08-15** · `measured` · `LeagueGameLog.get_request()` sends **and then** runs
  `load_response()`, which indexes `resultSets['LeagueGameLog']` — so a non-conforming body
  raises inside the call instead of being returned. Landing one needs the lower-level
  `NBAStatsHTTP().send_api_request`. · evidence: `src/nba_platform/client.py` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Colon-free compact-UTC stamps are one-second resolution, and
  a two-run offline test really does collide on one. The landing writer claims a directory
  with `mkdir(exist_ok=False)` and advances the stamp a second on collision rather than
  overwrite. · evidence: `src/nba_platform/landing.py` (`_reserve`) · tag: `tooling-trap`

- **2026-08-15** · `measured` · `write_capture` builds a fixed-shape manifest and opens it
  `"xb"`, so a caller cannot add a field or append one afterwards — appending would mutate a
  landed file. Anything needing extra per-capture metadata writes a sibling document. ·
  evidence: `src/nba_platform/fixtures.py` (`_record_provenance`) · tag: `tooling-trap`

- **2026-08-15** · `measured` · RUF100 flags a `# noqa` naming a rule this repo does not
  `select` ("Unused noqa directive (non-enabled: PLC2701)"), so pylint-style codes cannot be
  pre-silenced. Justify a deliberate private cross-module import in a comment instead. ·
  evidence: `src/nba_platform/fixtures.py` (the `_serialize` import) · tag: `tooling-trap`

- **2026-08-15** · `measured` · **SUPERSEDES the sibling-document entry above.** `write_capture`
  now takes `provenance=` and nests it under the manifest's `provenance` key — reach for that
  before inventing a third file per capture. Nested, never merged into `parameters` (the wire
  dict bronze reads), and always present as `null` when absent, so "never trimmed" and "trimmed
  to everything" are distinguishable without knowing the key can be missing. ·
  evidence: `src/nba_platform/landing.py` (`PROVENANCE_KEY`) · tag: `tooling-trap`

- **2026-08-15** · `measured` · Serialise **both** documents before opening either handle. The
  writer used to render the manifest inline at its own `open("xb")`, so an unserialisable
  optional field would land a payload with no manifest — an aborted capture — instead of failing
  clean. Now a bad value fails with nothing on disk. Any writer taking caller-supplied JSON wants
  this ordering. · evidence: `src/nba_platform/landing.py` (`write_capture`) · tag: `tooling-trap`

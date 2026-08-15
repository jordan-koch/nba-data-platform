<!-- handoff: v1 -->

# Handoff — document `.claude/agents/` in README.md

## track

feature

## built

`README.md` — two edits, both inside the declared target path.

1. New `## Implementation agents` section, placed immediately after `## Repo layout` so the
   tree introduces the directory and the prose elaborates. Three short paragraphs: what
   `.claude/agents/` is and how the harness registers a definition; the manager/developer
   split and the fixed-format handoff into a request's `reviews/`; and the spawn
   preconditions plus the honest statement that this harness has no path-level permission
   system, so the guardrails detect a bad write rather than prevent one. It does not restate
   the protocol — it links to `.claude/agents/README.md`, which owns it.
2. The `## Repo layout` fenced tree now carries `.claude/` with `agents/` and `skills/`
   nested under it, inserted after `requests/` to mirror the ordering of `CLAUDE.md`'s
   project map. Comment columns match the existing tree exactly (24 for top-level entries,
   26 for nested ones — the file's own two conventions, measured rather than eyeballed).

All prose is sourced from `.claude/agents/README.md`, not invented.

`.claude/agents/data-engineer-memory.md` — one appended entry (the allowlisted exact path).
See `surprised-me` for what and why; the leaguegamelog item I was handed did **not** go here.

## verified

| Check | Command | Actual output |
|---|---|---|
| Full offline suite green | `uv run pytest -m "not network" -p no:cacheprovider` | `40 passed in 0.37s`, `exit=0` |
| No dead relative links (both new README links resolve) | `uv run pytest tests/test_doc_links.py tests/test_handoff_contract.py -m "not network"` | `11 passed in 0.31s` |
| Memory entry conforms: format, label, routing denylist, 120-line cap | `uv run pytest tests/test_agent_contract.py -q` | `22 passed` (22 dots, `[100%]`) |
| Lint clean | `uv run ruff check` | `All checks passed!` |
| Formatting clean | `uv run ruff format --check` | `45 files already formatted` |
| Tree alignment matches existing rows | regex gap-scan of README lines 72-82 via `[System.IO.File]::ReadAllText(..., UTF8)` | `cols=[24]` for top-level rows, `cols=[4,26]` for nested rows — my three new rows included |
| LF endings preserved (`.gitattributes` not defeated) | same UTF-8 read, `[regex]::Matches($text, "\r\n").Count` | `CRLF count: 0` |
| Blast radius is exactly the allowlist | `git status --porcelain` | ` M .claude/agents/data-engineer-memory.md`, ` M README.md` — nothing else |
| README change is additive only | `git diff --stat` (run before the memory edit) | `1 file changed, 21 insertions(+)`, zero deletions |
| Memory under cap after append | UTF-8 line count of the memory file | 101 physical lines, cap 120 |

## assumed

- That `uv run mypy` and `uv run dbt build` were unnecessary here: no Python and no dbt
  artifact changed. Not run, so not claimed above.
- That "place it where it reads naturally" permits a new top-level `##` heading rather than a
  subsection of `Repo layout`. Top-level matches every other README section's weight.
- That ordering `.claude/` after `requests/` (rather than alphabetically first) is preferable
  because it matches `CLAUDE.md`'s project map, keeping the two maps readable side by side.

## surprised-me

- Recorded to memory, `measured`, tag `tooling-trap`: PowerShell 5.1's `Get-Content` decodes
  UTF-8 as ANSI, so each box-drawing character in an ASCII-art tree measures as **three**
  characters and every column calculation comes out wrong. My first alignment measurement
  reported comment column 30 for a row that is actually at 24. Use
  `[System.IO.File]::ReadAllText(path, [Text.Encoding]::UTF8)` for any alignment or length
  check. This is the read-side twin of the existing `Set-Content`/`Out-File` entry.
- Not recorded anywhere, offered as an observation: the README layout tree is internally
  inconsistent — top-level comments sit at column 24, nested ones at 26. I matched the local
  convention rather than normalising, since normalising was not the task.

## could-not-do

- **`CLAUDE.md` is in my deny set**, and its project map is now the stale one: it lists
  `.claude/skills/` but not `.claude/agents/`, so README and CLAUDE.md disagree about what
  `.claude/` contains. The task named `README.md` only. Routed to `docs-delta`.
- **`docs/data-sources.md` is denied to me**, which is where the leaguegamelog item belongs.
  Routed to `docs-delta` instead. No destructive-git need arose; no package was missing.

## docs-delta

- **leaguegamelog bulk-call belief** (the item I was handed mid-task). This is a *data fact* —
  endpoint shape and call volume — so by my routing rule it goes here, not into agent memory,
  and I deliberately did not write it there. **It is already recorded**: `docs/data-sources.md`
  carries it under "Bulk vs. per-game endpoints" with the same figures (~50 calls for the
  season-wide family vs ~60,000 for per-game box scores) and an explicit `unconfirmed` label.
  Proposed label: `unconfirmed`, unchanged. **No doc change needed** — flagging it as a
  verified no-op so the main thread does not route a duplicate through `/update-docs`.
- **`CLAUDE.md` Project Map is stale.** Its tree lists `.claude/skills/` and omits
  `.claude/agents/`. README now documents the directory; CLAUDE.md still does not mention it.
  Proposed label: `measured`. Main thread's to edit.
- **A referenced ADR does not exist.** `.claude/agents/README.md` cites
  `docs/decisions/0007-write-capable-implementation-subagent.md` for the detection-not-
  prevention trade; `docs/decisions/` currently stops at 0006. It survives the link checker
  only because the citation sits inside a sentence as plain text, not as a markdown link.
  Proposed label: `measured`. I did **not** link that ADR from README for exactly this reason.

## still-open

- **Ambiguity, smaller reading taken.** "Update the tree so the file stays internally
  consistent" — I read this as *add `.claude/` and its two children*. The larger reading I did
  not take: also add `README.md`, `CLAUDE.md`, `.github/`, and `.gitattributes` as tree rows,
  which `CLAUDE.md`'s map lists and README's does not. That would have been a bigger rewrite
  of a section nobody asked me to restructure.
- Once ADR 0007 lands, the `## Implementation agents` section is the natural place to link it,
  next to the detection-not-prevention sentence. One-line follow-up.
- Nothing here spends cloud money or touches prod; no user-run step is pending.

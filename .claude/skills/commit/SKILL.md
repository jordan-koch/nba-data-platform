---
name: commit
description: >-
  Stage the current work, check the docs still describe it, show you exactly what's about to land,
  and commit once you say yes. This is the ONLY sanctioned path by which an agent commits in this
  repo — never run `git commit` ad hoc. Use it whenever a unit of work is finished: "commit this",
  "commit the changes", "let's land this", "/commit", or as the natural end of a pipeline stage.
  It stages deliberately (never a blind `git add -A`), refuses to stage secrets or bulk data, runs
  the doc-drift checks proportionally to what changed, proposes a message, and asks before writing
  anything. It does NOT push and does NOT open a PR — those stay yours. It does NOT run lint,
  types, tests, or dbt build; CI owns those and runs them on the PR.
---

# Commit

## What this produces and why

One commit, on a branch, containing exactly what you meant to land — after the docs have been
checked against it and you've seen the staged list.

The rule this replaces was "agents never commit," which was correct about the risk and wrong about
the friction. The actual hazard isn't an agent committing; it's an agent committing **something you
didn't see**: a stray credential, a 400MB Parquet file, a half-finished refactor swept up by
`git add -A`. So the guard is *deliberate staging plus an explicit yes*, not a blanket prohibition.

**Keep this skill lightweight.** It is a gate, not a pipeline. If it grows a panel, something has
gone wrong.

---

## Step 1 — Survey

```
git status --porcelain --untracked-files=all
git diff HEAD --stat
git branch --show-current
```

**Read the actual diff**, not just the file list. You're about to describe it in a commit message,
and a message that misdescribes its diff is worse than no message.

**Branch check.** If the current branch is `main`, say so and stop for a decision. `main` is
protected and work is supposed to land by PR. Offer to create a branch — `git switch -c
<descriptive-slug>` — and note that this is cheap now and annoying later. Proceed on `main` only if
the user explicitly says to.

## Step 2 — Stage deliberately

**Never `git add -A` or `git add .` without reading the untracked list first.** That single habit
is the one this skill exists to prevent.

Go through the untracked and modified files and decide, per file, whether it belongs in this
commit. Then stage by path.

**Refuse to stage** any of these, and say why rather than staging quietly:

| Refuse | Because |
|---|---|
| Anything under `var/` | Gitignored working root — regenerable, machine-local |
| `.env`, `*.pem`, `*.key`, credentials | This repo is **public**; a leaked secret is permanent in history |
| `*.parquet`, `*.duckdb`, `*.csv`, `*.jsonl` outside `tests/fixtures/` or `transform/seeds/` | The repo holds code and contracts, not bulk data |
| `.user.yml`, `target/`, `dbt_packages/`, `.venv/` | Generated or machine-local |
| Anything you can't explain the presence of | If you don't know why it changed, neither will the reviewer |

Most of these are already in `.gitignore`. If one shows up as untracked anyway, that's a
`.gitignore` gap worth fixing in this same commit — say so.

Then sanity-check what you staged:

```
git diff --cached --stat
```

Scan the staged diff for anything that looks like a credential, an account ID, a bucket name, or a
connection string. `gitleaks` will catch it in CI, but catching it *before* it enters history is
the difference between an edit and a history rewrite.

## Step 3 — Doc drift, proportional to the change

Run the checks in proportion to what actually changed — this is the step that keeps the gate
lightweight.

**Run the full [`/update-docs`](../update-docs/SKILL.md) sweep** when the change touches anything
the docs describe:

- a new or changed directory (the `CLAUDE.md` project map)
- a new convention, constraint, or gotcha (the rules sections)
- a new dbt model, source, or a changed grain (model docs, and the grain-vs-test check)
- a completed phase or a changed setup step (`README.md`)
- anything contradicting an accepted ADR
- a source claim that moved from `unconfirmed` to `verified` (`docs/data-sources.md`)
- a request artifact whose status advanced (the track Index rows)

**Otherwise, do the two-minute version yourself:**

```
uv run pytest tests/test_doc_links.py -q
```

plus a read of `CLAUDE.md`'s project map against the tree. A typo fix in a test does not need the
full sweep, and pretending it does is how a gate becomes something people route around.

If `/update-docs` flags something needing your judgment — a superseded ADR, a grain/test mismatch —
**stop and surface it.** Those are not commit-blockers by policy, but they're decisions, and a
commit is a bad place to make one silently.

## Step 4 — Propose, then ask

Show the user three things:

```
STAGED    — the file list, grouped by area, with the stat line
DOCS      — what the drift check did: updated / flagged / clean
MESSAGE   — the proposed commit message
```

**Message format:** an imperative subject line under ~72 characters saying what the commit *does*,
and — when the change isn't self-evident — a body explaining *why*, wrapped at 72. The diff already
shows what changed; the body is for what the diff can't say.

```
Add bronze layer for league game logs

The bulk endpoint returns a full season per call, so the backfill is ~50
requests rather than ~60k. Fixtures cover 2019-20 (bubble) and 2011-12
(lockout) since both break the 82-game assumption.
```

Then **ask, explicitly, and wait.** Not a rhetorical "shall I commit?" trailing a wall of text — a
real question with the staged list visible above it. The user's yes is the gate.

## Step 5 — Commit

On approval:

```
git commit -m "<subject>" -m "<body>"
```

Hard rails, no exceptions without an explicit request:

- **Never `--no-verify`.** If a hook fails, that's the hook working.
- **Never `--amend`.** Amending rewrites history that may already be pushed. A follow-up commit is
  almost always right; if the user genuinely wants an amend, they'll say so.
- **Never `push`.** Pushing publishes to a public repo — outward-facing, and the user's call.
- **Never `-A` at this stage.** Staging happened in Step 2, deliberately.

Then report the short SHA and hand back the push command:

```
git push -u origin <branch>
```

If the branch has no upstream yet, say so — the `-u` matters and is easy to forget.

---

## What good looks like

- **Nothing landed that the user didn't see.** The staged list was shown before the yes, not after.
- **Staging was per-path, not wholesale.** `git add -A` appears nowhere in the transcript.
- **The message describes the diff.** Someone reading `git log` in six months learns why, not just
  what.
- **The doc check was sized to the change.** Full sweep on a new model; link check on a typo fix.
- **It committed and stopped.** No push, no PR, no amend, no `--no-verify`.

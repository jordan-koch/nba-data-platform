# 0006 — Public repository from the first commit

**Status:** accepted · 2026-08-12

## Context

The repository is portfolio work — employers need to be able to read it. The question was
whether to develop privately and open it later, once it looked finished.

The deciding factor is that **git history is permanent.** A secret, account ID, or bucket name
committed while private is still in the history after being deleted from `HEAD`. Going public
later means either accepting that exposure, rewriting history, or starting over — and this is
typically discovered at the worst possible moment.

## Decision

**Public from the first commit**, under `jordan-koch/nba-data-platform`.

Supporting choices:

- Authorship uses the GitHub noreply address (`24264704+jordan-koch@users.noreply.github.com`),
  set in **repo-local** git config rather than inherited from global. Attribution works normally;
  the personal address is never published to anyone who clones.
- Credentials via gitignored `.env`, with `.env.example` committed.
- Account IDs and bucket names treated as secrets — no reason to publish them, and
  parameterizing them is correct practice regardless.
- `gitleaks` runs in CI against full history, and a structural test asserts `.env` is ignored.
- Terraform state in S3, never local.
- `main` protected; changes land by PR with green checks.

## Consequences

**Buys:**

- **Secret discipline is non-optional from commit one** — the habit is enforced by the situation
  rather than by remembering.
- **The commit history becomes portfolio material.** A repo that visibly evolved, with real PRs
  and ADRs written as decisions were made, reads very differently from one that appeared fully
  formed.
- No future migration, no history rewrite, no scrubbing.

**Costs:**

- **Every mistake is public**, including early ones. Accepted deliberately — the alternative is a
  history that's been curated into dishonesty.
- Branch protection means self-approved PRs, which is mild friction for solo work. Kept anyway,
  because a repo whose settings say the rules are optional is making a statement.
- Ongoing vigilance: one careless paste of a connection string is a real incident, not a
  hypothetical one.

**Forecloses:** publishing any NBA data through this repo. Code, config, docs, and small test
fixtures only. That constraint is independently desirable — bulk data doesn't belong in git —
but it is now a hard rule rather than a preference.

## Alternatives considered

**Private now, public at launch.** The intuitive choice, and the trap described above. Rejected
on the history-permanence problem alone.

**Two repos — private infrastructure, public code.** Solves the exposure problem. Rejected as
ongoing complexity for a solo project, and it fragments the history that is itself part of the
value.

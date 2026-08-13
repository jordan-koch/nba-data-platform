# Ops

Repository governance, kept as code rather than as clicks in a settings page.

## Why this is a file

`main` is protected with `enforce_admins: true`, which means **the repo owner cannot push to it
either.** That's deliberate — protection an admin can shrug off is theatre — but it has a
consequence: if `main` ever breaks in a way the normal PR path can't fix, recovery requires
*removing* the protection, pushing, and putting it back.

"Putting it back" from memory, under pressure, is how a repo quietly ends up less protected than it
was. So the configuration lives here and gets re-applied from the file.

The secondary reason is the same one the ADRs exist for: a reviewer can see what the rules are
without being handed admin access to look.

## `branch-protection.json`

The protection ruleset for `main`. Apply or restore it with:

```bash
gh api --method PUT repos/jordan-koch/nba-data-platform/branches/main/protection \
  --input ops/branch-protection.json
```

Read the current live state to compare:

```bash
gh api repos/jordan-koch/nba-data-platform/branches/main/protection
```

### What each setting is doing

| Setting | Value | Why |
|---|---|---|
| `enforce_admins` | `true` | Rules apply to everyone. The point of the exercise. |
| `required_status_checks.contexts` | the three CI jobs | Nothing merges on a red build |
| `required_status_checks.strict` | `true` | Branch must be current with `main` before merging |
| `required_approving_review_count` | `0` | **Not laxness** — GitHub forbids approving your own PR, so any value above 0 deadlocks a solo repo. A PR is still required; it just doesn't need a second human. |
| `required_linear_history` | `true` | Matches the squash/rebase-only merge policy |
| `required_conversation_resolution` | `true` | Review comments get resolved, not scrolled past |
| `allow_force_pushes` / `allow_deletions` | `false` | History is append-only |

### The gotcha

The `contexts` array matches CI job **display names**, not job IDs — `Lint, types, tests`, not
`python`. Rename a job in [`ci.yml`](../.github/workflows/ci.yml) without updating this file and the
protection waits forever for a check that will never report. The PR simply never becomes mergeable,
with no error explaining why.

Change both, in the same commit.

## Emergency recovery

Only when `main` is broken and the fix genuinely can't go through a PR:

```bash
# 1. Lift protection
gh api --method DELETE repos/jordan-koch/nba-data-platform/branches/main/protection

# 2. Push the fix

# 3. Put it back — immediately, same session
gh api --method PUT repos/jordan-koch/nba-data-platform/branches/main/protection \
  --input ops/branch-protection.json
```

Step 3 is not optional and not "later."

## Settings not captured here

Some repo configuration isn't part of the protection ruleset and was applied directly. Recorded so
it's reproducible:

```bash
gh repo edit jordan-koch/nba-data-platform \
  --enable-wiki=false --enable-projects=false \
  --enable-merge-commit=false --enable-squash-merge=true --enable-rebase-merge=true \
  --delete-branch-on-merge=true

gh api --method PUT repos/jordan-koch/nba-data-platform/vulnerability-alerts
gh api --method PUT repos/jordan-koch/nba-data-platform/automated-security-fixes
```

Secret scanning and push protection are on by GitHub's default for public repositories. Actions
default workflow token permissions are read-only.

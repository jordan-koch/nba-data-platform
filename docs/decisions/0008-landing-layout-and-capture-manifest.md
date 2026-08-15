# 0008 — Landing layout, the capture manifest, and latest-capture-wins

**Status:** accepted · 2026-08-15

## Context

`CLAUDE.md` claims the landing zone's immutability is "what makes data-incident triage tractable,"
and `transform/models/bronze/README.md:17-19` claims you can always diff bronze against the raw
payload. Until this slice, nothing implemented the record that makes either claim checkable. Both
were prose.

At the same time, box scores get **restated** — the source corrects them after the fact. So a
re-pull of a season already landed produces a second, *different* payload for the same partition.
That puts two stated rules in direct tension:

- If raw is never mutated, two payloads now exist for one partition and something must decide which
  one bronze sees.
- If a re-pull overwrites, the landing zone is no longer immutable and the diff-against-raw
  invariant is gone.

Left undecided this silently doubles row counts or silently breaks immutability, and **both
plausible choices are wrong if unstated**. Three things therefore had to be settled together,
because each constrains the others: the path layout, what a capture records about itself, and how
bronze resolves two captures of one partition.

Constraints in play at the time:

- `var/` is gitignored, so the layout is **invisible to a repo reader**. A convention nobody can see
  is one the second dataset will not follow.
- Windows development, Linux CI. Paths must be legal on both.
- `transform/models/bronze/README.md:10` — *"No joins. A bronze model reads exactly one source."* So
  per-row capture provenance cannot come from a join to a sidecar.
- [ADR 0003](0003-iceberg-as-storage-substrate.md) defers S3 and Iceberg but does not cancel them.
  Whatever layout is chosen now is the one a later phase has to migrate.
- The repo had **zero runtime dependencies** before this slice.

## Decision

Five parts, decided as one.

**1. Landing paths are S3-key-shaped, Hive-partitioned prefixes.**

```
<landing_root>/nba_stats/league_game_log/season=2003-04/grain=player/season_type=regular/capture=20260815T134506Z/
    payload.json
    manifest.json
```

Two bare segments name the source and the endpoint; the four trailing segments are `key=value`
pairs. The prefix is rendered by `landing_key()` in `src/nba_platform/config.py` and never composed
by a caller, so there is one definition of the shape rather than one per module.

**2. The capture stamp in the path is colon-free compact UTC** — `YYYYMMDDTHHMMSSZ`. A colon is
illegal in a Windows path, and a layout that works in CI and fails on the developer's machine is
worse than one that works nowhere. The true tz-aware ISO-8601 timestamp lives inside `manifest.json`,
where punctuation is safe.

**3. Every capture writes `manifest.json` beside its payload**, carrying the endpoint, the full
parameter dict, a tz-aware `captured_at`, the HTTP status, the row count, the sha256 of
`payload.json`, the `nba_api` version, and elapsed seconds. This is what makes immutability
*auditable* rather than merely asserted.

**4. The payload is the raw JSON envelope, verbatim — never a DataFrame round-trip.** `get_dict()`
returns the source's own `resource` / `parameters` / `resultSets` structure intact — with
`resultSets[0]` carrying `name` / `headers` / `rowSet` — so landing raw costs nothing.

> **`verified`** · 2026-08-15 · The accessor exists and returns the envelope un-round-tripped.
> Confirmed twice: by introspection during planning, and again against the *resolved* package after
> `uv lock` pinned it — `nba_api` **1.11.4** exposes `get_dict` and `get_json` on `LeagueGameLog`.
> Decision 8's raw-JSON path is satisfiable without a DataFrame, so the bronze decode is written
> against a known envelope rather than a guess.

Two honest limits, recorded rather than glossed. First, `get_dict()` is a re-serialization of the
already-parsed response body, not the literal wire bytes. Second — **`measured`** 2026-08-15 by
reading the installed source — `LeagueGameLog.get_request()` both sends *and* parses, indexing the
envelope's own result set, so a non-conforming body raises inside the call instead of being
returned. This transport therefore cannot *land* an error response; capturing one for the fixture
corpus needs the lower-level `NBAStatsHTTP.send_api_request`.

**5. Bronze resolves two captures of one partition by latest-capture-wins** on the natural key,
ordered by the capture stamp **recovered from the path**, with the capture directory name as the
tiebreak. Provenance rides in the path and is projected by DuckDB, never joined from the manifest.

Write-once follows from all five: an existing partition is **skipped, not overwritten**, and a
deliberate re-pull is an explicit `--recapture` that writes a *new* `capture=` directory beside the
first and never touches a landed byte.

## Consequences

**Buys:**

- **Immutability stops being a claim.** The sha256 in each manifest plus a double-run hash-set
  comparison over the whole landed tree makes it a test that can fail.
- **Restatement and immutability coexist** without either being violated — the correction lands
  beside the original, and bronze picks the newer one deterministically.
- **Bronze stays 1:1 and join-free**, honouring its own layer contract on the repo's very first
  bronze model rather than breaking it immediately.
- **The ADR 0003 migration is a root swap.** These are S3 keys already; only `<landing_root>` moves.
- **Skip-if-present is a free checkpoint** at this volume, which is why no checkpoint store was
  built (Decision 7).

**Costs:**

- **A re-pull permanently doubles disk for that partition, and nothing reclaims it.** There is no
  compaction, no retention policy, no vacuum, and no plan for one. A season re-pulled quarterly for
  a year is five copies of that season. At the pilot's six calls this is megabytes and genuinely
  irrelevant; at the full 23-season widening with play-by-play it stops being irrelevant, and the
  decision to add retention will then get made under storage pressure rather than deliberately here.
- **`nba_api` drags pandas and numpy into a repo that had zero runtime dependencies.** Tens of
  megabytes installed, to support a config layer that needs none of it, purely because `nba_api` is
  the only transport that reaches `stats.nba.com` from this environment — a raw HTTP request times
  out. Every future `uv sync` in every future CI run pays that weight. Confining the import to
  `client.py` behind one declared mypy override bounds the *type* damage; it does nothing about the
  bytes.
- **One instant now has two representations** — the colon-free stamp in the path and the ISO
  timestamp in the manifest — and nothing but care keeps them agreeing. The path form is also not
  parseable by a naive ISO reader, which will surprise someone.
- **Latest-capture-wins is only as good as the clock.** Two captures can no longer *share* a
  directory name — the writer claims one with an exclusive `mkdir` and advances the stamp by a
  second rather than collide, and the offline two-run proof hit that path for real rather than
  hypothetically. The residue is that a capture's true `captured_at` in the manifest and the
  possibly-advanced `capture=` segment in its path can differ by a second or two, and both are
  recorded so the disagreement is visible rather than silent. A clock that steps *backwards* still
  makes an older capture win, and nothing here detects that.

- **An aborted capture leaves an orphan that the bronze glob would read.** The payload is written
  first and the manifest second, so the manifest is the completeness marker — which means a process
  killed between the two writes leaves a `payload.json` with no manifest beside it. Skip-if-present
  correctly ignores it, but the bronze source globs `capture=*/payload.json` and never consults a
  manifest, so it *would* pick the orphan up. Nothing in this package deletes from the landing zone
  by design, so clearing one is a human action before a `--target local` build. The failure is at
  least not silent corruption in either direction: a fully-written payload is valid data that is
  merely unaudited, and a truncated one fails the JSON read loudly.
- **Hive partitioning is inferred here, not verified.** That DuckDB's `read_json_auto(...,
  hive_partitioning = true)` projects these segments as columns is a belief at the time of writing;
  the documented fallback is `filename = true` plus `regexp_extract` over the path. The Phase 4
  spike settles it before any model depends on it, and this ADR should be read as *unconfirmed on
  that one point* until it does.

**Forecloses:** nothing permanently — but changing the layout after data is landed means re-landing
it, because the partition segments are load-bearing for bronze rather than decorative.

## Alternatives considered

**Overwrite the partition on re-pull.** By far the simplest, and what most pipelines do. Rejected
because it destroys the ability to diagnose a data incident by diffing the payload that produced the
bad number against the one that replaced it — which is the entire stated purpose of having an
immutable landing zone at all.

**Join bronze to the manifest sidecar to get `captured_at`.** The obvious way to get per-row
provenance. Rejected because `transform/models/bronze/README.md:10` forbids a bronze model reading
more than one source, and breaking a layer contract on the first model written under it sets the
precedent every later model copies.

**Land the DataFrame as Parquet or CSV.** Smaller and directly queryable. Rejected because a pandas
re-serialization means "immutable raw" is not raw: typing decisions get made *before* landing rather
than in bronze where they can be reviewed, and `game_id`'s leading zeros are precisely what a
DataFrame round-trip destroys.

**Flat filenames with a timestamp suffix** (`league_game_log_2003-04_player_20260815.json`).
Rejected because the segments cannot be projected as partition columns, and because it does not
become an S3 key layout without a rewrite.

**A colon-bearing ISO stamp in the path.** More readable. Rejected outright: it fails on Windows,
where half this project is developed.

**A standalone checkpoint store**, per `docs/data-sources.md:34`. Rejected per Decision 7 — a
six-call backfill that finishes in seconds has no hour six to resume from. Revisit at the ~30,000
play-by-play calls that phase already names.

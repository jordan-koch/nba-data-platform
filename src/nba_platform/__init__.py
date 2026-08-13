"""NBA data platform — extraction, landing, and pipeline support code.

Transformation lives in `transform/` (dbt), not here. This package covers the
extract-and-land half: talking to source APIs, enforcing polite request pacing,
checkpointing long backfills, and writing immutable raw payloads to the landing
zone.

Submodules arrive with the feature requests that need them — see
`requests/feature-requests/README.md`.
"""

__version__ = "0.1.0"

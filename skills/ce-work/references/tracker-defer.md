# Tracker Defer Execution

Use when the Residual Work Gate must file actionable findings. Interactive mode may ask; headless mode never prompts and returns structured `filed`, `failed`, and `no_sink` buckets.

## Detect Once

Use tracker conventions already in context, then obvious repository documentation and available connectors/APIs/CLIs. Probe only when filing is imminent and cache the result:

```text
{ tracker_name, confidence, named_sink_available, any_sink_available }
```

Prefer the named project tracker. If unavailable, use GitHub Issues through authenticated `gh` when issues are enabled. Otherwise retain the finding in the review report interactively or return it in `no_sink` headlessly. A missing binary or environment variable alone does not prove a connector/API is unavailable.

## Compose Tickets

Each ticket includes the merged title, plain-language impact, suggested fix, direct evidence, PR URL when present or the current Jujutsu bookmark/change ID, severity, confidence, reviewers, and stable finding fingerprint. Respect tracker body limits while preserving the fingerprint and artifact path.

Ticket prose is not a Jujutsu change description. Do not apply repository-description templates to tickets.

On failure, interactive mode offers one retry, next sink, or recorded skip. Headless mode advances through the chain and records every failure. Backfill a later PR URL best-effort. Never drop a finding silently.

GitHub Issue creation and PR updates use `gh`; repository synchronization remains exclusively `jj git fetch` and `jj git push`.

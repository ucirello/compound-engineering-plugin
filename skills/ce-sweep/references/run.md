# Sweep run phases (2a-2i)

Required read before Phase 2 of `ce-sweep`. The body carries the ordering invariant, the boundaries, and the stop classes; this file carries the full detail of each phase.

## Interaction method

Default to the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Never silently skip a question you owe the user; if no blocking tool exists in the harness, the run is non-interactive. Ask one question at a time — the decision round (2h) may group by category but still asks one blocking question per category.

## Config keys

- `feedback_sources` — list of source entries; each carries a `type` (`slack`, `github-issues`, `email`), its target, the standing-approved ack action, an optional close-out action, and an optional `sensitive: true`. Presence of this key means the skill is configured.
- `sweep_state_path` — path to the state file, established at setup; fallback `<root>/feedback-sweep/state.yml`. A tracked workspace path means recorded mode (the state file is included in each sweep revision and must not be ignored); a path under `<workspace-root>/.tmp/rocketclaw/` means workspace-local mode (the state file is never recorded; only the plan is).
- `sweep_lease_ttl_minutes` — single-writer lease staleness threshold; default `60`. Passed to `lease-acquire` in 2a.
- `sweep_shared_bookmark` — `true` when the state file is published through a shared bookmark used by multiple workspaces (see 2a topology); default `false`. Resolve this key through the ordinary config cascade first. Only when it is unset in both layers, resolve the legacy `sweep_shared_branch` alias through that cascade. Thus `sweep_shared_bookmark` wins when both names exist; config writes use only `sweep_shared_bookmark`.
- `sweep_ack_cap` — integer circuit-breaker threshold; default `25`.

## Run identity

Resolve once and reuse for the entire run:
- `<state>` = `sweep_state_path` from config (fallback `<root>/feedback-sweep/state.yml`).
- `<writer>` = a run-unique writer id identifying harness + session + host, e.g. `sweep-<host>-<session>-<YYYY-MM-DD>`. Use the same string for every state-engine call this run.
- `<run-id>` = a short unique token for scratch paths, e.g. the date plus a random suffix.

## Engine invocation

Every Bash call that runs the bundled engine sets `SKILL_DIR` inline (shell state does not persist between calls):

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/sweep-state.py" <subcommand> --state <state> ...
```

#### 2a. Acquire lease + validate

`lease-acquire --state <state> --writer <writer> --ttl-minutes <sweep_lease_ttl_minutes>`:
- `LOCKED` — another live writer holds it. Record the outcome and stop: `run-record --state <state> --writer <writer> --outcome aborted-locked --counts '{}' --timestamp <ISO now>`, report that a concurrent sweep is running, and exit. (This record is safe against the mid-sweep holder: the engine serializes every state write with an OS advisory lock, so it cannot clobber the holder's concurrent upserts — see `references/state-schema.md`.)
- `STALE-RECLAIMED` — an expired lease was taken over; proceed, and note the takeover in the final summary.
- `OK` — proceed.

**Shared-bookmark topology** (`sweep_shared_bookmark: true`): before any source-side write, identify the configured shared bookmark, remote, and tracked remote bookmark from the project's active conventions and current `jj log`, `jj bookmark list --all-remotes`, and `jj git remote list` output. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The mandated sentence's `git log` wording is not an operational instruction; inspect history with `jj log`. Runtime project instructions and description syntax inferred from `jj log` win. Preserve the requirement that the description communicate lease acquisition while adapting its syntax to those conventions; apply compatible Go guidance only to quality, clarity, and structure, and impose no fixed prefix, type, scope, subject, body, layout, template, or example. Record only `<state>` with path-limited `jj commit`; the recorded revision is then `@-`. Move the shared bookmark to `@-` and publish only it with `jj git push --remote <remote> --bookmark <bookmark>`. Confirm after `jj git fetch --remote <remote>` that the tracked remote bookmark contains the lease. If publication is rejected, fetch and inspect the remote state under the existing lease-owner and expiry protocol before rebasing or republishing. Rebase and retry only when the fetched state proves no competing live lease, then reacquire against that state; if another live writer owns the lease or the race is lost, record `aborted-locked` and stop without overwriting.

Then `validate --state <state>` (a lease-agnostic repair): note in the summary any ids it downgrades from `closed` to `fix_pending`.

#### 2b. Fetch each source

For each entry in `feedback_sources`, dispatch a generic subagent at the **extraction tier** (`references/model-tiers.md`) seeded with:
- the matching persona file contents (`references/sources/<type>.md`),
- the source's config entry verbatim,
- the current cursor from `cursor-get --state <state> --source <source-id>`.

The persona returns mapped items (`id`, `origin`, `author_class`, `body`, `media`, identity-scoped `existing_ack`, `existing_closeout`) or one of its degrade/skip sentences. Personas report facts and never advance cursors.
- **Skipped source** (read tools unavailable): drop it this run, note in the summary.
- **Write-degraded source** (read works, no ack-write tool): upsert its items as `ack_deferred` and do NOT advance the cursor past them — they get acked on a later run once write capability returns.

#### 2c. Circuit breaker (before any acknowledgment batch)

Count new unacknowledged items per source. If the count exceeds `sweep_ack_cap`:
- interactive -> ask whether to proceed with acking that many;
- non-interactive -> upsert the whole batch as `ack_deferred`, do NOT ack, and flag it prominently in the summary.

#### 2d. Acknowledge each item — correctness core

Process each new item in cursor order. This ordering is an invariant; do not reorder it or batch across the read-back:

1. If the source's config entry has `approved: false` (the user declined standing approval for source-side writes), skip the ack write entirely and upsert the item as `ack_deferred` — never write to a source the user did not approve, even when the write tool is available. Otherwise: if the item's `existing_ack` (own identity) is true, skip the ack write; else perform the source's configured ack action at the source.
2. Read back and confirm the ack is visible at the source before trusting it.
3. `upsert-item --state <state> --id <id> --source <source-id> --json <item-json> --writer <writer>`. Include `"sensitive": true` in the item JSON when the source's config entry is marked sensitive — the engine drops `body`/`quote` before writing.
4. `cursor-advance --state <state> --source <source-id> --to <item's own cursor value> --past-item <id> --writer <writer>` — only after the item is durably in state. Never advance past an item not yet upserted.

A failed ack write -> upsert the item as `ack_deferred` and hold the cursor (do not advance past it). A `LEASE-LOST` from any engine call means another writer took over — stop writing, record `partial` at wrap-up, and exit.

#### 2e. Media

Resolve and create media scratch with this shell block, substituting the current run id. It uses the JJ workspace's ignored `.tmp/rocketclaw/` tree and falls back to local `.tmp/rocketclaw/` when no JJ workspace is available:

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd)";
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw/ce-sweep";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
MEDIA_DIR="$SCRATCH_ROOT/<run-id>";
(umask 077; mkdir -p "$MEDIA_DIR") || exit 1; chmod 700 "$MEDIA_DIR" || exit 1;
```

Pass absolute artifact paths beneath `$MEDIA_DIR` to subagents. If that block exits without a usable `$MEDIA_DIR`, media is the only thing lost: upsert every item carrying `media` as `needs_download` (counting the attempt), note the scratch failure in the summary, and continue the run at 2f — state is still writable, so the run does not stop.

For each new item carrying `media`:
- Download attachments into `$MEDIA_DIR`; raw media is never recorded in a revision. A download failure -> set the item `needs_download` and continue.
- Dispatch one generic subagent per recording, in parallel, at the **generation tier**, using `references/subagent-template.md` filled from `references/agents/media-analyzer.md`. Fill the template's `{skill_dir}` slot with the same absolute ce-sweep skill directory you resolve for your own `SKILL_DIR` Bash calls (a fresh subagent does not inherit your shell state, so it cannot run the bundled analyzer without being told the path). Pass the absolute media PATHS, a scratch artifact path, and the item's `sensitive` flag; collect the compact 1-2 line summary each returns. A subagent failure -> set the item `needs_analysis`, retain the media, and continue.
- Track attempts on the item (a `media_attempts` count upserted on each try). After 3 failed attempts across runs (`needs_download`/`needs_analysis`), set the item `manual_stuck` and list it separately — out of the routine nag.

#### 2f. Fix verification

For each `fix_pending` item, resolve its claimed fix ref and verify it landed on the default bookmark. The fix ref originates from untrusted feedback content, so **validate its shape before it reaches any `jj`/`gh` command**: accept only a bare PR number (`#?\d+`), a Jujutsu change ID (`[k-z]{7,64}`), or a commit ID (`[0-9a-f]{7,64}`), and treat anything else as an unresolved claim. This blocks argument and revset injection.
- For a PR, strip an optional leading `#`, quote the number, preserve `gh pr view`, and require its merge time and base to match the repository's default branch. Resolve the merge commit returned by GitHub as a Jujutsu revision after `jj git fetch`.
- For a change or commit ID, pass the validated token to `change_id(<id>)` or `commit_id(<id>)` respectively, intersect it with `::trunk()`, and require `jj log` to return exactly one revision. Use `jj log` and the project's active conventions to confirm `trunk()` identifies the actual default bookmark; stop as unresolved if it does not.
- Same `approved: false` guard as 2d: a source the user did not approve for writes receives no close-out action — advance its verified item's status in state only.
- Verified -> perform the source's configured close-out action (same write -> read-back -> confirm discipline as 2d), then `upsert-item` with `status: closed` carrying all three evidence fields: `fix_ref`, `verified_merge_sha`, `verified_at`. Store the stable commit ID of the verified Jujutsu revision in the compatibility-named field. Close-out is terminal.
- Unverified claim -> the item stays open; record the claim on the item, but do not close.
- Item deleted at source -> set `source_gone`.

#### 2g. Plan reconciliation

Read `references/plan-template.md` and follow it. Target the stable path `<root>/plans/feedback-sweep-plan.md`.

**Rotation check first.** Treat the historical source alias formed by prefixing `ce-` to `sweep` as equivalent when reading an existing file, but write only `product_contract_source: sweep`. If the file exists and its frontmatter is not requirements-only with either recognized sweep source, archive it untouched to a dated sibling `<root>/plans/feedback-sweep-plan-YYYY-MM-DD.md` and write a fresh plan from the template. Never overwrite an unrelated plan in place.

Rewrite ONLY the machine-owned region — the `date` frontmatter key, `### Summary`, the `<!-- sweep-items:start -->` / `<!-- sweep-items:end -->` marker region, and `### Outstanding Questions` (matching the template's reconciliation rules); never read or write inside the human-owned notes region. Append new actionable items with their state ids, drain items that are now `closed`, and land any non-interactive-deferred decisions in the Outstanding Questions section.

#### 2h. Decision round

Interactive only. For items needing a product call, ask the user — grouped by category, one blocking question per category — and fold the answers into the plan. Non-interactive skips this; the deferrals are already in the plan's Outstanding Questions.

#### 2i. Wrap-up

Render the handoff invocation exactly as the skill body's 2i section states.

- **Record a revision.** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The mandated sentence's `git log` wording is not an operational instruction; inspect history with `jj log`. Runtime project instructions and description syntax inferred from `jj log` win. Preserve the requirement that the description communicate the completed feedback sweep while adapting its syntax to those conventions; apply compatible Go guidance only to quality, clarity, and structure, and impose no fixed prefix, type, scope, subject, body, layout, template, or example. Use path-limited `jj commit` for only `<root>/plans/feedback-sweep-plan.md` plus `<state>` when tracked, so unrelated working-copy changes remain outside the recorded revision; workspace-local state under `.tmp/rocketclaw/` is never included. A revision-recording failure is reported, not fatal. In local mode, do not move or publish a bookmark. In shared-bookmark mode (`sweep_shared_bookmark: true`), fetch the configured remote, rebase the recorded revision `@-` and its working-copy descendant onto `<bookmark>@<remote>`, move the bookmark to `@-`, and publish only that bookmark.
- **Record the run.** `run-record --state <state> --writer <writer> --outcome <completed|partial|failed> --counts '<per-source JSON>' --timestamp <ISO now>`.
- **Release.** `lease-release --state <state> --writer <writer>`.
- **Summary** (always emit): new items by source; recordings analyzed, each with its one-line finding; closed items with their fix evidence; the `ack_deferred` / `manual_stuck` / needs-attention list; any circuit-breaker or stale-reclaim note; and always the plan path with the handoff line:

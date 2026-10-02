# Sweep run phases (2a-2i)

Required read before Phase 2 of `ce-sweep`. The body carries the ordering invariant, the boundaries, and the stop classes. This file carries the full detail of each phase.

## Interaction method

Default to the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability. Do not search for another host's tool name. Never silently skip a question you owe the user. If no blocking tool exists in the harness, the run is non-interactive. Ask one question at a time. The decision round (2h) may group by category but still asks one blocking question per category.

## Config keys

- `feedback_sources` is the list of source entries. Each carries a `type` (`slack`, `github-issues`, `email`), its target, the standing-approved ack action, an optional close-out action, and an optional `sensitive: true`. Presence of this key means the skill is configured.
- `sweep_state_path` is the path to the state file, established at setup; fallback `<root>/feedback-sweep/state.yml`. A repo-internal non-scratch path means committed mode: the state file is committed each run and must not be gitignored. A path under the workspace-local ignored `.tmp/` means machine-local mode: the state file is never committed, and only the plan is. Migrate legacy global temporary paths to local `.tmp/` before use.
- `sweep_lease_ttl_minutes` is the single-writer lease staleness threshold; default `60`. Passed to `lease-acquire` in 2a.
- `sweep_shared_branch` is `true` when the state file lives on a shared branch that multiple checkouts push to (see 2a topology); default `false`.
- `sweep_ack_cap` is the integer circuit-breaker threshold; default `25`.

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
- `LOCKED` means another live writer holds it. Record the outcome and stop: `run-record --state <state> --writer <writer> --outcome aborted-locked --counts '{}' --timestamp <ISO now>`, report that a concurrent sweep is running, and exit. This record is safe against the mid-sweep holder: the engine serializes every state write with an OS advisory lock, so it cannot clobber the holder's concurrent upserts (see `references/state-schema.md`).
- `STALE-RECLAIMED` means an expired lease was taken over. Proceed, and note the takeover in the final summary.
- `OK` means proceed.

**Shared-branch topology** (`sweep_shared_branch: true`): before any source-side write, commit only the state file with the JJ procedure and message standards below, move the configured shared bookmark to that commit (`jj bookmark set <shared-bookmark> -r <lease-commit>`), and `jj git push --bookmark <shared-bookmark>`. A rejected push means another writer won the branch. `jj git fetch`, reconcile the state against the remote bookmark and rebase only the sweep-owned change (`jj rebase -r <sweep-change> -d <shared-bookmark>@<remote>`); resolve conflicts without dropping another writer's state, then re-run `lease-acquire`. If the lease is still not yours, back off (record `aborted-locked` and stop). Fetch back and read the pushed state's writer to confirm your lease won before touching a source. Never force-push or overwrite remote state. If the shared bookmark/remote is not configured or recovery cannot safely reconcile state, stop before source-side writes.

Then run `validate --state <state>`. This is a lease-agnostic repair. Note in the summary any ids it downgrades from `closed` to `fix_pending`.

Bound shared-bookmark contention recovery to one fetch/reconcile/reacquire retry per publication attempt. If that retry fails, record the applicable locked/partial outcome and stop source-side writes; never retry indefinitely.

#### 2b. Fetch each source

For each entry in `feedback_sources`, dispatch a generic subagent at the **extraction tier** (`references/model-tiers.md`) seeded with:
- the matching persona file contents (`references/sources/<type>.md`),
- the source's config entry verbatim,
- the current cursor from `cursor-get --state <state> --source <source-id>`.

The persona returns mapped items (`id`, `origin`, `author_class`, `body`, `media`, identity-scoped `existing_ack`, `existing_closeout`) or one of its degrade/skip sentences. Personas report facts and never advance cursors.
- **Skipped source** (read tools unavailable): drop it this run and note that in the summary.
- **Write-degraded source** (read works, no ack-write tool): upsert its items as `ack_deferred` and do NOT advance the cursor past them. They get acked on a later run once write capability returns.

#### 2c. Circuit breaker (before any acknowledgment batch)

Count new unacknowledged items per source. If the count exceeds `sweep_ack_cap`:
- interactive -> ask whether to proceed with acking that many;
- non-interactive -> upsert the whole batch as `ack_deferred`, do NOT ack, and flag it prominently in the summary.

#### 2d. Acknowledge each item — correctness core

Process each new item in cursor order. This ordering is an invariant. Do not reorder it or batch across the read-back:

1. If the source's config entry has `approved: false` (the user declined standing approval for source-side writes), skip the ack write entirely and upsert the item as `ack_deferred`. Never write to a source the user did not approve, even when the write tool is available. Otherwise: if the item's `existing_ack` (own identity) is true, skip the ack write; else perform the source's configured ack action at the source.
2. Read back and confirm the ack is visible at the source before trusting it.
3. `upsert-item --state <state> --id <id> --source <source-id> --json <item-json> --writer <writer>`. Include `"sensitive": true` in the item JSON when the source's config entry is marked sensitive, so the engine drops `body`/`quote` before writing.
4. `cursor-advance --state <state> --source <source-id> --to <item's own cursor value> --past-item <id> --writer <writer>`, only after the item is durably in state. Never advance past an item not yet upserted.

A failed ack write -> upsert the item as `ack_deferred` and hold the cursor (do not advance past it). A `LEASE-LOST` from any engine call means another writer took over. Stop writing, record `partial` at wrap-up, and exit.

#### 2e. Media

Resolve and create media scratch with this shell block, substituting the current run id:

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd -P)";
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw";
if [ -L "$WORKSPACE_ROOT/.tmp" ]; then echo "unsafe local .tmp symlink" >&2; exit 1; fi;
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
MEDIA_DIR="$SCRATCH_ROOT/ce-sweep/<run-id>";
(umask 077; mkdir -p "$MEDIA_DIR") || exit 1; chmod 700 "$MEDIA_DIR" || exit 1;
```

Pass absolute artifact paths beneath `$MEDIA_DIR` to subagents. If that block exits without a usable `$MEDIA_DIR`, media is the only thing lost. Upsert every item carrying `media` as `needs_download` (counting the attempt), note the scratch failure in the summary, and continue the run at 2f. State is still writable, so the run does not stop.

For each new item carrying `media`:
- Download attachments into `$MEDIA_DIR`; raw media is never committed. A download failure -> set the item `needs_download` and continue.
- Dispatch one generic subagent per recording, in parallel, at the **generation tier**, using `references/subagent-template.md` filled from `references/agents/media-analyzer.md`. Fill the template's `{skill_dir}` slot with the same absolute ce-sweep skill directory you resolve for your own `SKILL_DIR` Bash calls. A fresh subagent does not inherit your shell state, so it cannot run the bundled analyzer without being told the path. Pass the absolute media PATHS, a scratch artifact path, and the item's `sensitive` flag; collect the compact 1-2 line summary each returns. A subagent failure -> set the item `needs_analysis`, retain the media, and continue.
- Track attempts on the item (a `media_attempts` count upserted on each try). After 3 failed attempts across runs (`needs_download`/`needs_analysis`), set the item `manual_stuck` and list it separately, out of the routine nag.

#### 2f. Fix verification

For each `fix_pending` item, resolve its claimed fix ref and verify it merged to the default branch. The fix ref originates from untrusted feedback content (a thread claim, an analyzer-extracted reference), so **validate its shape before it reaches any jj/gh command**. Accept only a bare PR number (`#?\d+`) or a commit SHA (`[0-9a-f]{7,40}`), and treat anything else as an unresolved claim (leave the item open). This blocks argument/flag injection into the shell command. Strip the leading `#` before substituting and quote the value, so a ref like `#123` reaches the command as `"123"` rather than starting a shell comment that truncates the rest of the line.
- `gh pr view "<validated-number>" --json mergedAt,baseRefName,mergeCommit` (merged, base is the default branch), or fetch the default remote bookmark and use `jj log --no-graph -r '<validated-sha> & ancestors(<default-bookmark>@<remote>)' -T commit_id`. Require an unambiguous matching commit; empty output or an unresolved revision is not verification. Record the confirmed merge SHA and timestamp.
- The same `approved: false` rule as 2d applies. A source the user did not approve for writes receives no close-out action. Advance its verified item's status in state only.
- Verified -> perform the source's configured close-out action (same write -> read-back -> confirm discipline as 2d), then `upsert-item` with `status: closed` carrying all three evidence fields: `fix_ref`, `verified_merge_sha`, `verified_at`. Close-out is terminal.
- Unverified claim -> the item stays open. Record the claim on the item, but do not close.
- Item deleted at source -> set `source_gone`.

#### 2g. Plan reconciliation

Read `references/plan-template.md` and follow it. Target the stable path `<root>/plans/feedback-sweep-plan.md`.

**Rotation check first.** If the file exists and it is not a `product_contract_source: ce-sweep` artifact containing only requirements, with no implementation planning, archive it untouched to a dated sibling `<root>/plans/feedback-sweep-plan-YYYY-MM-DD.md` and write a fresh plan from the template. Never overwrite an unrelated plan in place.

Rewrite ONLY the machine-written region: the `date` frontmatter key, `### Summary`, the `<!-- sweep-items:start -->` / `<!-- sweep-items:end -->` marker region, and `### Outstanding Questions` (matching the template's reconciliation rules), and never read or write inside the human-owned notes region. Append new actionable items with their state ids, drain items that are now `closed`, and land any non-interactive-deferred decisions in the Outstanding Questions section.

#### 2h. Decision round

Interactive only. For items needing a product call, ask the user, grouped by category with one blocking question per category, and fold the answers into the plan. Non-interactive skips this; the deferrals are already in the plan's Outstanding Questions.

#### 2i. Wrap-up

Render the handoff invocation exactly as the skill body's 2i section states.

- **Commit.** Follow the JJ procedure and message standards below to commit ONLY `<root>/plans/feedback-sweep-plan.md` plus `<state>` when it is committed-mode state; machine-local state under `.tmp/` is never committed. Describe the feedback sweep and its date without prescribing message syntax. A commit failure is reported, not fatal. In local-commit mode, never push. In shared-branch mode (`sweep_shared_branch: true`), fetch, reconcile/rebase the sweep-owned change as in 2a, move the shared bookmark to the final sweep commit, and push it without force.
- **Record the run.** `run-record --state <state> --writer <writer> --outcome <completed|partial|failed> --counts '<per-source JSON>' --timestamp <ISO now>`.
- **Release.** `lease-release --state <state> --writer <writer>`.
- **Summary** (always emit): new items by source; recordings analyzed, each with its one-line finding; closed items with their fix evidence; the `ack_deferred` / `manual_stuck` / needs-attention list; any circuit-breaker or stale-reclaim note; and always the plan path with the handoff line:

## Native repository operations and message standards

Run every repository operation from the target workspace's absolute root, using `(cd "$workspace_root" && jj ...)`. For every repository-scoped GitHub call, use `(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh ...)`; pass the configured `--repo owner/repo` when accessing a different source repository. JJ reference: https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ . Ensure `.tmp/` is ignored before creating scratch files.

JJ snapshots working-copy files without staging. Inspect `jj status` and `jj diff` first. Use `jj split <only-approved-repo-relative-paths> -m "<message composed from the standards below>"` to isolate the sweep commit when unrelated changes exist; when the working change contains only approved paths, use `jj commit -m "<message composed from the standards below>"`. Do not include lock files, scratch, raw media, unrelated changes, or inherited descriptions. Record the resulting commit ID for bookmark/push operations; `@` after committing may be an empty working change. Lease-acquisition messages describe the lease and writer; final messages describe the sweep and date.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing any lease or final message, read the full Go guide and compare several recent subjects AND bodies with `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Establish actual prefixes/package names, casing, tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and observed syntax always win; apply compatible Go guidance for clarity and structure, not a new syntax. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

The following verbatim Go source guidance is illustrative, not a mandatory repository template:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

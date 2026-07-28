# RocketClaw watch loop — scheduling, state, dedup, edge cases

Read this once per babysit session, before acting on the first tick's output. It defines *how ticks are scheduled per harness*, the *on-disk state contract*, the *claim→act→confirm dedup protocol* that makes ticks idempotent and crash-safe, and the *edge-case handling*. SKILL.md owns the ordering invariant; this file owns the mechanics.

## How the watch sustains itself

A skill's turn ends when it returns, so *the skill sets up its own loop* — nothing re-invokes it by magic. The robust, cross-harness-verified way is **not** to call a specific per-harness scheduler; it is to run a cheap deterministic background change-detector and **stay in-session**, woken when it signals:

- **`pr-snapshot watch`** is that detector. It performs fetch and diff on an interval without reasoning tokens, prints one `BABYSIT_WAKE {reason,url,...}` line for work or a stop condition, then exits. A `feedback-candidate` that the resolver silent-drops is a normal classification outcome.
- At the fixed deadline, the final refresh preserves terminal and already-settled readiness stops; `max-runtime` outranks every non-terminal wake so the cap cannot start another AI Assistant round.
- The AI Assistant backgrounds `watch`, waits through the runtime's background-and-wake capability, runs a tick, and re-arms. The loop stays in the current session, preserves consequential decisions, and spends reasoning only when something changed.

Watcher ownership is **latest-valid-watcher-wins**. A newer invocation cancels an older invocation whose first fetch is still in flight, preventing network completion order from stealing ownership back. That candidate reservation does not displace the active watcher: only a successful first snapshot atomically supersedes and gracefully terminates it, while a failed preflight leaves it healthy and active. Wakes and snapshots carry `watch_generation`. On delivery, compare the wake generation with a fresh snapshot: discard a stale wake and coalesce it into that current read; if the generation matches but the attention set already cleared, do no work. An `invocation-superseded` wake ends the old loop without a tick or re-arm because a later explicit invocation owns the state. Replacement preserves `last_change_at`, `invocation_started_at`, and `invocation_budget_seconds`, so a fresh watcher polls immediately without adding a new settle delay or renewing the budget.

The needed capability is generic — *run a background process and be woken when it emits a line, without ending the turn* — so **describe the capability and use whatever tool the harness has**, rather than hardcoding a scheduler. A skill drives **tool calls**, never user-typed slash commands. Known instances (examples, not a required list; verified live this session):

| Runtime | Background-and-wake capability the AI Assistant uses | Durable beyond the session? |
|---------|-----------------------------------------|-----------------------------|
| Claude Code (CLI) | background `Bash` + a `Monitor`/wait; or `ScheduleWakeup` under `/loop` | No (session-bound) — cron for durable |
| Grok (CLI/TUI) | background `run_terminal_command` + `get_command_or_subagent_output`; `scheduler_create --durable` for a cross-session schedule | Yes via `scheduler_create --durable` (60s min, 7d) |
| Cursor (CLI) | `Shell` background + `notify_on_output` sentinel (its `/loop` is user-typed, **not** skill-invocable) | No (session-bound) |
| Codex (CLI) | a runtime-owned background exec that re-runs the tick (a detached `nohup` is **reaped** when the tool call ends) | No (session-bound) |
| GUI apps / headless / unknown | none reliable → **checkpoint** | — |

**User-runnable resume syntax.** Whenever this reference tells the skill to print or copy a resume invocation, default to `/ce-babysit-pr <url>`. Use `$ce-babysit-pr <url>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Checkpoint (the floor):** when no background-and-wake capability exists, run one tick, persist, report, and print the exact host-rendered re-run invocation — monitoring is *paused*, say so plainly. Because every tick is disk-resumable, checkpoint is the same loop hand-cranked; the in-session watch only automates the crank. Never fake a loop with a foreground `sleep` (blocked on Claude Code, discouraged elsewhere) or a detached `nohup` (reaped/unsupported on several harnesses).

**Durability:** the in-session watch dies with the session; re-invoking resumes from the workspace-local `.tmp/rocketclaw/` state. Resolve it from `$(jj workspace root)/.tmp/rocketclaw`; if workspace-root discovery fails, use the current directory's `.tmp/rocketclaw`. Reject symlinked or non-owned scratch directories and create them mode `0700`. For an unattended multi-day watch, escalate to a durable scheduler (Grok `scheduler_create --durable`, or cron running `<cli> exec '<host-rendered resume invocation>'`) — a fresh headless run is context-blind, so persist consequential decisions to disk. **Shell environment variables do not persist between separate tool calls** on any runtime; re-set `SKILL_DIR` and `STATE_DIR` inline in every command.

## Cadence (the watch interval)

- `pr-snapshot watch --interval` is the poll cadence: ~2-3 min while active; widen to ~5-10 min when quiet — the detector is cheap, but each poll is a `gh` call, so respect rate limits.
- `--settle-seconds` (default 300) is the quiet window before a `merge-ready` wake, so the AI Assistant is roused only after the PR has cooled off. Leave it unset on the normal arm; only the post-rejection re-arm changes it.
- A push/mutation moves the head — re-arm `watch` (active cadence) so it reads the new state.
- Every re-arm presents the same `--invocation-id "$RUN_INVOCATION_ID" --session-started-at "$RUN_STARTED_AT" --invocation-budget-seconds "$RUN_BUDGET_SECONDS"`; the helper rejects a changed token, anchor, or budget. Only the first snapshot uses `--start-invocation`; only a managed-stack layer transition uses `--continue-invocation`.
- Honor GitHub rate-limit reset headers; back off on `403`/`429`.
- After any mutation, re-snapshot at the *start of the next tick*, not mid-tick.

## Pipeline mode bound (`mode:pipeline`)

An orchestrator (`lfg`) drives ticks in-line and needs the loop to terminate. Run ticks back-to-back until the stop below. **To wait for CI to progress between ticks, use the harness's native non-blocking wait — never a bare foreground `sleep`** (blocked on Claude Code, discouraged elsewhere): Claude Code's `Monitor` until-loop; Grok's `get_command_or_subagent_output(timeout_ms=…)` or a `monitor`; Cursor's `Await` on a backgrounded `gh pr checks --watch`. If the harness has no non-blocking wait, do one tick and return control to the orchestrator rather than busy-spinning. Loop until:

- **Report success only when** `all_checks_ok` is true (every check terminal, **none failing**, and at least one observed), the actionable backlog is empty, `mergeability_certain` is true, `merge_state_status == "CLEAN"`, `stack_blocker` is null, and `branch_currency_blocker` is null/current currency is clear. A terminal-but-**red** check `ce-debug` left as a residual (`has_failing_checks` true), an empty rollup (`checks_present` false — Actions has not created check-runs yet, not that CI passed), unknown or non-clean merge state, manager-stale/probe-error chain state, or an open/claimed/parked currency item is **not** success: keep ticking until it clears or the time budget expires, then return with residuals or `no-checks-observed`; or
- a **budget** is hit: default **3 CI fix rounds** per head-lineage (mirrors `lfg`'s historical cap) and an overall time cap (~30-45 min). On budget-exhaust, the still-red checks and any `needs-human` items become residuals.

Never wait on the merge-ready settle window or human review in pipeline mode — those are interactive stops. A check stuck `IN_PROGRESS` past the time cap ends the run with a "CI still running" residual rather than blocking forever.

The round/time budget above is a **blunt cost floor**, not a convergence detector — it catches a runaway that never trips the trajectory-driven stop below. Prefer to stop *because it's demonstrably not converging*, not because a timer expired.

## Non-convergence (trigger → route → park → re-open)

A loop can churn without finishing: CI **ping-pong** (fix A surfaces B, fix B brings A back — often an emergent trade-off), a review-bot **treadmill** (each published change spawns fresh nits), or **wrong-approach whack-a-mole** (each nit is valid but the approach is the problem). A raw attempt counter cannot tell these from legitimate progress, so the decision is **AI Assistant reasoning over the trajectory**, and the split is strict:

- **`pr-snapshot` (babysit) ships facts.** The `trajectory` block is deterministic and coarse: `check_recur_max`/`recurring_checks` (a check that failed → cleared → failed again on a *new* head; same-head flapping is excluded, so this is not flaky noise), `unresolved_trend` + `new_threads_this_tick` (backlog growing / fresh threads arriving), `stream_alternations` (ci↔review bouncing — cross-stream churn only babysit can see), `heads_since_progress` (heads moved without a new low in open problems). Babysit **never** labels this "non-convergence."
- **The leaf judges.** When a trigger fires (the thresholds are in SKILL.md Step 2 — the single source of truth; do not re-list them here), pass the trajectory into that tick's `ce-debug`/`ce-resolve-pr-feedback` as **mandatory input**. It must either demonstrate progress (name the invariant the next bounded fix resolves) or return a `needs-human` that **parks the whole stream** with a `decision_context` (the tension/root, options, tradeoffs, its lean).

**The anti-cry-wolf line (put it to the leaf):** *progressive failure migration* — A fixed → B appears once → B fixed → done — is ordinary repair; **do not park.** *Oscillation* — A returns after B's fix, the failing set cycles, defects migrate X→Y→Z with the same invariant unsatisfied, or fix size grows superlinearly — is non-convergence; park. "We've tried a lot" is never enough.

**A third case the counter must not miss: a *correct* finding recurring across sibling sites.** When each new head brings a fresh thread that is *valid* and shares one root and treatment with an already-fixed one — not a wrong-approach cluster, not oscillation — the problem is a single fix with a multi-site blast radius surfacing one site per head; dripping it one-per-head is as wasteful as parking it is wrong. **Route it, don't decide it here:** pass the recurring feedback cluster **plus** the trajectory to `ce-resolve-pr-feedback` and request a **bounded-class assessment**. The resolver holds the diff and owns the call — it decides whether the sites are genuinely equivalent (same invariant, same fix, only behavior this PR touched), enumerates the concrete locations, and fixes the class in one pass. Babysit does **not** infer the root or the sites from the `trajectory` — those are churn counts, not semantic identity. If the resolver judges the sites *not* equivalent, it falls back to per-site; if it judges the shared root a wrong approach, it parks — unchanged from above.

**Guards:**

- **Moving-target ≠ non-convergence.** Base-branch merges, dep bumps, flaky infra, and bot-rule changes create unrelated new failures. Recurrence already excludes same-SHA flapping; still, don't park a failure the leaf attributes to an external cause rather than the approach.
- **Cross-stream contradiction.** If `ce-debug` concludes the review-requested behavior is invalid while `ce-resolve-pr-feedback` concludes it's required, that's a single **cross-stream** residual — don't arbitrarily park one side.
- **Parked = hard blocker, re-openable.** A parked stream makes the PR *not* merge-ready (never "done"), but re-open it on material change (a human pushed a new head, the parked thread was superseded/resolved, or the failing-check universe changed). **How:** CI re-opens itself — a new head SHA clears the SHA-scoped dispatch state, so just re-snapshot. A parked **review thread** does *not* auto-re-open; `mark --thread <id> --disposition open` re-actionizes it for a fresh pass. Un-park deliberately, on judged material change — not on the resolver's own reply.

## On-disk state contract

State lives at `<workspace-root>/.tmp/rocketclaw/ce-babysit-pr/<host>-<owner>-<repo>-<pr>/state.json` (a stable, cross-invocation-reusable path so any later tick finds it). Use the current directory as `<workspace-root>` only when `jj workspace root` cannot resolve one. The `<host>` segment is load-bearing for GitHub Enterprise: without it, two PRs sharing `owner/repo#N` on different hosts would reuse one `state.json` and cross-contaminate dispositions. The `pr-snapshot` script owns all reads and writes under a file lock. Shape:

```json
{
  "pr": { "owner": "...", "repo": "...", "number": 123, "url": "..." },
  "head_sha": "abc123",
  "tick": 7,
  "state_created_at": "<iso8601>",
  "started_at": "<iso8601>",
  "invocation_id": "<opaque invocation token>",
  "invocation_budget_seconds": 28800,
  "last_activity_at": "<iso8601 — activity heartbeat: last watch poll or AI Assistant snapshot/mark>",
  "dead_time_seconds": 0,
  "invocation_backstop_seconds": 259200,
  "watch_generation": "<opaque generation>",
  "watch_pid": 12345,
  "watch_process_identity": "<pid-reuse guard>",
  "checks": { "<check_key>": { "name": "...", "status": "COMPLETED", "conclusion": "FAILURE", "head_sha": "abc123" } },
  "threads": { "<thread_id>": { "last_comment_id": "...", "last_comment_at": "<iso8601>", "disposition": "open|dispatched|needs-human", "acted_identity": ["<comment_id>", "<comment_at>"] } },
  "feedback": { "<comment_or_review_id>": { "kind": "comment|review", "author": "...", "disposition": "open|dispatched|needs-human" } },
  "ci_dispatched": { "<head_sha>": ["<check_key>", "..."] },
  "review_decision": "APPROVED",
  "review_in_progress": false,
  "review_signal_count": 0,
  "review_signal_identities": [],
  "review_signal_seen_on_head": true,
  "review_signal_first_seen_at": "<iso8601>",
  "review_signal_last_changed_at": "<iso8601>",
  "mergeable": "MERGEABLE",
  "merge_state_status": "CLEAN",
  "base": { "host": "github.com", "repository": "owner/repo", "ref": "main", "oid": "base-sha" },
  "branch_currency_state": {
    "current_key": "currency:<identity-hash>",
    "head_sha": "abc123",
    "items": { "<currency-key>": { "status": "BEHIND|DIRTY", "disposition": "open|claimed|confirmed|needs-human", "host_branch_update_capability": true, "recovery_state": "claimed|mutation-observed|ambiguous|retry-authorized|retry-exhausted", "semantic_conflict_fingerprint": "<paths-and-stage-blobs>" } },
    "semantic_parks": { "<fingerprint>": { "head_sha": "abc123", "status": "DIRTY", "route": "normal-base", "observation_key": "<currency-key>" } }
  },
  "pr_chain": {
    "manager_status": "confirmed|absent|probe-error",
    "manager_source": "gh-stack|graphql|null",
    "relationship_status": "dependent|independent|probe-error",
    "target_position": 2,
    "target_needs_rebase": false,
    "upstack_needs_rebase": [],
    "entries": [],
    "parent_prs": [],
    "dependent_prs": []
  },
  "last_change_at": "<iso8601>",
  "last_action": "<short string>",
  "trajectory": {
    "check_history": { "<check_key>": { "state": "failing|clear", "last_head": "abc123", "recur": 0 } },
    "seen_threads": { "<thread_id>": 3 },
    "unresolved_series": [2, 3, 4],
    "stream_series": ["ci", "review", "ci"],
    "min_open_problems": 1,
    "heads_since_progress": 0
  }
}
```

A `check_key` is `"<workflow>/<name>"`, or `"<name>"` without a workflow, and remains stable across polls for one head. Each snapshot emits movement, timing, invocation, chain, blocker, review-signal, and trajectory facts. Reactor identity-set changes count as movement even when count and boolean views do not change. `review_signal_seen_on_head` remains true after observed signals disappear, so a fresh AI Assistant can distinguish an incomplete lifecycle from a head where no signal appeared; a new head resets it. The first snapshot starts one fixed invocation, and later calls must match its token, anchor, and budget. Persisted-state age never contributes to that cap. Chain probing accepts `gh stack view --json` only when it contains the target PR, then uses the GraphQL fallback. Only a stack-field schema-unavailable response plus a successful default-ref lookup degrades to `absent`; other failures remain `probe-error`. Ordinary open-PR base/head relationships classify manual dependencies only when no manager is confirmed. The script maintains trajectory facts; delegated skills judge them.

## Claim → act → confirm (the dedup protocol)

The rule that makes ticks idempotent and crash-safe: **the snapshot never marks an item handled just from observing it.** An item leaves the actionable set only when the AI Assistant confirms it acted through `mark` or when remote truth removes it. A failed or incomplete resolver/debugger pass therefore leaves the item actionable.

- **Review threads.** A thread is actionable while it is unresolved and you have not recorded acting on it. After a resolve pass, `mark --thread <id> --disposition dispatched` (handled) or `--disposition needs-human` (escalated) silences it. Every `mark` must pass the active invocation ID, start anchor, and budget; a stale tick is rejected before it can write into a newer invocation. A later fetch drops resolved threads entirely (remote confirms the resolve). A **`dispatched`** thread that is still unresolved is **reactivated** when a later reviewer comment moves its last-comment identity past `acted_identity` — the identity captured on the first tick we saw it dispatched, which is *after* our own reply landed, so our reply is the baseline and does not re-trigger while a genuine reviewer re-engagement does. A **`needs-human`** thread stays parked — blocking merge-ready via `open_needs_human` — until **a human answers it**: a reviewer reply or a top-level-comment edit moves its identity past the `decision_context` reply we captured as the baseline, which auto-reopens and wakes it (our own reply is the baseline, so it never self-triggers); an explicit `--disposition open` still forces it too. This closes two failure modes: a dispatched-but-unresolved thread with fresh reviewer activity would otherwise vanish from `counts.threads` and let the merge-ready gate call the PR ready, and a parked question the human *answered* would otherwise sit ignored forever while the watch stayed idle.
- **Non-thread feedback candidates** (top-level PR comments + review-submission bodies). Surfaced as `actionable.comments` for content that has no inline thread. The field name supports the shared claim→act→confirm protocol; it does not mean the detector has semantically proven that the body requires work. A comments-only watch emits `feedback-candidate`, and a resolver pass that silent-drops it is a normal classification outcome. The deterministic fetch excludes only empty bodies and messages known to be from the PR author. It never classifies external feedback by content, bot identity, or comment-vs-review surface. Unlike a thread there is no remote resolve, so `mark --comment <id> --disposition dispatched|needs-human` is the only thing that silences it. A dispatched item reactivates when its body is edited. Both streams count as one review stream for trajectory and merge-ready backlog purposes.
- **CI checks.** A failing check on the current head is actionable until you `mark --check <key>` (recorded in `ci_dispatched[head_sha]`). A new head OID clears `ci_dispatched` and re-evaluates every check against the new revision, so green is never carried across a push. There is no transition tracking: a failing check stays actionable until you record acting on it.

- **Branch currency.** `branch_currency` is the third attention stream. Its identity binds host-qualified base repository/ref/OID, head SHA, merge status, and route. `UNKNOWN` mergeability emits no item. Managed stacks and manager/relationship `probe-error` are excluded; a `normal-base` target may be independent or an eligible target-local manual dependency, and a root with open child dependents remains allowed. Never mutate those dependents.

  A current open item with carried `parked_semantic_fingerprints` must be previewed first. Compute the current fingerprint from sorted conflicted paths plus stage blob identities, excluding the base OID, and mark `--currency-inspected-fingerprint <fingerprint>`. Unchanged evidence remains parked; changed evidence retires the old park and reopens attention. Before either a host update or local merge, atomically mark the exact item with `--currency-key <currency_key> --currency-disposition claimed`, plus `--invocation-id "$RUN_INVOCATION_ID" --session-started-at "$RUN_STARTED_AT" --invocation-budget-seconds "$RUN_BUDGET_SECONDS"`. Stale invocation fencing and `max-runtime` take precedence over a new claim or mutation.

  Re-entry into `claimed` is reconciliation-only, never a direct resubmission. Record the observed recovery as `--currency-outcome mutation-observed`, `--currency-outcome proven-no-mutation`, or `--currency-outcome ambiguous`. Exactly one retry follows only conclusive no-mutation proof and the engine backoff. Ambiguous recovery never retries or resubmits; keep reconciling or park. Confirm or park the same exact item with `--currency-disposition confirmed|needs-human`; never transfer a claim to a moved head/base observation.

`ci_dispatched`, the thread dispositions, the feedback dispositions, and `branch_currency_state` **are** the journal — they are written by `mark` and read by `snapshot`. There is no separate crash-recovery record: an unmarked review/CI item stays actionable, while a claimed currency item stays reconciliation-only until explicitly confirmed or parked.

## Merge-readiness and the settle window

Do not re-derive "required checks" — GitHub already computes it. Use `mergeable == "MERGEABLE"` and `merge_state_status == "CLEAN"` for GitHub gates, then require both chain and branch currency to be clear. A managed target is ready only when `target_needs_rebase == false`; true or unknown emits `stack_blocker`. Any current `branch_currency_blocker` blocks ready until fresh remote evidence clears it. A manual dependency can be ready relative to its parent but is not independently landable while that parent remains open. `UNSTABLE` means mergeable but a non-required check is red; `BLOCKED` means a required gate is unmet. The snapshot also emits `has_failing_checks` so you can act on a red check even while `merge_state_status` is `UNSTABLE`.

The settle window guards the most damaging false positive: "CI went green, told the user to merge, then feedback landed."

- The script stamps `last_change_at` whenever anything observable moves — a check status/conclusion, a thread's identity (added, edited, or resolved-away), the head SHA, `review_decision`, `mergeable`, `merge_state_status`, or the current 👀 reactor identity set. Each snapshot emits `quiet_seconds`.
- "Looks ready" requires `quiet_seconds >= 300` (default) on top of a CLEAN mergeable state and zero actionable backlog (threads **and** non-thread feedback). A reviewer or bot still working shows up as recent activity → `quiet_seconds` resets.
- A current-head review signal creates an incomplete lifecycle even if it later disappears. The detector blocks a live 👀 through 900 quiet seconds; the skill applies the same 15-minute floor to a disappeared/non-👀 signal, may extend once to 1800 seconds from concrete prior-round timing, and never re-arms past 30 quiet minutes after the last observable movement solely for the unchanged signal. A new signal transition is movement and resets that quiet phase; the ceiling is not wall-clock time from the first 👀.
- **It is a cooling-off signal, not a guarantee.** Five quiet minutes is evidence the PR stopped moving, not proof no review is coming. Report "looks ready — your call," never "safe to merge"; a stalled lifecycle uses the stronger cautious-ready disclosure and resume path from SKILL.md.

## Concurrency

- **Lock.** The script takes a file lock around each state read/write. It cannot span the AI Assistant's mutations between script calls, so it is necessary but not sufficient.
- **Pre-mutation claim and revalidation.** Before a `BEHIND`/`DIRTY` external mutation, claim the exact item, then immediately prove its observed head and base OIDs are still current. A moved head or base invalidates the stale action. Treat the snapshot as a hint, never as a guarantee the world is unchanged at mutation time.
- **Interrupted local conflict resolution.** On re-entry, inspect `jj status`, `jj diff`, `jj log`, and the remembered remote bookmark before acting. Reconcile the interrupted resolution to the already-validated change or leave it unpublished and abandon it safely; never begin another attempt over unknown local state.

## Managed-stack continuation

Sequential babysitting is available only while a fresh probe positively reports `manager_status == "confirmed"` for the active PR. It uses one active PR target and one watcher, never a watcher per stack layer. On an authorized transition, stop the old watcher, re-read `gh stack view --json`, require the next PR to be the manager's immediate open entry and either non-draft or explicitly included by the user, run `jj git fetch --remote <remote>`, verify its remote bookmark, and create the layer's working-copy change with `jj new '<next-bookmark>@<remote>'`. Initialize its state directory with `--continue-invocation`, the original invocation ID, start anchor, and budget, plus `--continue-dead-time-seconds <prior-dead-time>`. One fixed budget covers the accepted traversal. Recheck downstack settledness only at transitions, immediately before mutation, and at readiness; if a lower layer becomes unsettled, return to the lowest unsettled layer rather than writing to both concurrently. Loss of manager confirmation ends continuation.

The one-time semantic-scope offer and draft/human boundaries live inline in SKILL.md because they are routing decisions, not detector mechanics. A manual dependency chain never enters this continuation path; it remains target-local even when its base/head relationships have the same shape.

## Edge cases

- **Managed stack:** `target_needs_rebase` true or unknown becomes `stack-blocked`; do not use the host update operation or a target-local base merge. After an authorized target push, retain the pushed OID, re-confirm that `gh stack view --json` still owns the target and ordered dependent refs, require `jj status` to show no unrelated changes, run `jj git fetch --remote <remote>`, and verify the target local and remembered remote bookmarks remain at that OID with `jj bookmark list --all-remotes` and `jj log`. Select the first open dependent immediately above the target and run `jj rebase -s <first-dependent-revision> -d <target-revision>`; descendants move and the target remains unchanged. Inspect the result with `jj status`, `jj diff`, and `jj log`, advance every affected bookmark to its rewritten revision, and publish all affected bookmarks in the single atomic `jj git push --bookmark <bookmark>... --remote <remote>` operation proven before delegation. On a conflict, leave the rewrite unpublished and surface a `needs-human`/upstack residual. On target movement or push rejection, fetch and surface the residual; never bypass Jujutsu's remote-state safety checks. If membership cannot be re-confirmed, do not import or guess at the stack.
- **Manual dependency chain:** keep the requested PR as the target, qualify readiness relative to its parent, and report downstream impact. An eligible emitted `normal-base` item may be repaired target-locally, but never rebase, rewrite, restack, or otherwise mutate dependent bookmarks. A root with open child dependents remains eligible; a target push may make those children stale, which is a residual only.
- **Normal-base `BEHIND`:** require `host_branch_update_capability == true`; denied/`false` or `unknown` becomes `needs-human`, and that capability is never treated as bookmark-push authority. Claim the exact item and revalidate its observed head and base OIDs. Invoke GitHub's `PUT /repos/{owner}/{repo}/pulls/{number}/update-branch` endpoint once with `expected_head_sha` set to the claimed observation's head OID. Treat an HTTP 422 mismatch as a stale claim: run `jj git fetch --remote <remote>`, re-snapshot, and reconcile without resubmitting. Confirm only after a fresh snapshot plus `jj log` ancestry evidence proves the resulting head contains the observed base OID and the currency gate is clear.
- **Normal-base `DIRTY`:** `host_branch_update_capability` is irrelevant. Separately prove `jj git push` authority to the exact head bookmark without mutating; unknown or denied proof parks. Require a verified clean Jujutsu workspace at the observed remote bookmark, run `jj git fetch --remote <remote>`, and create an unpublished merge preview with `jj new '<head-bookmark>@<remote>' <base-oid>`. Inspect with `jj status` and `jj diff`. Fingerprint the sorted conflicted paths and side identities, excluding the base OID. If `parked_semantic_fingerprints` is present, record `--currency-inspected-fingerprint` before any claim: an unchanged fingerprint remains parked, while changed evidence retires the old park and reopens the item.

  A resolution is mechanical only when positive intent evidence leaves no reasonable alternative behavior. Two plausible resolutions, a material intent change, stale or incomplete evidence, unavailable authority, or unbounded work requires leaving the preview unpublished and recording `--currency-disposition needs-human --semantic-conflict-fingerprint <fingerprint>`, with concise competing options, tradeoffs, and a lean. For a mechanical case, claim and revalidate, recreate the exact merge change, and mark `--currency-outcome mutation-observed` when local resolution starts. Resolve only the previewed conflict and validate proportionally.

  Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

  Compose, edit, validate, or recommend the Jujutsu change description under that rule. The project's active instructions and syntax observed at runtime via `jj log` always win; apply only compatible Go guidance. Do not impose a fixed prefix, type, scope, template, example, or canned wording. Use `jj describe -m <change-description>`, advance the exact bookmark with `jj bookmark set <head-bookmark> -r <validated-revision>`, and publish only with `jj git push --bookmark <head-bookmark> --remote <remote>`. Use `ai:assistant` if an actor identifier is required. Confirm only after the remote head equals or contains the validated merge revision and a fresh snapshot clears the gate. An interrupted resolution must reconcile or be abandoned safely.
- **Manager/relationship probe error:** continue review and CI streams, but perform no branch-currency mutation and do not declare ready until classification succeeds.
- **External head rewrite:** the head OID moved under the loop. The snapshot clears OID-scoped CI state automatically; re-snapshot and never clobber unrelated published work.
- **PR closed or merged externally:** detected as `pr_state != "OPEN"` on any tick → clean exit with a final status.
- **needs-human feedback:** `ce-resolve-pr-feedback` leaves those threads open and returns them as escalations; record each with `mark ... --disposition needs-human`, keep doing independent CI work, and surface them. Never auto-decline or auto-resolve a thread you did not fix. A parked `needs-human` is a **standing residual** (SKILL.md Step 3): it blocks *declaring* merge-ready but does **not** end the watch — keep handling new CI and later review rounds around it. Only a true stop (terminal / looks-ready / the budget cap) ends the active layer, not a count of accumulated escalations; an authorized confirmed-managed-stack run may transition after a looks-ready layer as defined inline in SKILL.md.
- **No bookmark-push access / fork PR:** detect unavailable authority before publication when possible; otherwise consume the delegated failure, report it, and stop because the loop cannot make progress without permission.
- **CI that never completes:** a check stuck `IN_PROGRESS` for a long time will keep the loop from settling. When the invocation budget is reached — either the 8h **active** cap (`invocation_elapsed_seconds`, which excludes suspended time) or the 3-calendar-day **wall-clock backstop** (`invocation_wall_elapsed_seconds`) — hand back with the measured `invocation_elapsed_seconds` and the `max_runtime_ceiling` that fired; never substitute the age of persisted PR state or automatically start another budget.
- **Rate limits / transient API errors:** honor the reset time, back off, resume. The claim→confirm protocol protects against replay.

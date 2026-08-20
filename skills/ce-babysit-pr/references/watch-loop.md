# Watch loop — scheduling, state, dedup, edge cases

Read this once per babysit session, before acting on the first tick's output. It defines *how ticks are scheduled per harness*, the *on-disk state contract*, the *claim→act→confirm dedup protocol* that makes ticks idempotent and crash-safe, and the *edge-case handling*. SKILL.md owns the ordering invariant; this file owns the mechanics.

## How the watch sustains itself

A skill's turn ends when it returns, so *the skill sets up its own loop* — nothing re-invokes it by magic. The robust, cross-harness-verified way is **not** to call a specific per-harness scheduler; it is to run a cheap deterministic background change-detector and **stay in-session**, woken when it signals:

- **`pr-snapshot watch`** performs the deterministic fetch/diff and emits one `BABYSIT_WAKE` only for actionable feedback/CI, `bookmark-currency`, or a stop/residual condition.
- At the fixed deadline, the final refresh preserves `terminal` and already-settled `merge-ready` stops; `max-runtime` outranks every non-terminal work/residual wake so the cap cannot start another agent round.
- The agent **backgrounds `watch` and waits for that line** with its harness's *background-and-wake* capability, runs a tick, and re-arms. The loop lives **in the current session**, so it keeps every decision the conversation made — declined nits, a reviewer judged wrong, the user's mid-run steering — and spends reasoning only when something changed.

Watcher ownership is **latest-valid-watcher-wins**. A newer invocation cancels an older invocation whose first fetch is still in flight, preventing network completion order from stealing ownership back. That candidate reservation does not displace the active watcher: only a successful first snapshot atomically supersedes and gracefully terminates it, while a failed preflight leaves it healthy and active. Wakes and snapshots carry `watch_generation`. On delivery, compare the wake generation with a fresh snapshot: discard a stale wake and coalesce it into that current read; if the generation matches but the attention set already cleared, do no work. An `invocation-superseded` wake ends the old loop without a tick or re-arm because a later explicit invocation owns the state. Replacement preserves `last_change_at`, `invocation_started_at`, and `invocation_budget_seconds`, so a fresh watcher polls immediately without adding a new settle delay or renewing the budget.

The needed capability is generic — *run a background process and be woken when it emits a line, without ending the turn* — so **describe the capability and use whatever tool the harness has**, rather than hardcoding a scheduler. A skill drives **tool calls**, never user-typed slash commands. Known instances (examples, not a required list; verified live this session):

| Harness | Background-and-wake tool the agent uses | Durable beyond the session? |
|---------|-----------------------------------------|-----------------------------|
| Claude Code (CLI) | background `Bash` + a `Monitor`/wait; or `ScheduleWakeup` under `/loop` | No (session-bound) — cron for durable |
| Grok (CLI/TUI) | background `run_terminal_command` + `get_command_or_subagent_output`; `scheduler_create --durable` for a cross-session schedule | Yes via `scheduler_create --durable` (60s min, 7d) |
| Cursor (CLI) | `Shell` background + `notify_on_output` sentinel (its `/loop` is user-typed, **not** skill-invocable) | No (session-bound) |
| Codex (CLI) | a runtime-owned background exec that re-runs the tick (a detached `nohup` is **reaped** when the tool call ends) | No (session-bound) |
| GUI apps / headless / unknown | none reliable → **checkpoint** | — |

**User-runnable resume syntax.** Whenever this reference tells the skill to print or copy a resume invocation, default to `/ce-babysit-pr <url>` and, when the run posture is not `target`, append the same `posture:stack-ready` or `posture:stack-land` token so checkpoint / durable / session re-entry keeps stack scope. Use `$ce-babysit-pr <url> [posture:…]` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Checkpoint (the floor):** when no background-and-wake capability exists, run one tick, persist, report, and print the exact host-rendered re-run invocation — monitoring is *paused*, say so plainly. Because every tick is disk-resumable, checkpoint is the same loop hand-cranked; the in-session watch only automates the crank. Never fake a loop with a foreground `sleep` (blocked on Claude Code, discouraged elsewhere) or a detached `nohup` (reaped/unsupported on several harnesses).

**Durability:** the in-session watch dies with the session; re-invoking resumes from the jj repository's `.tmp` tree, or the local workspace's `.tmp` fallback when `jj root` is unavailable. For an unattended multi-day watch, use a durable scheduler — a fresh headless run is context-blind, so persist consequential decisions there. **Shell env vars do not persist between separate tool calls** on any harness — re-set `SKILL_DIR`/`STATE_DIR` inline in every command.

## Cadence (the watch interval)

- `pr-snapshot watch --interval` is the poll cadence: ~2-3 min while active; widen to ~5-10 min when quiet — the detector is cheap, but each poll is a `gh` call, so respect rate limits.
- `--settle-seconds` (default 300) is the quiet window before a `merge-ready` wake, so the agent is roused to declare-ready only once the PR has actually cooled off, not every poll. Leave it unset on the normal arm — the script's default is the initial policy; the only invocation that sets it is the post-rejection re-arm in SKILL.md Step 3's merge-ready wake protocol.
- `--blocked-external-drain-seconds` is set only after an interactive approval-gate wake. Keep the active ~150s interval throughout this short 300/900/1800-second review drain: a quiet 5-10 minute poll could consume the entire signal-less tier. The persisted head-scoped review clock, not the arm time or broad merge-ready quiet clock, decides expiry.
- A bookmark push/mutation moves the head — re-arm `watch` (active cadence) so it reads the new state.
- Every re-arm presents the same `--invocation-id "$RUN_INVOCATION_ID" --session-started-at "$RUN_STARTED_AT" --invocation-budget-seconds "$RUN_BUDGET_SECONDS"`; the helper rejects a changed token, anchor, or budget. Only the first snapshot uses `--start-invocation`; only a managed-stack layer transition uses `--continue-invocation`.
- Honor GitHub rate-limit reset headers; back off on `403`/`429`.
- After any mutation, re-snapshot at the *start of the next tick*, not mid-tick.

## Pipeline mode bound (`mode:pipeline`)

An orchestrator (`lfg`) drives ticks in-line and needs the loop to terminate. Run ticks back-to-back until the stop below. **To wait for CI to progress between ticks, use the harness's native non-blocking wait — never a bare foreground `sleep`** (blocked on Claude Code, discouraged elsewhere): Claude Code's `Monitor` until-loop; Grok's `get_command_or_subagent_output(timeout_ms=…)` or a `monitor`; Cursor's `Await` on a backgrounded `gh pr checks --watch`. If the harness has no non-blocking wait, do one tick and return control to the orchestrator rather than busy-spinning. Loop until:

- **Report success only when** checks/backlog/mergeability are clean and base, stack, and `bookmark_currency_blocker` are clear; otherwise keep ticking until budget and return residuals.
- a **budget** is hit: default **3 CI fix rounds** per head-lineage (mirrors `lfg`'s historical cap) and an overall time cap (~30-45 min). On budget-exhaust, the still-red checks and any `needs-human` items become residuals.

Never wait on the merge-ready settle window or human review in pipeline mode — those are interactive stops. A check stuck `IN_PROGRESS` past the time cap ends the run with a "CI still running" residual rather than blocking forever.

The round/time budget above is a **blunt cost floor**, not a convergence detector — it catches a runaway that never trips the trajectory-driven stop below. Prefer to stop *because it's demonstrably not converging*, not because a timer expired.

## Non-convergence (trigger → route → park → re-open)

A loop can churn without finishing: CI **ping-pong** (fix A surfaces B, fix B brings A back — often an emergent trade-off), a review-bot **treadmill** (each pushed change spawns fresh nits), or **wrong-approach whack-a-mole**. A raw attempt counter cannot distinguish these from legitimate progress, so the leaf reasons over the trajectory.

- **`pr-snapshot` (babysit) ships facts.** The `trajectory` block is deterministic and coarse: `check_recur_max`/`recurring_checks` (a check that failed → cleared → failed again on a *new* head; same-head flapping is excluded, so this is not flaky noise), `unresolved_trend` + `new_threads_this_tick` (backlog growing / fresh threads arriving), `stream_alternations` (ci↔review bouncing — cross-stream churn only babysit can see), `heads_since_progress` (heads moved without a new low in open problems). Babysit **never** labels this "non-convergence."
- **The leaf judges.** When a trigger fires (the thresholds are in SKILL.md Step 2 — the single source of truth; do not re-list them here), pass the trajectory into that tick's `ce-debug`/`ce-resolve-pr-feedback` as **mandatory input**. It must either demonstrate progress (name the invariant the next bounded fix resolves) or return a `needs-human` that **parks the whole stream** with a `decision_context` (the tension/root, options, tradeoffs, its lean).

**The anti-cry-wolf line (put it to the leaf):** *progressive failure migration* — A fixed → B appears once → B fixed → done — is ordinary repair; **do not park.** *Oscillation* — A returns after B's fix, the failing set cycles, defects migrate X→Y→Z with the same invariant unsatisfied, or fix size grows superlinearly — is non-convergence; park. "We've tried a lot" is never enough.

**A third case the counter must not miss: a *correct* finding recurring across sibling sites.** When each new head brings a fresh thread that is *valid* and shares one root and treatment with an already-fixed one — not a wrong-approach cluster, not oscillation — the problem is a single fix with a multi-site blast radius surfacing one site per head; dripping it one-per-head is as wasteful as parking it is wrong. **Route it, don't decide it here:** pass the recurring feedback cluster **plus** the trajectory to `ce-resolve-pr-feedback` and request a **bounded-class assessment**. The resolver holds the diff and owns the call — it decides whether the sites are genuinely equivalent (same invariant, same fix, only behavior this PR touched), enumerates the concrete locations, and fixes the class in one pass. Babysit does **not** infer the root or the sites from the `trajectory` — those are churn counts, not semantic identity. If the resolver judges the sites *not* equivalent, it falls back to per-site; if it judges the shared root a wrong approach, it parks — unchanged from above.

**Guards:**

- **Moving-target ≠ non-convergence.** Base-bookmark movement, dependency bumps, flaky infra, and bot-rule changes create unrelated failures. Recurrence excludes same-head flapping; do not park an externally caused failure.
- **Cross-stream contradiction.** If `ce-debug` concludes the review-requested behavior is invalid while `ce-resolve-pr-feedback` concludes it's required, that's a single **cross-stream** residual — don't arbitrarily park one side.
- **Parked = hard blocker, re-openable.** A parked stream blocks readiness but re-opens on material context change. A new head commit ID clears head-scoped CI dispatch state; review threads reopen explicitly or through the recorded remote-activity rules.

## On-disk state contract

State lives at `<jj-root>/.tmp/babysit-pr/<host>-<owner>-<repo>-<pr>/state.json`, with `./.tmp/babysit-pr/...` as the local fallback when `jj root` is unavailable. The `<host>` segment is load-bearing for GitHub Enterprise. The helper owns all reads and writes under a file lock.

```json
{
  "pr": { "owner": "...", "repo": "...", "number": 123, "url": "..." },
  "head_sha": "abc123",
  "tick": 7,
  "state_created_at": "<iso8601>",
  "started_at": "<iso8601>",
  "invocation_id": "<opaque invocation token>",
  "invocation_budget_seconds": 28800,
  "last_activity_at": "<iso8601 — activity heartbeat: last watch poll or agent snapshot/mark>",
  "dead_time_seconds": 0,
  "invocation_backstop_seconds": 259200,
  "watch_generation": "<opaque generation>",
  "watch_pid": 12345,
  "watch_process_identity": "<pid-reuse guard>",
  "checks": { "<check_key>": { "name": "...", "status": "COMPLETED", "conclusion": "FAILURE", "head_sha": "abc123" } },
  "threads": { "<thread_id>": { "last_comment_id": "...", "last_comment_at": "<iso8601>", "disposition": "open|dispatched|needs-human", "acted_identity": ["<comment_id>", "<comment_at>"] } },
  "feedback": { "<comment_or_review_id>": { "kind": "comment|review", "author": "...", "disposition": "open|dispatched|needs-human", "acted_identity": ["<edit_id>"] } },
  "ci_dispatched": { "<head_sha>": ["<check_key>", "..."] },
  "review_decision": "APPROVED",
  "review_in_progress": false,
  "review_signal_count": 0,
  "review_signal_identities": [],
  "review_signal_seen_on_head": true,
  "review_signal_first_seen_at": "<iso8601>",
  "review_signal_last_changed_at": "<iso8601>",
  "blocked_external_head_sha": "abc123",
  "blocked_external_first_seen_at": "<iso8601>",
  "blocked_external_review_last_activity_at": "<iso8601>",
  "mergeable": "MERGEABLE",
  "merge_state_status": "CLEAN",
  "base": {
    "host": "github.com",
    "repository": "owner/repo",
    "ref": "main",
    "oid": "<live-base-commit-id>",
    "graphql_oid": "<host-live-base-commit-id>",
    "historical_oid": "<historical-base-commit-id>",
    "merge_commit_oid": "<generated-test-merge-commit-id>",
    "merge_parent_oids": ["<live-base-commit-id>", "<head-commit-id>"],
    "identity": "current"
  },
  "base_ref_blocker": null,
  "bookmark_currency_state": {
    "current_key": "currency:<identity-hash>",
    "head_sha": "abc123",
    "items": { "<currency-key>": { "status": "BEHIND|DIRTY", "disposition": "open|claimed|confirmed|needs-human", "host_bookmark_update_capability": true, "recovery_state": "claimed|mutation-observed|ambiguous|retry-authorized|retry-exhausted", "semantic_conflict_fingerprint": "<paths-and-conflict-identities>" } },
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

A `check_key` is `"<workflow>/<name>"` (or `"<name>"` when there is no workflow) — stable across polls for the same head, which is all the dedup needs (see below). Each `snapshot` emits `changed_this_tick`, `quiet_seconds`, `invocation_id`, `invocation_started_at`, `invocation_elapsed_seconds`, `invocation_budget_seconds`, `invocation_remaining_seconds`, `persisted_state_created_at`, `persisted_state_age_seconds`, `pr_chain`, `stack_blocker`, the review-signal lifecycle fields, `blocked_external_first_seen_at`, `blocked_external_review_last_activity_at`, `blocked_external_review_quiet_seconds`, `blocked_external_review_moved_this_tick`, and the derived `trajectory` facts (see **Non-convergence** above). The blocked-external clock is head-scoped and narrower than `quiet_seconds`: external thread/comment/review movement, review-signal movement, or a new head resets it; check, base, stack, and disposition-only movement does not. `blocked_external_review_moved_this_tick` lets a newly started or changed lifecycle wake through an already-baselined gate so the agent can select the longer tier. `review_signal_identities` is the sorted set of current 👀 reactor identities; `review_signal_count` and `review_in_progress` remain count and boolean compatibility views. Identity-set changes are observable signal movement even when the count and boolean stay unchanged. Legacy state without identities migrates on its first identity-aware observation. `review_signal_seen_on_head` remains true if all observed 👀 disappear, so a fresh agent can distinguish an incomplete lifecycle from a head where no signal ever appeared; a new head resets it. The first snapshot starts one fixed invocation; later calls must match its token, anchor, and budget. Persisted-state age describes how long the resumable PR journal has existed and never contributes to the invocation cap. The chain probe is CLI-first: accept `gh stack view --json` only when it contains the target PR, then use the GraphQL fallback. Only a stack-field schema-unavailable response with a successful read-only default-branch lookup degrades to `absent`; auth, transport, rate-limit, malformed, other GraphQL, and failed default-branch probes stay `probe-error`. Ordinary open-PR base/head relationships classify manual dependencies only when no manager is confirmed. The `trajectory` sub-state is deterministic bookkeeping the script maintains; the leaves reason over the emitted facts.

## Claim → act → confirm (the dedup protocol)

The rule that makes ticks idempotent *and* crash-safe: **the snapshot never marks an item handled just from observing it.** An item leaves the actionable set only when the agent confirms it acted (via `mark`) or when remote truth removes it. So if a resolve/debug pass crashes, errors, or returns without finishing, the item is still actionable on the next tick — the loop cannot silently drop work.

- **Review threads.** A thread is actionable while it is unresolved and you have not recorded acting on it. After a resolve pass, `mark --thread <id> --disposition dispatched` (handled) or `--disposition needs-human` (escalated) silences it. Every `mark` must pass the active invocation ID, start anchor, and budget; a stale tick is rejected before it can write into a newer invocation. A later fetch drops resolved threads entirely (remote confirms the resolve). A **`dispatched`** thread that is still unresolved is **reactivated** when a later reviewer comment moves its last-comment identity past `acted_identity` — the identity captured on the first tick we saw it dispatched, which is *after* our own reply landed, so our reply is the baseline and does not re-trigger while a genuine reviewer re-engagement does. A **`needs-human`** thread stays parked — blocking merge-ready via `open_needs_human` — until **a human answers it**: a reviewer reply or a top-level-comment edit moves its identity past the `decision_context` reply we captured as the baseline, which auto-reopens and wakes it (our own reply is the baseline, so it never self-triggers); an explicit `--disposition open` still forces it too. This closes two failure modes: a dispatched-but-unresolved thread with fresh reviewer activity would otherwise vanish from `counts.threads` and let the merge-ready gate call the PR ready, and a parked question the human *answered* would otherwise sit ignored forever while the watch stayed idle.
- **Non-thread feedback candidates** (top-level PR comments + review-submission bodies). Surfaced as `actionable.comments` for content that has **no inline thread** — a Changes-Requested review summary or a bare top-level "please rename X". The field name supports the shared claim→act→confirm protocol; it does not mean the detector has semantically proven that the body requires work. A comments-only watch emits `feedback-candidate`, and a resolver pass that silent-drops it is a normal classification outcome. The deterministic fetch excludes only empty bodies and messages known to be from the PR author; those are structural loop-prevention facts. It never classifies external feedback by content, bot identity, or comment-vs-review surface: those are semantic signals for `ce-resolve` to judge, and bot formats, identities, and posting surfaces can change. Unlike a thread there is **no remote resolve**, so a surfaced item never drops out of the fetch on its own: `mark --comment <id> --disposition dispatched` (handled or judged non-actionable) or `--disposition needs-human` (escalated) is the *only* thing that silences it. Same open/dispatched/needs-human dispositions and explicit re-open (`--disposition open`) as threads. Edit-reactivation is **per-disposition**: a `dispatched` item is never auto-reactivated by a body edit — status bots (changeset-bot, CodeRabbit, Codecov) rewrite their own comment bodies on every push, so edit-keyed reactivation re-actionized already-handled bot comments forever and the merge-ready gate could never fire — while a `needs-human` item **does** reactivate when its body is edited past the acted baseline, because a human may answer the parked question by editing the same comment/review body (pin the baseline with `--acted-edit-id` at mark time to close the answered-by-edit race). A *new* comment is simply a new id and stays actionable; a dispatched item's edit still counts as external review activity (the `edit_id` body hash feeds the settle clock, since `gh pr view` exposes no `updatedAt`) without re-opening it. Both streams count as one **review** stream for the trajectory (a bot re-posting fresh top-level nits every commit is a treadmill, not silence) and for the merge-ready backlog (`counts.threads` **and** `counts.comments` must both be 0).
- **CI checks.** A failing check on the current head is actionable until `mark --check <key>` records it. A new head commit ID clears the head-scoped dispatch set and re-evaluates every check, so green is never carried across a bookmark push.

- **Current-base merge identity.** `base.historical_oid` is historical PR metadata. `base.graphql_oid` and the independent exact host-ref API read must agree; a mergeable result also requires GitHub's generated test merge to name the observed base/head parents. Race, pending, and probe-error results conservatively block. There is no secondary VCS transport fallback.
- **Bookmark currency.** `bookmark_currency` is the third stream. Its identity binds host-qualified base/head commit IDs, merge status, and route. Never mutate dependent bookmarks.

  Preview parked conflict evidence first. Fingerprint sorted conflicted paths plus jj materialized conflict identities, excluding the base commit ID. Claim the exact item before host update or creation of a jj merge change; stale invocation fencing and budget win.

  Re-entry into `claimed` is reconciliation-only, never a direct resubmission. Record the observed recovery as `--currency-outcome mutation-observed`, `--currency-outcome proven-no-mutation`, or `--currency-outcome ambiguous`. Exactly one retry follows only conclusive no-mutation proof and the engine backoff. Ambiguous recovery never retries or resubmits; keep reconciling or park. Confirm or park the same exact item with `--currency-disposition confirmed|needs-human`; never transfer a claim to a moved head/base observation.

`ci_dispatched`, feedback dispositions, and `bookmark_currency_state` are the journal; unmarked work stays actionable and claimed currency stays reconciliation-only.

## Merge-readiness and the settle window

Use GitHub's required-check/review computation, then require chain and bookmark currency clear. `bookmark_currency_blocker` blocks readiness until fresh remote evidence clears it.

The settle window guards the most damaging false positive: "CI went green, told the user to merge, then feedback landed."

- The script stamps `last_change_at` whenever checks, review evidence, the head commit ID, merge state, or reviewer signals move. Each snapshot emits `quiet_seconds`.
- "Looks ready" requires `quiet_seconds >= 300` (default) on top of a CLEAN mergeable state and zero actionable backlog (threads **and** non-thread feedback). A reviewer or bot still working shows up as recent activity → `quiet_seconds` resets.
- A current-head review signal creates an incomplete lifecycle even if it later disappears. The detector blocks a live 👀 through 900 quiet seconds; the skill applies the same 15-minute floor to a disappeared/non-👀 signal, may extend once to 1800 seconds from concrete prior-round timing, and never re-arms past 30 quiet minutes after the last observable movement solely for the unchanged signal. A new signal transition is movement and resets that quiet phase; the ceiling is not wall-clock time from the first 👀.
- **It is a cooling-off signal, not a guarantee.** Five quiet minutes is evidence the PR stopped moving, not proof no review is coming. Report "looks ready — your call," never "safe to merge"; a stalled lifecycle uses the stronger cautious-ready disclosure and resume path from SKILL.md.

## Concurrency

- **Lock.** The script takes a file lock around each state read/write. It cannot span the agent's mutations (which happen between script calls), so it is necessary but not sufficient.
- **Pre-mutation claim and revalidation.** Before `BEHIND`/`DIRTY` mutation, claim the exact item and prove its observed head/base commit IDs are current. Treat snapshots as hints, never mutation-time guarantees.
- **Interrupted jj merge change.** On re-entry, inspect `jj status`, `jj log -r '@ | parents(@)'`, and remote bookmarks. Reconcile to the validated change or restore/abandon only the proven operation before trying again.

## Managed-stack continuation

Sequential babysitting requires fresh `manager_status == "confirmed"` and stack-wide posture. It uses one target and watcher. On transition, stop the watcher, re-read `gh stack view --json`, require the immediate eligible entry, run `jj git fetch --remote <remote>`, and move a clean jj workspace to the next bookmark with `jj edit <next-bookmark>`. Initialize that layer with `--continue-invocation`, the same invocation ID/start/budget, carried dead time, and the same posture. One budget covers traversal; loss of manager confirmation ends continuation.

Under `stack-land`, after settle the caller-owned land step merges the bottom-most open settled PR then syncs before continuing; recipes live in `references/stack-commands.md`. A just-landed MERGED outcome is a transition, not a Terminal exit for the run.

The one-time semantic-scope offer (under `target`), posture table, and draft/human boundaries live inline in SKILL.md because they are routing decisions, not detector mechanics. A manual dependency chain never enters this continuation path; it remains target-local even when its base/head relationships have the same shape.

## Edge cases

- **Managed stack:** stale/unknown manager currency becomes `stack-blocked`. Record manager-ordered open bookmarks and remote-tracking commit IDs before delegation. After a target push, re-confirm manager ownership, require a clean jj workspace, run `jj git fetch --remote <remote>`, and verify the target bookmark plus `<target-bookmark>@<remote>` still select the pushed revision. Rebase open dependents with `jj rebase`, advance only their bookmarks, and push each explicitly with `jj git push --bookmark <bookmark> --remote <remote>`. Re-fetch, preserve partial progress, and surface the first rejected/divergent layer. Preserve conflicts for inspection or restore only the proven jj operation; never guess at stack membership or overwrite moved bookmarks.
- **Manual dependency chain:** keep the requested PR as target, qualify readiness relative to its parent, and never mutate dependent changes/bookmarks. A target bookmark push may make children stale; report that residual.
- **Normal-base `BEHIND`:** require positive host update capability, claim and revalidate exact head/base commit IDs, then invoke GitHub's preconditioned update-branch endpoint once. HTTP 422 is stale; fresh ancestry and a clear currency gate are required for confirmation.
- **Normal-base `DIRTY`:** prove jj bookmark-push authority without mutating, require a clean PR-head workspace, fetch with `jj git fetch --remote <remote>`, and create a disposable, undescribed `jj new <pr-head-revision> <base-revision>` merge preview. Fingerprint conflicted paths/materialized conflict identities, excluding the base ID. Restore the prior working-copy change and abandon the preview unless applying the proven mechanical repair.

  A mechanical resolution requires positive intent evidence with no reasonable alternative. Otherwise restore/abandon the preview and park. For a mechanical repair, compose the actual merge change's description. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure without imposing fixed syntax. Create the actual merge change with `jj new -m "<merge-description>" <pr-head-revision> <base-revision>`, resolve only the previewed conflict, validate, advance `<pr-bookmark>`, and run `jj git push --bookmark <pr-bookmark> --remote <remote>`.
- **Manager/relationship probe error:** continue review and CI, but perform no bookmark-currency mutation or ready declaration.
- **External head movement:** the head commit ID moved under the loop. Re-snapshot; never clobber unrelated pushed changes or moved bookmarks.
- **PR closed or merged externally:** detected as `pr_state != "OPEN"` on any tick → clean exit with a final status — **except** a just-landed MERGED from this run's authorized `stack-land` land step, which is a layer transition (see Managed-stack continuation above), not a Terminal exit.
- **needs-human feedback:** `ce-resolve-pr-feedback` leaves those threads open and returns them as escalations; record each with `mark ... --disposition needs-human`, keep doing independent CI work, and surface them. Never auto-decline or auto-resolve a thread you did not fix. A parked `needs-human` is a **standing residual** (SKILL.md Step 3): it blocks *declaring* merge-ready but does **not** end the watch — keep handling new CI and later review rounds around it. Only a true stop (terminal / looks-ready / the budget cap) ends the active layer, not a count of accumulated escalations; an authorized confirmed-managed-stack run may transition after a looks-ready layer as defined inline in SKILL.md.
- **No bookmark-push access / fork PR:** detect the failed `jj git push` authority, report it, and stop.
- **CI that never completes:** a check stuck `IN_PROGRESS` for a long time will keep the loop from settling. When the invocation budget is reached — either the 8h **active** cap (`invocation_elapsed_seconds`, which excludes suspended time) or the 3-calendar-day **wall-clock backstop** (`invocation_wall_elapsed_seconds`) — hand back with the measured `invocation_elapsed_seconds` and the `max_runtime_ceiling` that fired; never substitute the age of persisted PR state or automatically start another budget.
- **Rate limits / transient API errors:** honor the reset time, back off, resume. The claim→confirm protocol protects against replay.

# Cross-Model Execution Contract

Load this reference only after the cross-model engine is selected or recovery of an existing run is activated. It owns fixed-route authority, workspace isolation, durable receipts, fallback, recovery, and canonical Jujutsu integration. Process completion and worker prose never substitute for controller and Jujutsu evidence.

## Fixed Route

Use only targets `codex`, `claude`, `grok`, `cursor`, and `composer`. Keep target, harness/intermediary route, requested model, actual model, and receipt status separate.

Controller route tokens are exactly `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`. The latter two route through Cursor; `grok-cli` is native Grok. A same-host default request collapses to native execution when no distinct model or serving route was requested.

For an ordered preference, preflight candidates without egress. Skip only an equivalent self-route or a candidate proven unavailable. The documented adapter is the default; live CLI help may refine flags only within the sanctioned harness/model family while preserving restrictions. Once dispatch begins, route, model family, provider, and intermediaries are locked.

`prefer` and `require` both fall back to the current harness and session model after the requested candidates are unavailable. `require` prevents substitution by another external recipient while its requested route remains viable; it does not authorize permission elevation or turn unavailability into a user-choice gate.

## Sanction And Authority

Before egress, disclose and durably record the binding source, fixed recipient and intermediaries, exposed repository/unit material, inherited restrictions, and whether each restriction is enforced by the adapter or cooperative. Workspace isolation contains accidental concurrent mutation but is not an OS security boundary.

The worker receives one unit, one Jujutsu workspace, one fixed recipient, and inherited authority that it may narrow but never broaden. It has no authority to describe or abandon changes, rebase, squash, split, manage bookmarks, push, open a PR, schedule peers, switch recipients, choose fallback, or expand scope.

Jujutsu automatically snapshots worker edits into the workspace's working-copy change. Successful output terminalizes that change as transport evidence. Only the host may inspect it, duplicate and squash it onto the canonical working-copy change, run authoritative verification, apply a description, start the next change, publish a bookmark, or enter an owning tail.

A Codex `workspace-write` worker treats socket binds, OS permission checks, and peer-credential probes as host-owned. Preserve the host command and result; sandbox `EPERM` is not proof that the host lacks the capability.

Ordinary synchronous native units stay in the active workspace and native subagent isolation remains harness-owned. Only this external controller may create sibling Jujutsu workspaces under `<workspace-root>/.tmp/rocketclaw/ce-work/<run-id>/`. Outside Jujutsu, its state root is `<current-directory>/.tmp/rocketclaw/ce-work/<run-id>/`. Never create a unit workspace beneath another unit workspace.

## Receipts

Direct and return-to-caller runs preserve:

- resolved `implementation_engine_binding`;
- requested and actual routes, including intermediaries;
- requested and actual model identities plus receipt status;
- fallback reason or `null`;
- source kind and digest;
- run id and per-unit process, transport-change, integration, verification, canonical-change, and cleanup receipts;
- a plan checkpoint only when the plan was the sole canonical diff;
- blockers and recovery path.

The run is complete only after every required unit has accepted canonical-change evidence and source-wide verification has a successful stored receipt.

## Bare-Prompt Source

When Phase 0 has already bounded a bare prompt, write one implementation brief under `<workspace-root>/.tmp/rocketclaw/ce-work/`; outside Jujutsu, use the current directory's local equivalent. Never use an OS-global temporary location. Include only:

- `Request`;
- one observable `Goal`;
- bounded `Scope` and discovered patterns;
- `Acceptance and verification`;
- inherited `Constraints and exclusions`;
- conservative units whose dependencies and expected files are known.

Do not initialize or egress when goal, scope, or verification is unresolved. Pass the workspace-local brief and its SHA-256 to `init`; the controller-owned copy becomes authoritative.

## Serial Unit Transaction

Run one ready unit at a time from the canonical Jujutsu workspace. Resolve bundled files from this skill's directory. Use `jj -R <canonical-workspace>` for host inspection, never shell-directory assumptions.

Use separate host calls and one state-changing controller transition per call until scope inspection. `start` returns before supervision. Runner waits are at most 60 seconds, followed by separate sync and progress updates. A nonzero controller, runner, verification, or Jujutsu exit ends that call and enters recorded recovery before another transition.

1. **Resolve and sanction.** Resolve one candidate, verify restrictions, and record an egress object with exact plural keys `route`, `intermediaries`, and `restrictions`.
2. **Initialize durable state.** `unit-workspace.py init` creates the run root. A repository plan uses `--plan` and `--plan-digest`; if it is the only diff, call `checkpoint-plan --checkpoint-description <dynamic-description>` to describe that plan change and run `jj new`. A prompt brief uses `--prompt-brief` and `--prompt-digest` and requires an empty canonical working-copy change. Re-read repository identity, workspace, current change/commit, source digest, conflicts, and diff before preparation.
3. **Prepare a bounded packet.** Write it under the controller's recovery path. `prepare` creates a sibling workspace from the exact canonical commit and returns authoritative attempt, packet, authorization, workspace, result-directory, and digest values.
4. **Start one author and bind it immediately.** Preserve the run-root environment selection used by the controller and run this canonical shape, filling every value from `prepare`; both digest positions equal `prepare.packet_digest`, and the result path is `<prepare.result_dir>/implementation-result.json`. Invoke `prepare.adapter` directly as the first worker argv. Set `ROCKETCLAW_PEER_HARD_SECS=7200`; set `ROCKETCLAW_PEER_IDLE_SECS=600` only for qualified incremental activity and `0` for hard-only activity.

   ```bash
   SKILL_DIR="<absolute path of this skill directory>"; ROCKETCLAW_WORK_RUNS_ROOT="<controller runs root>" ROCKETCLAW_PEER_HARD_SECS=7200 ROCKETCLAW_PEER_IDLE_SECS="<600 or 0>" "<resolved Python interpreter>" "$SKILL_DIR/scripts/peer-job-runner.py" start --skill ce-work --run-id "<run-id>" --label "<unit-id>" --input-digest "<prepare.packet_digest>" --result-path "<prepare.result_dir>/implementation-result.json" --no-sweep -- "<prepare.adapter>" "<prepare.authorization_path>" "<prepare.workspace>" "<prepare.packet_path>" "<prepare.packet_digest>" "<prepare.result_dir>"
   ```

   `start` returns `job_id`. In the immediately following host call, preserve the same run-root selection and bind that returned id to the exact attempt before status, wait, result, reap, fallback, or another dispatch:

   ```bash
   SKILL_DIR="<absolute path of this skill directory>"; ROCKETCLAW_WORK_RUNS_ROOT="<controller runs root>" "<resolved Python interpreter>" "$SKILL_DIR/scripts/unit-workspace.py" record-job --run-id "<run-id>" --unit-id "<unit-id>" --attempt-id "<prepare.attempt_id>" --job-id "<returned job_id>"
   ```

   The adapter must obtain `authorize-dispatch` before egress.
5. **Observe without steering.** Interleave runner `status --skill ce-work` or bounded `wait --skill ce-work --max-secs 60` with controller `sync-job`. Every runner `status`, `wait`, `result`, or `reap` call for this attempt must use `--skill ce-work` and the exact same `ROCKETCLAW_WORK_RUNS_ROOT` or `ROCKETCLAW_PEER_JOBS_ROOT` selection used by `start`; never let bare-job lookup cross a run root. Report route, elapsed time, latest activity, posture, and state. A live or unreachable attempt remains authoritative until terminal evidence or explicit reap.
6. **Terminalize the complete change.** `terminalize` requires the workspace change to have the recorded base as sole parent, contain no conflicts, and expose a complete Jujutsu diff. Inspect summary, paths, types, adapter result, expected scope, and any expansion request before integration.
7. **Integrate once.** Invoke `unit-workspace.py integrate --run-id <run-id> --unit-id <unit-id> --change-description <dynamic-description> --verification-summary <summary> [--allowed-change <recorded-revision>] -- <verification-argv>`. Use explicit `bash -o pipefail -c` only when the verification contract itself contains shell syntax.
8. **Let the transaction own mutation.** It acquires the lock, preflights revision evidence, duplicates transport onto `@`, squashes the duplicate into `@`, runs authoritative verification, reconciles exact canonical state, applies the supplied description, records accepted change and commit ids, starts a fresh change with `jj new`, forgets the unit workspace, abandons transport, and releases the lock.
9. **Trust only its receipt.** Before any `jj restore`, the controller snapshots `@` again. It mutates only when that snapshot exactly equals the recorded pre-integration state or an exact controller-recorded applied state; any other state is an unrelated or unproven edit and blocks without touching `@`. An eligible restoration uses `jj restore --from <recorded-commit> --to @` and restores the recorded description. The controller discloses ignored-state divergence but never restores or deletes ignored files. Unprovable restoration retains lock, workspace, transport, and recovery path. Accepted changes interrupted during finalization are resumed, never redispatched.
10. **Run source-wide gates.** `verify-run` requires an empty conflict-free `@`, proves accepted changes are ancestors, captures the actual verification exit, and stores a receipt. It restores tracked state only when the post-command snapshot is an exact controller-owned restoration source; otherwise it preserves the changed state and lock as a blocker. It discloses ignored-state divergence, and failure retains its workspace-local log and blocks the owning tail.

Project every transition into commentary or the return envelope: source, route, checkpoint, dispatch, activity, terminal result, scope inspection, integration, restoration, verification, canonical change, cleanup, blocker, and recovery path.

## Parallel Waves

Use a wave only when dependencies, paths, shared contracts, migrations, generated/configuration surfaces, runtime resources, and merge cost establish independence. Uncertainty selects serial execution. Cap a wave at 3-5 workers.

1. Record one wave id, dependency order, and canonical base commit. Prepare every member as a distinct sibling workspace from that base.
2. Terminalize every member before integrating any. Inspect all transport inventories; path or semantic contention stops the wave.
3. Integrate sequentially under the canonical lock. Each transport is duplicated and squashed onto the advancing `@`, then independently inspected, verified, and described.
4. While the lock is held, call `wave-advance --canonical-change <accepted-commit>` so later members accept only manifest-recorded canonical revisions.
5. Conflict, expansion, semantic collision, verification failure, or description failure enters exact restoration. No sibling, retry, or fallback starts before restoration and lock release.
6. Repeated collision, broad edits, or unprovable restoration disables more waves. Preserve inspectable workspaces and transport changes.

## Recovery And Fallback

A supplied run id uses `resume --run-id <id>` before ordinary input classification. Without one, discover a plan-backed run with `resume --repo <canonical-workspace> --plan-digest <digest>`. Prompt-backed runs require their disclosed id. Resume only one matching repository/source run; ambiguity lists candidates and blocks. Recovery discovers and migrates v1 manifests only under the current workspace-local `.tmp/rocketclaw` root. Modern or legacy root overrides are accepted only when their resolved path remains inside the active Jujutsu workspace's `.tmp`, or inside physical CWD's `.tmp` when no Jujutsu workspace exists. The controller migrates only a pristine v1 run whose repository identity, source, empty lifecycle, and current revision map exactly to Jujutsu; any active or ambiguous v1 state is preserved and returns a non-destructive blocker without redispatch.

Completed recovery is observation-only. Resume may adopt one matching job, monitor a live job, terminalize authoritative output, restore interrupted integration, finalize an accepted canonical change, clean a finalized workspace, or release its lock. It never dispatches, repeats accepted integration, reruns completed verification, or enters a shipping tail.

Use `status`, `reap`, and `cleanup` for preserved work. Explicit abandonment requires the exact transport commit id or terminal job id. A corrected retry uses the same run id and a fresh attempt id only after exact restoration, cleanup, and lock release.

Post-start fallback is an atomic gate. After authoritative terminal failure or exact restoration, call `claim-fallback`. One claim authorizes one native implementation. Live or unreconciled successful output refuses it. After native implementation is verified and described, call `complete-fallback --accepted-change <revision> --evidence-digest <sha256> --summary <summary>`, clean the retained external workspace, then run source-wide `verify-run`.

## Tail Ownership

The engine changes implementation authorship only. Standalone use resumes quality and shipping after local verification. `mode:return-to-caller` returns implementation receipts with `standalone_shipping_skipped: true`. External workers never inherit either tail. After controller `READY`, continue through its protocol or return blocked with the recovery path; native work requires explicit fallback authorization.

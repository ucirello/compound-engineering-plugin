# Cross-Model Execution Contract

Load this reference only after the cross-model engine is selected or recovery of an existing external run is activated. It defines the fixed route, authority, identity, receipt, JJ workspace, and serial integration contract. The host drives the bundled controller, detached runner, and adapter; no worker response or process exit substitutes for controller and JJ evidence.

## Fixed Route

Use only targets `codex`, `claude`, `grok`, `cursor`, and `composer`. Keep target, harness/intermediary route, requested model, actual model, and receipt status separate. Controller route tokens are exactly `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`.

Resolve ordered preferences before egress. Skip an equivalent same-host default and continue after a candidate is observably unavailable. The first qualified candidate becomes fixed. After dispatch begins, never switch recipient, provider, intermediary, or model inside the attempt. Same-host default requests collapse to native execution with requested and actual identity recorded separately.

Both `prefer` and `require` fall back to the current harness and session model when the fixed route is unavailable. Requirement strength prevents substitution by another external recipient; it does not authorize privilege elevation, prompting, or failure solely because the requested route is unavailable.

Before egress, disclose and record the binding source, fixed route and intermediaries, exposed unit material and workspace content, inherited restrictions, and whether confinement is adapter-enforced or cooperative. A JJ workspace isolates concurrent working-copy changes but is not an OS security sandbox. A required restriction the adapter cannot enforce makes the route unavailable.

## Worker Authority

The worker receives one unit, one controller-owned JJ workspace, one fixed recipient, and inherited authority only. It may edit and run scoped checks there. It must not describe, squash, duplicate, abandon, rebase, or publish a change; move or create a bookmark; operate on another workspace; invoke Git state-changing commands; push; open a PR; schedule peers; or broaden scope. The host owns transport inspection, canonical squash, authoritative verification, descriptions, bookmarks, and the shipping tail.

External unit workspaces are siblings registered through `jj workspace add` and live below `$(jj workspace root)/.tmp/rocketclaw/ce-work/<run-id>/`. Outside a JJ repository, scratch falls back to `<current-directory>/.tmp/rocketclaw`; it never uses a global temporary directory. Ordinary native work remains in the active workspace unless the harness owns isolation.

## Receipts

Preserve `implementation_engine_binding`, requested and actual route/model, `fallback_reason`, source kind/digest, `run_id`, per-unit process/workspace/integration/verification/cleanup receipts, a plan checkpoint when applicable, blockers, and `recovery_path`. Detached completion alone is not success. A complete unit has a host-accepted canonical JJ change and authoritative verification.

## Bare-Prompt Source

For concrete bare-prompt work, write one bounded brief below `$(jj workspace root)/.tmp/rocketclaw/ce-work/` or the local fallback. Include Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative units. Do not include raw conversation, unrelated context, credentials, or speculative scope. If Goal, Scope, or verification cannot be bounded, clarify or plan before initialization or egress.

## Serial Unit Transaction

Run one ready unit at a time from the canonical JJ workspace. Resolve scripts from this skill's directory. Use one state-changing controller transition per host tool call until scope inspection; `start` returns before supervision, waits are capped at 60 seconds, and every nonzero exit stops the sequence for status and recovery inspection.

1. Resolve, preflight, sanction, and record the fixed route. `init` receives exact plural egress keys `route`, `intermediaries`, and `restrictions`.
2. Initialize state with `unit-workspace.py init`. State belongs below the workspace-local `.tmp/rocketclaw` root. Do not pre-create a run directory. A selected plan may be the only changed path; compose a runtime-conformant description and call `checkpoint-plan --description <description>` when that checkpoint is needed. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime conventions win; apply compatible Go guidance to message quality, clarity, and structure, and impose no fixed message shape. Unrelated changes make external execution unavailable.
3. Write a bounded unit packet directly below the controller-returned recovery path. `prepare` receives its source path, unit id, exact base revision, dependencies, optional wave fields, and activity posture. Dispatch only the returned workspace, packet, digest, authorization, attempt id, result directory, and adapter.
4. Start `peer-job-runner.py` with `CE_WORK_RUNS_ROOT` set to the parent of the controller-returned `<run-id>` recovery path, `--skill ce-work`, label equal to the unit id, the controller packet digest, and result path `<result-dir>/implementation-result.json`. The configured root must remain below the canonical workspace's `.tmp/rocketclaw`. Invoke the returned adapter directly. Use `CE_PEER_HARD_SECS=7200`; use `CE_PEER_IDLE_SECS=600` for trustworthy incremental activity and `0` for hard-only activity. The adapter must obtain controller `authorize-dispatch` before egress.
5. Observe through separate runner `status` or bounded `wait` calls followed by controller `sync-job`. A live or unreachable attempt remains authoritative. Reap only through the explicit controller/runner path.
6. On authoritative completion, call `terminalize`. Inspect `jj diff --summary -r <transport-change>`, `jj diff --git -r <transport-change>`, changed paths, modes, renames, deletions, conflicts, worker evidence, expected scope, and any scope-expansion request. Unexplained output is a blocker.
7. Integrate only through `unit-workspace.py integrate --run-id <run-id> --unit-id <unit-id> --change-description <description> --verification-summary <summary> -- <verification-argv>`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository syntax and conventions win; compatible Go quality applies only where it does not conflict. Do not impose fixed messages, types, scopes, prefixes, templates, or examples.
8. The transaction acquires the integration lock, records the canonical JJ operation, preflights a clean working-copy change, squashes the transport change into `@`, runs authoritative verification, proves the working-copy change stayed exact, describes it, creates a fresh child change, records the accepted canonical change, cleans the unit workspace, and releases the lock. A failure restores the recorded JJ operation before retry, sibling work, or fallback; unprovable restoration retains the lock and recovery path.
9. After all units are accepted, run source-wide gates through `verify-run`. It starts from a clean working-copy change, captures the command exit directly, restores any tracked mutation through the operation log, records local `.tmp/rocketclaw` artifact divergence, and retains failed logs below that root.

Filesets limit partial finalization; revsets select changes. Quote expressions with operators or metacharacters. `jj squash --from <source> --into <destination>` moves selected content into an existing destination and may abandon an emptied source; `jj duplicate <source> -o <destination>` copies a change onto a new parent while preserving the source. The controller uses squash for accepted transport and operation-log restoration for failure; use duplicate only when preserving an independently useful source change is the required outcome. Use change IDs for mutable logical work, commit IDs for immutable receipts and Git interoperability, `jj evolog` for change evolution, `jj operation log` for repository operations, and `jj log -r 'trunk()..<change>'` for unpublished stacks. There is no index or staging area.

## Parallel Waves

Use a wave only when dependencies, declared paths, semantic contracts, generated/config surfaces, runtime singletons, and expected integration cost all support independence. Every member starts from one recorded base in a distinct JJ workspace and terminalizes before the first canonical mutation. Stop on path overlap or semantic contention. Integrate sequentially in dependency order against the advancing canonical change; a conflict-free squash is not semantic proof. Repeated collision or unprovable restoration disables further waves.

## Recovery And Fallback

A supplied run id is authoritative. Without one, plan-backed discovery matches repository identity and plan digest and blocks on ambiguity; prompt-backed runs require the disclosed id. Recovery reconciles durable evidence but does not redispatch, reimplement, rerun completed verification, or enter a shipping tail.

After authoritative failure or exact restoration and lock release, `claim-fallback` authorizes native implementation exactly once. After a runtime-conformant native JJ change and local verification, `complete-fallback` records the accepted change and evidence digest, then `verify-run` closes the source-wide gate. A live job or successful unreconciled transport cannot be bypassed.

The engine changes implementation authorship only. Standalone use resumes the quality and shipping workflow. Return-to-Caller Mode returns implementation and local-verification receipts with `standalone_shipping_skipped: true`. External workers inherit neither tail.

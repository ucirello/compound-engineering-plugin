# Cross-Model Execution Contract

Use native `opencode.models`, subagents, and shell tools, not another harness dispatcher. The host owns scheduling, durable receipts, scope inspection, integration, verification, recovery, and canonical changes. A worker result or terminal process alone never proves completion.

## Resolve and preflight one route

Apply `execution-engines.md` authority order. Preserve `work_engine_mode: off | prefer | require`, ordered `work_engine_preferences` objects (`harness`, optional `model`), and `work_engine_effort` maps. Resolve each key independently from `.rocketclaw/config.local.yaml` then `config.yaml`; a present local list/map, including empty, replaces the team value. Keep configured provider/model/effort intent, not old CLI transport. Live strict intent fixes the requested identity; typed caller bindings remain one exact candidate.

Discover exact available model IDs with `opencode.models`. Preflight ordered candidates without sending repository material. A configured harness is requested provenance, not permission to launch it. Resolve a compatible native provider/model only when the identity and effort are supported; never silently replace an explicit pin. Record unavailable candidates and reasons. Collapse a same-session default route to native inline execution and disclose any unapplied effort. Invalid/non-map effort requests are disclosed, not interpreted as shell syntax.

This skill explicitly requests implementation subagents. Under a user-or-skill delegation rule this satisfies the skill-requested exception; do not demand a second user request. Actual higher-priority prohibitions still apply. Model selection is separate: if a model override requires explicit user permission, omit the optional model argument; use a suitable inherited model, but disclose unmet configured intent. Same-model workers do not prove cross-model independence. Classify missing tools, permission denial, model rejection, and depth/capacity errors from actual evidence; never evade them through shell harnesses. Required independent coverage that cannot run remains incomplete.

For both `prefer` and `require`, unavailable preflight discloses requested/actual identity and every reason once, then continues on the current session model without substituting an unrequested recipient. After dispatch starts, no fallback or replacement begins until that attempt is authoritatively terminal or stopped. Restrictions that cannot be enforced make the route unavailable; workspace isolation is cooperative containment, not a security sandbox.

## Durable authority and source

Store private run evidence under the canonical absolute workspace root's `.tmp/rocketclaw/ce-work/<run-id>/`. Overrides must remain under that workspace's `.tmp`, never OS temporary or global cache storage. Atomically write/read back a manifest for each transition, using a single host writer and integration lock. Record repository identity, canonical root, bookmark, exact base/head commit IDs, source kind/path/SHA-256, run/unit/attempt IDs, dependencies/wave base, expected paths, packet digest, fixed requested route/model/effort, actual route/model and receipt status, restriction posture, native job/session ID, lifecycle timestamps, verification exit/log/digest, ignored-state divergence, canonical commit, cleanup, blockers and recovery paths. Actual model and effort remain unverified unless runtime evidence proves them.

Plan-backed work copies only the selected plan and verifies its digest. A selected plan that is the sole dirty path may receive a disclosed host-only plan checkpoint using the message standards in `implementation-loop.md`; unrelated dirt blocks isolated execution. Prompt-backed work requires a clean canonical snapshot and a bounded brief containing Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative P-units. Missing bounded scope or authoritative verification returns to triage. Never expose raw conversation, credentials, or unrelated material.

## Isolation and authority

Detect and reuse existing harness isolation under its verified name, even an old name. Native isolation must use supported harness ownership/adoption; do not bypass its lifecycle. For a newly authorized isolated workspace capture the local date once, normalize any caller date prefix, and select `YYYYMMDD-meaningful-kebab-slug`, with identical workspace name and destination basename. Check registrations and paths; use `-2`, `-3` collisions, preserving the chosen identity across retries/resumes and midnight. Keep PR/source bookmarks unchanged.

From the source absolute root create only an owned local `.tmp` destination:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Adopt the workspace through the supported native session move before working there. Unsupported harness colocation, naming or adoption is a compatibility blocker, not permission for a Git fallback or silent manual workspace. Do not rename/recreate existing isolation to enforce new naming.

Workers receive one bounded unit packet: relevant goal/acceptance, dependencies, expected files, verification strategy, cited requirements/prototypes and matched pack rules, exclusions, inherited restrictions, exact root/base and packet digest. Rules never widen authority. Workers may edit and self-check only their unit; no canonical commits, push, PR, shipping, peer scheduling, scope expansion or recipient switch. The host independently inspects the whole output, including untracked, binary, mode, rename and deletion evidence.

## Serial host transaction

Perform one visible state transition per host tool call; a nonzero operation stops advancement. Never bundle start/wait/integrate or loop over workers in an unattended shell script.

1. Record sanctioned source, recipient/provider/intermediaries, exposed material, enforceable/cooperative restrictions and clean canonical base before dispatch. Once ready, the chosen engine is locked; overhead or triviality does not authorize bypassing it.
2. Prepare a fresh immutable attempt packet and digest. Persist authorization binding run/unit/attempt, root/base, fixed route and exact packet. Dispatch one native subagent with that packet and record the returned job/session ID immediately. A lost response is uncertain live work, not permission to duplicate it.
3. Observe through native status/wait tools, at most 60 seconds per wait, publishing elapsed time, activity and terminal state separately. Preserve a 7200-second hard bound and 600-second progress-reset idle bound only where activity is trustworthy; otherwise disable idle expiry (`hard-only`). Lack of incremental output alone never proves failure. Stop through supported native cancellation and verify terminal state before replacement; retain uncertain jobs and workspaces.
4. At authoritative completion snapshot output with native JJ and pin an owned recovery bookmark to the exact result commit. Require the recorded base as sole parent and complete final tree. Use absolute target-root cwd for every JJ command. Inspect `jj diff --from <base> --to <result>` and complete status/inventory, not only worker claims. Unexpected scope blocks before integration.
5. Acquire the single integration lock and persist exact pre-fold canonical commit/tree, bookmark and tracked/conflicted/untracked inventory plus ignored metadata. Verify canonical state still equals the recorded base or an exact previously recorded wave advance. Apply only the inspected delta using native JJ (for example `jj squash --from <result> --into <canonical-change> --keep-emptied` with exact verified IDs); conflicts stop, never silently resolve. Preserve the pinned source and pre-fold recovery refs.
6. Run the authoritative verification command as direct argv; use an explicit pipefail shell only for shell syntax. Capture exit status directly, with Python bytecode disabled. Require unchanged tracked tree/bookmark/parent and status-visible inventory after verification. Record ignored entries created/removed/changed with bounded samples; do not copy, restore or delete ignored state. Caches, `.env` and local databases are not protected from a misbehaving verification command.
7. On success record verified state and create the host-only canonical change description using `implementation-loop.md`; pin its exact commit and parent/tree evidence before cleanup and lock release. A worker transport is never the canonical commit. On failure forbid the commit and restore only run-owned tracked changes from the saved exact pre-fold revision with native JJ; unknown or unrelated changes block restoration. Prove exact snapshot equality before releasing the lock, retrying, falling back or advancing any sibling. If proof fails retain lock, refs, workspace and recovery path.
8. After all units are terminal, run source-wide authoritative gates under the same clean-snapshot/reconciliation contract and persist a successful `RUN_VERIFIED` receipt. Cleanup success or unit success cannot replace this gate. Missing/failed coverage blocks completion.

## Parallel waves

Only the Parallel Safety Check in `execution-strategy.md` authorizes a wave; uncertainty selects serial work. Cap at 3–5 independent workers, each isolated from one recorded clean base. Terminalize and inspect every result before the first integration; same-path or semantic/interface contention blocks the wave. Integrate sequentially in dependency order, verifying against the advancing canonical tree. Record each exact host-owned canonical commit as the only allowed later wave head. A clean apply is not semantic compatibility. Restore and release the prior lock before any continuation; affected dependents stay queued. Preserve unaffected siblings. Repeated collisions or broad edits disable further waves.

## Resume and fallback exactly once

A supplied `implementation_run:<safe-id>` identifies durable state, not permission to dispatch. Resume before input classification. Without an ID, discover only one unfinished plan-backed manifest matching repository/bookmark/source digest; prompt-backed runs require their disclosed ID. Multiple matches, unsafe manifests, or foreign identity block selection. Never infer an ID from conversation or arbitrary directory order.

Reconcile native job evidence and exact trees/parents before any transition. Adopt at most one matching unbound native job; uncertain live state remains live. Reuse a pinned transport only when sole parent and full tree match. Reconcile a landed apply or canonical commit only from exact recorded pre/post state; never redispatch/reapply/recommit or run either shipping tail during resume. A completed manifest with all terminal units and successful run-wide receipt is observation-only: return stored evidence without rerunning tests/build/format/install/generation. Missing evidence is a blocker.

After authoritative failure/timeout/stopped-without-result, exact restoration or explicit abandonment, and lock release, atomically record one `claim-fallback` for that unit. Both modes permit exactly one current-session native fallback; a live job or unreconciled successful output refuses it. An existing claim cannot start another worker. Record `complete-fallback` only with accepted canonical head, local-verification SHA-256 and summary. Retry under the same scalar run ID with a fresh attempt ID, keeping prior receipts and dependency/wave contracts unchanged. Never mint a new run to evade recovery.

## Cleanup and tail ownership

Cleanup requires explicit run-owned disposal authority, terminal workers, integrated output where required, exact registration/name/absolute path and no still-needed references. Copy and read back receipts and recovery evidence outside the target first; preserve best/archive/recovery refs. Inspect tracked/conflicted/ignored/untracked content; unrelated or nondisposable files block removal. Stop workers, move active harness sessions to a surviving root, and leave the target. From that surviving absolute root use `jj workspace remove <verified-name>`, then verify both deregistration and directory disappearance. Warnings/incomplete deletion are blockers; retain remaining state, never force-delete or use Git removal. `jj workspace forget` is only unregister-and-preserve-files. Bookmark deletion is separate.

Report every transition, requested/actual identity, fallback reason, plan checkpoint, ignored divergence, blockers and recovery path. Standalone work returns to its quality/shipping steps; `mode:return-to-caller` returns implementation/local verification with `standalone_shipping_skipped: true`. Workers inherit neither tail.

Native JJ references: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .

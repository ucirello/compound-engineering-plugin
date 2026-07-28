# Fixed-Route External Execution

Load only after external routing or explicit recovery activates. The host drives the controller, detached runner, and adapter. Worker output never substitutes for controller and Jujutsu evidence.

## Route And Authority

Allowed targets are `codex`, `claude`, `grok`, `cursor`, and `composer`; fixed route tokens are `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`. Keep target, provider route, intermediary, requested model, actual model, and receipt status separate.

Preflight ordered candidates without egress. After dispatch, never switch recipient or intermediary. A same-provider default collapses to native. `prefer` may fall back only after authoritative unavailability; `require` needs explicit interactive confirmation or blocks headless use.

Before egress disclose and record binding source, recipient/intermediaries, exposed repository/unit material, restrictions, and whether confinement is enforced or cooperative. A worker receives one unit and one controller-owned Jujutsu workspace. It may edit and verify there but may not describe, split, squash, rebase, bookmark, fetch, push, open a PR, schedule peers, switch recipients, or broaden scope.

The host alone inspects the pinned change, squashes it canonically, verifies it, composes its description, advances the working-copy change, updates bookmarks, and owns delivery.

## Durable State

Controller state lives under the canonical workspace's owner-private `.tmp/rocketclaw/ce-work/<run-id>/`, or an explicitly configured `ROCKETCLAW_WORK_RUNS_ROOT`. Prompt briefs and unit packets are created directly under the controller-returned run path; no global scratch surface is used.

Every controller-owned canonical Jujutsu call applies `--config snapshot.auto-track='all() ~ root:.tmp'` so private run state cannot enter the working-copy change. Any direct host Jujutsu inspection while a run exists must apply the same exclusion. Worker-workspace calls retain the project's normal tracking policy because the controller state is outside that workspace root.

Receipts preserve binding, requested/actual route and model, fallback reason, source kind/digest, run id, per-unit process/change/integration/verification/description/cleanup state, plan checkpoint, blockers, and recovery path.

## Controller Protocol

Use one state-changing transition per host tool call until scope inspection. A nonzero controller, runner, Jujutsu, or verification result ends that call. Never script across start, waiting, terminalization, or integration.

1. Resolve and sanction one route. The egress object contains exact keys `route`, `intermediaries`, and `restrictions`.
2. Initialize with `unit-workspace.py init`. A repository plan passes its path and SHA-256. A bounded prompt brief is written under `.tmp/rocketclaw/ce-work` and passed with its digest. Do not pre-create the run directory.
3. If the selected plan is the only active change, compose a repository-native description and call `checkpoint-plan --description`. Unrelated changes block external execution.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there wins over generic guidance. Apply the linked Go guidance only when compatible with those instructions and that history. Do not use a fixed type, scope, template, example, or identity footer.

4. Prepare one bounded unit packet with goal, relevant acceptance/verification, cited requirements, constraints, expected files, evidence strategy, and exclusions. Pass the exact canonical base revision ID, dependencies, wave fields, and activity posture. The controller creates an isolated Jujutsu workspace and returns authoritative packet and authorization paths/digests.
5. Start `peer-job-runner.py` with `--skill ce-work`, the exact unit label and packet digest, and the returned adapter argv. Set `ROCKETCLAW_PEER_HARD_SECS=7200`; set `ROCKETCLAW_PEER_IDLE_SECS=600` only for qualified incremental activity, otherwise `0`. The adapter must obtain `authorize-dispatch` before constructing a prompt.
6. Observe with runner `status`/`wait --max-secs 60` and separate controller `sync-job` calls. Do not infer failure from silence. Reap only explicitly.
7. On authoritative `done`, call `terminalize`. It pins the worker workspace's Jujutsu change by change ID, immutable revision ID, base, digest, and actual changed paths. Inspect the actual diff, modes, renames, deletions, receipt, expected scope, and scope-expansion request before integration.
8. Compose a neutral repository-native description and call `integrate --description <description> --verification-summary <summary> -- <argv>`. Use an explicit pipefail-capable shell only when the check genuinely contains shell syntax.
9. `integrate` acquires the lock, preflights canonical identity and prerequisites, runs `jj squash --from <pinned-revision> --into @`, records the applied revision, performs authoritative verification, proves verification did not mutate canonical state, records evidence, runs `jj describe`, starts a fresh `jj new` working-copy change, records the accepted change, forgets/removes the isolated workspace, and releases the lock.
10. Any pre-description failure restores the recorded Jujutsu operation and proves exact change/revision identity before releasing the lock. Unproven restoration retains lock and recovery state. A crash after description is reconciled, never redispatched.
11. After all units are accepted and cleaned, call `verify-run`. It requires an empty conflict-free canonical working-copy change, captures the direct exit status, restores verification-created tracked changes, proves the starting revision, and records a receipt.

## Parallel Waves

Prepare independent members from one base. Terminalize all before the first squash. Changed-path or semantic collision stops the wave. Integrate sequentially in dependency order. After each accepted change, `wave-advance` authorizes its exact revision for later siblings. Rebase a stale worker change only through an explicit corrected attempt after checking collisions; never blind-squash a stale or conflicting result. Repeated collision disables waves.

## Recovery And Fallback

Recovery with a run id calls `resume --run-id` and never dispatches. Plan-backed discovery without an id is not supported by the v2 controller; require the disclosed id rather than enumerating shared state. A completed run with a successful run-wide receipt is observation-only.

Resume may monitor a bound job, terminalize done output, finish exact restoration, reconcile an accepted described change, clean a workspace, or release a proven lock. It never reruns a tail.

After authoritative failure or exact restoration, `claim-fallback` atomically authorizes one native attempt. A live or successful unreconciled worker refuses fallback. After native work is described, verified, and followed by an empty working-copy change, call `complete-fallback --accepted-revision`; then call `verify-run` when all units are terminal.

The engine changes authorship only. Standalone resumes its delivery tail; return-to-caller returns once with local receipts.

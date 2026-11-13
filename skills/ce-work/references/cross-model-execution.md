# Native cross-model execution

The host remains the controller. Use OpenCode `opencode.models` to discover exact available model IDs, native subagents to execute, and shell for JJ and local evidence. Do not dispatch through another harness or resurrect a bridge script. Configuration and applicable live/caller intent remain authoritative under `execution-engines.md`: preserve `work_engine_mode` (`off | prefer | require`), ordered `work_engine_preferences`, exact model pins, `work_engine_effort`, provenance, and restrictions. An explicit model is never silently replaced by another model. Skip an equivalent host/model candidate and record each unavailable candidate and reason in order.

## Permission, capability, and truthful receipts

Resolve standing keys independently under local-then-team layering: a present local list/map, including empty, replaces that whole key. Preserve this configuration shape:

```yaml
work_engine_mode: prefer
work_engine_preferences:
  - harness: cursor
    model: composer
  - harness: codex
    model: gpt-6.1-sol
  - harness: claude
work_engine_effort:
  codex: xhigh
  claude: max
```

Accepted intent harnesses remain `codex | claude | grok | cursor | opencode | antigravity | pi`; target `composer` denotes Composer-family intent. Optional model is an exact configured ID/family, omission its configured default; effort is a harness-keyed map resolved independently. Invalid non-map effort requests nothing and is disclosed once. An enabled mode without valid candidates is unavailable, never guessed. Do not execute config as shell or CLI flags. Preserve requested legacy target/intermediary identity in receipts while actual execution is OpenCode-native: a harness-specific route that native tools cannot satisfy is unavailable, not silently relabeled. Resolve aliases only with supported discovery and disclose any compatible mapping. Antigravity intent remains Gemini-only, with default candidates `gemini-4-argon` then `gemini-3.8-flash`; exact configured pins remain exact. Composer and Grok-through-Cursor presets remain requested intent, not permission to invoke Cursor.

Both `prefer` and `require` keep the selected identity fixed while viable; exhausted unavailable candidates disclose reasons and fall back once to the current session model without another user-choice gate when permitted. `require` never authorizes substitution with an unrequested external recipient. Once the durable run is ready, latency or convenience cannot unlock native work; only the recorded failure/fallback protocol can.

These instructions explicitly request bounded implementation subagents. Under a host rule allowing user OR loaded-skill requested delegation, this satisfies that exception without another approval. A genuine higher-priority prohibition or actual denial still controls. Model-selection permission is separate: if overrides require an explicit user model request, omit the optional model argument and use an inherited-model worker only if suitable. Discovering a configured tier does not grant override permission. Same-model workers are separate workers, not cross-model independence. Record unmet required model/effort/independence coverage as incomplete.

Verify effective nesting capacity separately; distinguish actual tool absence, permission denial, model rejection, and depth/capacity errors. Never evade a denial or nesting limit through shell or another harness. Before dispatch, resolve and disclose the fixed route/model, source of authority, exposed material, restrictions, requested effort and whether it can actually be verified. If no route qualifies, disclose reasons once and continue native execution only when the existing fallback contract and permissions allow it; do not claim the configured cross-model route completed.

## Durable bounded work

Use a private run directory under the canonical absolute workspace root's `.tmp/rocketclaw/ce-work/`. Preserve `CE_WORK_RUNS_ROOT` as a parent-directory override only within local `.tmp/`; never use OS-global scratch. Record one stable run ID, canonical workspace identity/bookmark/base, plan or prompt digest, fixed recipient, dependencies, expected paths, attempt IDs, and state in a durable JSON manifest. Read back every transition before proceeding; one state-changing transition per host tool call. Refuse symlinked, foreign, ambiguous or malformed run state.

For a plan, checkpoint only the selected plan if it is the sole owned dirt, disclosing that checkpoint. Unrelated dirt makes isolated integration unavailable, not implicitly authorized. For a concrete bare prompt, write a private brief containing Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative P-units. Missing goal/scope/verification returns to clarification. Hash and retain the private source; the original temporary input is not authoritative thereafter.

Prepare a minimal per-unit packet with goal, acceptance criteria, expected files, dependencies, verification, inherited restrictions, exclusions, relevant requirement/key-decision/prototype citations, and matched pack rules. Preserve prototype accessibility/locality qualifications. Do not expose the whole conversation, secrets, or unrelated plan. Hash the packet and bind its exact path/digest, workspace, recipient/model and attempt before dispatch; a second job for an attempt is forbidden. Workers may edit/test only their workspace, not push, integrate, ship, schedule peers, switch recipient, or expand scope. Only the host creates canonical commits.

## Isolation and lifecycle

Detect existing isolation first and respect its harness ownership/lifecycle. Reuse verified existing names unchanged; do not recreate or retrofit colocation. For new isolation prefer a harness-native supported colocated JJ workspace and adopt it through the supported session interface. Unsupported required colocation/naming is a compatibility blocker, not a Git fallback.

For new `ce-worktree` isolation, capture local creation date once and persist it with the selected identity. Normalize task/PR/revision/caller slug to `YYYYMMDD-meaningful-kebab-case`, without double-prefixing. Use the same identity for workspace name and absolute destination basename under the existing local `.tmp/` parent. Check both registrations and destinations; append `-2`, `-3`, etc. on collision, never overwrite. Reuse the recorded identity across retries/resumes and midnight, preserving PR/source bookmarks.

From the source's absolute root:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify base, name, path, colocation and ownership before allowing edits. Every JJ call must have cwd set to its target absolute root; `jj -R` is not a cwd substitute. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-experts/ .

## Observe, inspect, integrate

Record native job/session IDs immediately. Observe via supported native status/results, in bounded waits no longer than 60 seconds; publish route, unit, elapsed time, meaningful activity and state between calls. Keep a 7200-second hard cap; use a 600-second reset-on-progress idle window only when progress is trustworthy, otherwise disable idle termination. A missing update or lost contact is not authoritative termination. Do not duplicate live work or infer success from process completion.

On authoritative completion inspect the entire JJ result against the recorded base, not just worker-reported paths: added/deleted/renamed/binary/mode changes, conflicts, packet scope and expansion requests. Pin the complete result with a recovery bookmark. Require the expected base ancestry and complete final tree; unexplained output blocks integration.

Serialize integration with a run-owned lock. Preflight exact canonical revision/tree and dirt against the recorded snapshot; unknown movement blocks. Apply the reviewed result using native JJ changes (for example a host-owned `jj new` from the verified canonical revision followed by `jj restore --from <pinned-result> -- <owned-paths>`), never moving unrelated paths. Inspect conflicts and actual scope, run authoritative verification with its exit status captured directly, and reconcile tracked tree/revision/paths before committing. Inventory ignored content before/after verification and report changed/removed/created counts and a bounded sample; do not copy, restore or delete it. Ignored files, secrets and databases are not protected by a JJ snapshot.

If verification or any pre-commit step fails, do not commit. Restore only the exact run-owned integration changes from recorded recovery state and prove exact pre-fold equality before releasing the lock or retrying. Unknown/user changes forbid automatic restoration. If equality cannot be proved, retain lock, workspace, references and evidence and return blocked. A crash after canonical commit is reconciled from exact parent/tree evidence, never redispatched.

For parallel waves prove independence across dependencies, paths, interfaces, migrations, lockfiles, generated/registry/config files and singleton environments; uncertainty selects serial. Cap at 3–5 isolated workers on one recorded base. Await and inspect every result before any integration; same-path or semantic contention blocks. Integrate sequentially in dependency order, verifying each advancing canonical tree and recording exact earlier host commits for later preflight. Repeated collision disables waves without discarding unaffected results.

After all units, run the source-wide Verification Contract from the canonical absolute root, retain command/exit status/log/digest and ignored-state divergence. Failure blocks completion even if cleanup succeeds.

## Resume, fallback, receipts, cleanup

A supplied safe run ID is authoritative. Without one discover only a single unfinished plan run matching repository/bookmark/plan digest; multiple matches require selection, not a new run. Prompt runs require their disclosed ID. Resume reconciles existing evidence only: no duplicate dispatch, apply, commit, verification or shipping tail. Completed runs with all receipts are observation-only; missing receipts are blockers, not invented successes.

Lost contact remains live until authoritative terminal evidence or explicit supported termination. After authoritative failure/timeout and proven restoration plus lock release, record one atomic fallback claim before native implementation. A live job, unreconciled success, or prior claim refuses duplication. Retry keeps the run ID and prior receipts with a new attempt, fixed dependencies/base/recipient; changed recipients require new authorization. Record fallback completion with accepted revision and verification digest, then final source-wide verification.

Cleanup requires existing authorization; completion alone grants none. Stop workers, leave the target and move active harness sessions to a surviving workspace. Verify exact registered name, absolute path, run ownership, integration when required, tracked changes/conflicts and ignored/untracked content. Preserve best/archive/recovery bookmarks and copy then read back required evidence outside the target. Never remove unrelated, still-referenced, ambiguous or non-disposable content; obey harness-owned lifecycle authority.

From a surviving absolute workspace root use `jj workspace remove <verified-workspace-name>` for authorized retirement, not forget-plus-delete or Git removal. `jj workspace forget` is only for unregistering while preserving files. Verify both deregistration and directory disappearance; warnings can leave files despite exit success. On failure retain state and report the blocker; never force-delete. Bookmark deletion is a separate decision.

Return `implementation_engine_binding`, requested/actual route and intermediaries, requested/actual model and served-model receipt status, requested effort (served effort unverified unless supported evidence proves it), fallback reason, source kind/digest, run ID, unit receipts (terminal/integrated/verified/committed/cleaned separately), plan checkpoint, blockers and recovery path. Do not claim cross-model or independent coverage without evidence.

Standalone execution resumes its quality/shipping tail; `mode:return-to-caller` returns local implementation/verification receipts with `standalone_shipping_skipped: true`. Workers own neither tail.

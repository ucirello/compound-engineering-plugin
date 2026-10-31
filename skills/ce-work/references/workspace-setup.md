# Workspace setup and safe lifecycle

Resolve the absolute writable JJ workspace root by locating its `.jj` marker and confirming `(cd "$workspace_root" && jj root)`. Every JJ subprocess uses that absolute root as cwd, never `jj -R` as a cwd substitute. Repository `gh` operations run there with `GIT_DIR=$(jj git root)`, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)`.

Read `work-intake.md`, clarify actual plan ambiguity before implementation, and never edit the plan body for progress. Detect existing isolation first and reuse it unchanged, including nonconforming names and colocation. Never rename existing source or PR bookmarks. Establish a task bookmark from the verified intended base without moving the real default bookmark; use `jj bookmark list`, repository metadata, and `jj git fetch` as appropriate. Inspect local revisions beyond the remote default with an exact captured base/head revset; preserve them and report unknown remote state rather than inventing cleanliness.

Before editing, record `jj status`, `jj diff --summary`, conflicts, and a filesystem inventory of ignored and untracked paths. JJ snapshots do not protect ignored/untracked files. Preserve all pre-existing work; never stash or reset it. Commit only attributable owned paths. If a unit needs an already-dirty path, standalone mode asks once whether to include or exclude every colliding path; return-to-caller mode does not ask or edit it and returns blocked. Pass all uncommitted pre-work exclusions to shipping. Pre-existing unpushed changes force the local-only shipping path.

Use native task tracking when available; do not simulate it in chat. Tasks derive from the intake's dependency and verification contract.

## New isolation

Prefer harness-native lifecycle. If it cannot provide the required new-workspace naming/colocation, report a safe blocker rather than creating a conflicting workspace behind it. When caller-owned creation is authorized, capture the local date once and persist one `YYYYMMDD-meaningful-kebab-slug` identity before retry/resume. Derive the slug from task, PR or revision (`20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`); normalize an already-dated caller name without double prefixing. Check both `jj workspace list` registrations and destination existence under the existing workspace-local `.tmp` parent; append `-2`, `-3` on collision, never timestamp/PID/random names. Registered name and destination basename must be identical.

From the source absolute root, create only from a verified base:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify registered name/path and actual base commit before edits. An already-isolated workspace is reused, not renamed or recolocated. Native workers never mutate shared JJ repository state; the orchestrator owns snapshots/integration.

## Removal

Completion is not deletion authority. Stop all workers; leave the target; move the harness session to a surviving workspace before removing its former root. Verify exact registered name/path/run ownership, explicit disposal authority, and integrated output when required. Inspect tracked/conflicted/ignored/untracked state and preserve non-disposable data. Copy receipts and recovery evidence outside the target and read them back; retain recovery bookmarks. Unrelated, referenced, ambiguous, or non-disposable content blocks removal.

Only from the surviving absolute root use `(cd "$surviving_root" && jj workspace remove "$verified_name")`. `jj workspace forget` merely unregisters while preserving files and is not deletion. Never pair it with filesystem deletion or use force-delete fallback. Verify both registration and directory are gone. A warning or failure retains remaining state and is a blocker, not successful cleanup.

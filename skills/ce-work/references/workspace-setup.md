# Workspace Setup

Read after input triage and before editing, dispatching, moving bookmarks or committing. Establish the writable canonical absolute JJ root, exact base/head, pre-work inventory, exclusions and task state. Run every JJ command with cwd the target absolute workspace root, e.g. `(cd "$workspace_root" && jj status)`; `-R` alone is insufficient. Keep file arguments repository-relative. Repository-scoped `gh` runs from that root with `GIT_DIR` obtained there via `jj git root`.

## Detect isolation before creating anything

Confirm a writable JJ checkout with `jj root`; inspect `jj workspace list`, current root and harness ownership/session metadata. If the current checkout already is the intended verified isolated workspace, reuse it without renaming, recreating or modifying its identity. A remote writable surface must supply its absolute canonical root and native session ownership. Without a writable checkout, report blocked; do not manufacture repo changes in scratch.

Read `work-intake.md` for a plan (skip for a bounded bare prompt). Preserve the plan body; progress belongs in receipts, task tracking and revisions.

Resolve default and source bookmarks from actual remote metadata and `jj bookmark list --all-remotes`, using `jj git fetch --remote <verified-remote>` only when authorized. Do not hardcode a default revision or discard local commits. Capture exact `@` commit ID and relevant runtime history head; empty `@` above a remote commit does not erase that parent. Preserve PR/source bookmarks. Default-bookmark mutation needs explicit user authority; use a task bookmark otherwise. Unknown default/base or ambiguous push authority is a safe stop, not a reset.

Before any edit record `jj status`, `jj diff --summary`, `jj file list`, conflicts and pre-existing local commits relative to the verified remote base. Inspect filesystem untracked AND ignored content separately: JJ snapshots do not protect ignored files. Nothing pre-existing is implicitly offered for commit or publication. Do not stash, reset or discard it. Unit commits select owned paths only; pass all unoffered paths as shipping exclusions. If a unit must edit an already-dirty path, standalone asks once whether to include or exclude it; return-to-caller instead blocks before editing that path.

## New isolation when needed

Use `ce-worktree` when requested, or native isolated workers / multi-PR sessions when their contracts require separation. Prefer harness-native creation and session adoption. It must support and verify colocation, the requested identity and exact base; incompatibility stops for an authorized safe choice rather than bypassing the harness.

For a new ce-worktree identity, capture local date once as `YYYYMMDD` and persist it in run state before creation. Normalize the supplied name or task/PR/revision into a meaningful kebab-case slug, stripping an existing date prefix so there is no double date. Use `YYYYMMDD-meaningful-slug` for both the registered JJ name and destination basename under the existing absolute local `.tmp` layout. Check BOTH registered names and filesystem destinations; choose `-2`, `-3`, etc. on collisions. Reuse the persisted date/name on retries, resumes and across midnight; never use a timestamp, PID or random identity. Other new isolated workspace destinations also remain absolute and under local `.tmp`, with unique names and verified exact bases.

Where direct JJ creation is permitted by the harness lifecycle, the shell pattern is:

```sh
(cd "$surviving_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify the resulting name/path/base and positive colocation status before adopting the destination through native session tooling. Record owner/run and exact source bookmarks. Never recreate or rename an existing verified isolation to satisfy a naming preference.

## Authorized run-owned cleanup

Completion is not deletion authority. Before destructive cleanup stop workers, leave the target, and adopt a surviving harness session/root first. Verify the exact registered name/path and run ownership, no remaining references or active users, required integration and recovery/archive/best refs, plus tracked/conflicted and ignored/untracked contents. Retain anything unrelated, ambiguous or non-disposable. Copy receipts and necessary recovery evidence outside the target and read them back before proceeding. Respect harness permissions and lifecycle.

Only then, from the surviving absolute root, use `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Verify BOTH deregistration and directory disappearance. Warnings or remaining paths mean incomplete cleanup: retain/report state, never force-delete or use a Git fallback. `jj workspace forget` only unregisters and preserves files; it is not destructive cleanup. Bookmark cleanup is separate and must retain recovery/archive/best refs.

Create tasks with the actual host-native task facility when available. Derive units, order and evidence from `work-intake.md`; no fabricated platform tool names are required.

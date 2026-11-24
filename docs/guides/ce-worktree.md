# `ce-worktree`

> Put the work in an isolated, colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill rather than a core-loop step. It checks for existing isolation first, then prefers the harness's supported colocated JJ workspace tool. It only uses `jj workspace add --colocate` when the harness does not own creation and can adopt the resulting JJ workspace. Nesting isolation or creating a workspace the harness cannot see is worse than working where you already are.

There is no bundled script. Run [JJ workspace commands](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) from the relevant absolute workspace root.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers the harness tool, or creates a colocated workspace under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with its registered name, absolute path, and base reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this checkout is already a linked worktree, every form works in place rather than nesting.

```text
# New work. Detect isolation first. If none, create e.g. 20261008-account-notifications from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a worktree to an existing branch
/ce-worktree isolate feature/account-notifications

# Attach to the verified PR head in e.g. 20261008-pr-1234; preserve the PR bookmark.
/ce-worktree isolate PR 1234

# Attach at a verified commit in e.g. 20261008-review-abcdef1.
/ce-worktree isolate abcdef1
```

Do not disturb a workspace already associated with the work. Report its path and reuse it only when appropriate; a separate workspace can start from the verified revision without moving the existing bookmark.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- A behind-the-back workspace creation is invisible to the harness (Orca, Cursor, and similar). It cannot list, open, or clean up that workspace
- Keep scratch workspaces under ignored local `.tmp/` so they are not included in repository changes
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Use `jj workspace root`, workspace registrations, and harness session state to identify the current workspace. Report the verified name and absolute path and work in place when already isolated. Preserve the existing name even if it does not follow the new naming format. Verify colocation from that root with `jj git colocation status`; do not rename, recreate, or change an existing workspace to make it comply. If an attach target cannot safely be used there, report the blocker instead of moving unrelated work or nesting.

**2. Prefer the harness tool.** Where the harness owns workspace creation, use its supported colocated JJ capability. Request the required dated name and verify the registered name, basename, and colocation from the new absolute root. Adopt the workspace through the harness's supported session mechanism. If the harness cannot provide the required name or colocation, report a compatibility blocker without bypassing its lifecycle.

**3. JJ fallback.** Only when the harness does not own creation but can adopt the workspace. Verify the base and use an absolute owned destination under the caller's ignored local `.tmp/` layout, defaulting to `<source-root>/.tmp/workspace/`. Capture the local creation date once and form `YYYYMMDD-<meaningful-kebab-case-slug>` from the task, PR, or revision. Normalize caller-supplied names without double-prefixing. Use the same identity for the workspace name and destination basename. Check both registrations and destination paths; append `-2`, `-3`, etc. for collisions without overwriting anything. Preserve the selected name across retries, resumes, and midnight.

The two modes share the fallback. **New work** starts from the verified trunk. **Attach** starts from the verified bookmark, tag, commit, or PR head, without renaming existing PR/source bookmarks. For repository-scoped `gh`, run from the target workspace root with `GIT_DIR=$(jj git root)` and verify the PR's head repository, remote, bookmark, and commit.

If creation or verification fails, the skill does **not** continue in the current checkout. It reports the failure and asks whether to work here anyway or stop. It does not fall back to Git or bypass permissions.

---

## Quick Example

You are in an Orca-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies that you are already isolated, reports the existing name and path, and continues in place.

Where the harness can adopt a JJ workspace but does not own creation, the same prompt confirms `.tmp/` is ignored, verifies the base, then creates and verifies the workspace before adoption. Here `destination` is the absolute owned path ending in `20261008-fix-login`:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "20261008-fix-login" --revision "$verified_base" "$destination")
(cd "$destination" && jj git colocation status)
```

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers supply a meaningful task, PR, or revision slug. A new workspace uses the dated `YYYYMMDD-<slug>` identity, not a random label or a renamed bookmark.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated workspace from verified trunk |
| `isolate <bookmark\|tag\|commit>` | Start a workspace at that verified ref |
| `isolate PR <n>` | Start a workspace at the verified PR head; keep its bookmark |

List from a verified workspace root:

```bash
(cd "$workspace_root" && jj workspace list)
```

Completion does not authorize cleanup. Respect the harness's lifecycle and remove only an authorized, disposable, run-owned workspace. Stop its workers, verify the exact registered name and absolute path, establish integration where required, retain recovery references, and copy and read back required evidence outside the target. Inspect tracked changes, conflicts, and ignored or untracked content; the removal snapshot does not protect ignored or still-untracked files. Leave the target and move any active harness session to a surviving workspace before removal:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration and directory disappearance. If cleanup is incomplete, retain remaining state and report the blocker; do not force-delete files. Use `jj workspace forget` only to unregister while preserving files. Bookmark deletion is separate; retain all references still needed for recovery or ongoing work.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current workspace.

`ce-worktree` is the **isolation** skill, a JJ workflow tool rather than a core-loop step. The skill checks for existing isolation first, then prefers the harness's supported colocated JJ workspace capability, and only uses `jj workspace add --colocate` when neither applies. Do not nest isolation or create a workspace the harness cannot see.

There is no bundled script. Run JJ commands from the intended workspace's absolute root.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers the harness tool, else uses `jj workspace add --colocate` under the workspace's local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with its absolute path, registered name, and bookmark or exact revision reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this checkout is already a linked worktree, every form works in place rather than nesting.

```text
# New work. Detect isolation first. If none, create a dated workspace from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a worktree to an existing branch
/ce-worktree isolate feature/account-notifications

# Attach a worktree to a PR head on a local pr-1234 branch (so later commits can push back)
/ce-worktree isolate PR 1234

# Attach a worktree at an existing commit
/ce-worktree isolate abcdef1
```

Resolve the requested revision before creating isolation. Report any existing relevant workspace rather than modifying it or silently reusing one the run does not own.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating from inside an isolated workspace can nest isolation unnecessarily
- Bypassing a harness-owned lifecycle can leave the harness unable to open or clean up the workspace
- Confirm the local `.tmp/` parent is ignored so isolation does not become part of the source working copy
- Random names hide what a workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Compare the absolute path from `jj workspace root` to the registered workspace paths and respect the harness's existing isolation. Verify with `jj git colocation status` from the workspace's absolute root. Report and reuse the verified existing name; do not rename, recreate, or silently alter the workspace to enforce naming or colocation. If a requirement is unmet, report the blocker and use the safe decision path.

**2. Prefer the harness tool.** Request supported colocated JJ creation and the required name; verify the result without bypassing the harness lifecycle. Unsupported naming or colocation is a compatibility blocker, not permission to create a noncompliant workspace.

**3. Native JJ creation.** Only when neither applies. Verify the selected base and the ignored local `.tmp/workspace/` parent. Capture the local date once. Normalize the task, PR, revision, or caller-supplied name into `YYYYMMDD-<meaningful-kebab-case-slug>` without double-prefixing. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Use the same identity as the registered workspace name and absolute destination basename; check both for collisions and use `-2`, `-3`, etc. without overwriting. Preserve the selected name over retries, resumes, and midnight boundaries.

**New work** starts from verified trunk. **Attach** starts from the exact verified bookmark, tag, commit, or PR head. The dated workspace identity does not rename existing PR or source bookmarks.

If workspace creation or adoption fails on sandbox or permissions, the skill does **not** continue in the current workspace. It reports the failure and asks whether to work here anyway or stop.

---

## Quick Example

You are already in verified harness-provided JJ isolation. `ce-work` offers isolation. `/ce-worktree` reports the existing workspace and continues in place.

With no harness-provided isolation, verify the base and run:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Adopt the workspace through the harness's supported session-move operation when applicable.

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

On-demand isolation. Callers pass a meaningful task, PR, or revision slug for the dated workspace name, not a random label.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated workspace from verified trunk, with a separate work bookmark |
| `isolate <bookmark\|tag\|commit>` | Isolate work at that exact revision |
| `isolate PR <n>` | Isolate work at that exact PR head, preserving an existing local `pr-<n>` work bookmark |

Remove only with cleanup authorization and respect harness lifecycle ownership. Stop workers, leave the target, and move any active harness session to a surviving workspace before removal. Verify exact name, absolute path, and run ownership; prove integration when required, preserve recovery references, and copy and read back required evidence outside the target. Inspect tracked changes, conflicts, and ignored or untracked files; the removal snapshot does not protect ignored or still-untracked files. Leave unrelated, ambiguous, referenced, or non-disposable content alone.

List and remove from the surviving workspace with JJ:

```bash
(cd "$surviving_workspace_root" && jj workspace list)
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify deregistration and directory disappearance after removal; on incomplete cleanup retain remaining state and report the blocker, without force deletion or a fallback. Use `jj workspace forget` only to unregister while preserving files. Bookmark deletion is separate; preserve any bookmark still needed for integration or recovery.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

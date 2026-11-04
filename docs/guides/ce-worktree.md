# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already create isolation at session start. The skill checks that first, then prefers the harness's supported colocated JJ workspace capability. Native JJ creation is used only where the harness ownership contract permits it. Nesting isolation or creating a workspace the harness cannot see is worse than working where you already are.

There is no bundled script. The agent runs JJ from the target workspace's absolute root and uses supported harness session adoption. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers the supported harness tool, otherwise creates a colocated JJ workspace under local `.tmp/` when permitted |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name and source bookmark reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this checkout is already verified isolation, reuse its existing name and lifecycle rather than nesting or enforcing a new naming format.

```text
# New work. Detect isolation first. If none, create a dated JJ workspace under local .tmp/.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a workspace to an existing bookmark
/ce-worktree isolate feature/account-notifications

# Attach a workspace to a verified PR head; preserve its source bookmark and push target
/ce-worktree isolate PR 1234

# Attach a workspace at an existing commit
/ce-worktree isolate abcdef1
```

Resolve the exact requested revision before creation, preserving existing PR/source bookmarks. An already registered destination is not overwritten; reuse verified appropriate isolation or choose a collision-free new identity under the owning harness's rules.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating redundant isolation loses track of which workspace owns the work
- Behind-the-back workspace creation is invisible to a harness that owns the session lifecycle
- Local `.tmp/` destinations must be ignored so scratch content does not enter a change
- Random labels hide what the workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute workspace root, inspect `jj workspace list` there, and verify the harness's isolation and ownership state. Reuse existing verified isolation under its existing name, even if it is not dated or colocated. Do not rename, recreate or silently modify it to enforce new-creation requirements. Attach mode verifies the requested target and preserves unrelated work before any authorized movement.

**2. Prefer the harness tool.** Use its supported colocated JJ capability when available, request the required dated name, and verify both name and colocation. Unsupported naming or colocation is a compatibility blocker through the safe decision path, not permission to bypass ownership or use a Git-only fallback. Adopt the created workspace into the active harness session.

**3. Native JJ creation.** Only when existing isolation and a supported harness primitive do not apply and native creation is permitted. Capture the local creation date once; derive a meaningful kebab-case slug from the task, PR, or revision. Normalize caller-supplied names without double-prefixing. Use `YYYYMMDD-<slug>` for both the JJ registered name and destination basename under the existing absolute local `.tmp/` parent layout. Check registrations and paths for collisions; append `-2`, `-3`, etc. without overwriting. Persist the selected identity over retries, resumes and midnight boundaries; do not substitute timestamps, PIDs or random names.

The two modes share creation. **New work** resolves the repository's actual default/trunk bookmark to a verified exact base. **Attach** resolves the requested bookmark, tag, commit or PR head exactly, including fork repository and push tracking. Preserve PR/source bookmarks unchanged. Repository-scoped `gh` receives `GIT_DIR=$(jj git root)` from the source absolute root. Never substitute a different ref on failure.

Create and verify explicitly:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

If creation, naming, colocation or adoption fails, preserve state and use the existing safe decision path. Never silently continue in the current checkout, reset, bypass permissions or fall back to Git.

---

## Quick Example

You are in a harness-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the existing registration and harness ownership, reports its actual path/name and continues in place without renaming it.

For fresh creation on October 8, 2026, names include `20261008-fix-email-validation`, `20261008-pr-214`, and `20261008-review-efcb657`. A supplied `20261008-pr-214` is not prefixed again. A collision yields `20261008-pr-214-2`, with that exact registered name also the destination basename. The captured date and selected identity survive resumption after midnight. Creation uses the verified base and explicit `--colocate`, verifies colocation and adopts the harness session before work.

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

On-demand isolation. Callers pass task/PR/revision identity or a normalized dated workspace name, not a random label. Workspace naming never renames PR/source bookmarks.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated workspace from verified trunk |
| `isolate <bookmark\|tag\|commit>` | Create dated isolation at that verified exact ref |
| `isolate PR <n>` | Create dated isolation at the exact PR head, preserving source/push identity |

List and switch use the registered JJ workspace and its verified absolute path:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_absolute_destination"
```

Completion alone does not authorize deleting a user's workspace. For separately authorized run-owned cleanup, stop workers, leave the target and move the active harness session to a surviving workspace first. Verify the exact registered name, absolute path and run ownership; prove required integration, retain recovery references, and copy/read back required evidence outside the target. Inspect tracked changes, conflicts and ignored/untracked content: the removal snapshot does not protect ignored or untracked files. Preserve unrelated, ambiguously owned, still-referenced and non-disposable content, and respect harness lifecycle authority.

From the surviving workspace's absolute root run `(cd "$surviving_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance; warnings can mean deletion is incomplete despite success. On failure retain remaining state and report the blocker, never force-delete or use Git cleanup. `jj workspace forget` is reserved for unregister-only operations that preserve files. Bookmark deletion is separate; retain best/archive/recovery bookmarks and references still needed.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

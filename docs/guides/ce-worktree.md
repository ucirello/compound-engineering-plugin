# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing existing work.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already create isolation at session start, so the common case is that you are already isolated. The skill checks that first, then prefers the harness's supported colocated JJ workspace capability, and only uses inline JJ creation when the harness does not own that lifecycle. Nesting a workspace inside another one, or creating one the harness cannot see, is worse than working where you already are. Unsupported colocation or required new-workspace naming is a compatibility blocker, not permission to bypass harness ownership.

There is no bundled script. The agent runs inline JJ from the target workspace's absolute root, respecting the supported workspace and session capabilities of Claude Code, Codex, Gemini, OpenCode, and Pi.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers supported harness-owned colocated JJ creation, else `jj workspace add --colocate` under local `.tmp/workspaces/<dated-identity>` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated JJ workspace, with absolute path, registered name, and source bookmark reported |
| Skip when | Single-task work that fits on a bookmark in the current workspace |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this workspace is already isolated, every form follows the existing-isolation safe path rather than nesting or renaming it.

```text
# New work. Detect isolation first. If none, create a dated workspace from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report existing path and name, stay here
/ce-worktree

# Attach a workspace at an existing bookmark; do not rename the bookmark
/ce-worktree isolate feature/account-notifications

# Attach a workspace at the verified PR head; preserve its source bookmark and push identity
/ce-worktree isolate PR 1234

# Attach a workspace at a verified existing revision
/ce-worktree isolate abcdef1
```

Inspect registered JJ workspaces and absolute destinations before creation. Reuse suitable existing isolation under its verified existing name, even if undated or non-colocated; never rename, recreate, or silently modify it to enforce new-creation requirements. Ambiguous ownership or an incompatible requested target follows the skill's safe decision path without discarding work.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative destinations can create isolation in a directory tree you are not using
- Behind-the-back creation can bypass harness ownership and session lifecycle
- If local `.tmp/` is not ignored, nested artifacts can enter the source snapshot
- Random workspace labels hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list` and harness ownership, and verify the current registered name/path. Already isolated means report that existing identity and work in place. In attach mode, verify the exact requested target and preserve unrelated tracked, conflicted, ignored, and untracked work; do not reset or guess a target.

**2. Prefer the harness tool.** Use its supported colocated JJ workspace capability where available, request the required dated identity for newly created workspaces, and verify both name and colocation. Respect its ownership, cleanup authority, and session-adoption contract. Unsupported naming or colocation is a safe compatibility blocker, not a Git-only fallback.

**3. Inline JJ creation.** Only when neither applies. From the source workspace's absolute root, verify ignored local `.tmp/` storage and the exact base revision, fetching through JJ when required. Capture the local creation date once. Derive a meaningful kebab-case slug from the task, PR, or revision; normalize a caller-supplied name without double-prefixing. Use `YYYYMMDD-<slug>` as both registered workspace name and destination basename. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Preserve that selected identity across retries, resumes, and midnight boundaries. Check registrations and destinations; collisions append `-2`, `-3`, etc., never overwrite. Timestamps, PIDs, and random labels are not naming substitutes.

The two modes share creation. **New work** uses a verified default-branch revision. **Attach** resolves the requested bookmark, tag, revision, or PR to one verified commit. For a PR, verify the head repository, bookmark, remote, commit, and push authority; keep existing PR/source bookmarks unchanged. Scope GitHub queries from the target absolute root with `GIT_DIR=$(jj git root)`.

If creation fails on sandbox, permissions, or compatibility, the skill does **not** silently continue in the current workspace. Report the blocker through the existing safe decision path; do not retry denied operations or use a Git-only workaround.

---

## Quick Example

You are in harness-managed isolation created at session start. `ce-work` offers isolation. `/ce-worktree` verifies its existing registered identity and ownership, reports its absolute path and name, and continues in place without renaming or recreating it.

In a plain terminal workspace with no owning native tool, the same prompt verifies the base, name and destination, then creates explicit colocation:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$dated_identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Adopt the absolute destination through the harness's supported session move capability; when unavailable, report the path and compatibility boundary rather than assuming a shell `cd` moves the harness session.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a bookmark in the current workspace
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent already knows `jj workspace add --colocate`? The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass a meaningful task/PR/revision slug or normalized dated identity, not a random label. The skill selects one dated workspace/destination identity without changing source bookmarks.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated JJ workspace from verified trunk |
| `isolate <bookmark\|tag\|revision>` | Create dated isolation at that verified revision |
| `isolate PR <n>` | Create dated isolation at the verified PR head, preserving source bookmark identity |

List and inspect from an absolute workspace root. Removal is a separate authorized lifecycle operation:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$absolute_destination" && jj status)
```

Completion alone does not authorize deleting a user's workspace. Respect harness-owned lifecycle authority. For authorized retirement of run-owned disposable isolation: stop workers first; verify the exact registered name, absolute path, and run ownership; prove integration where required; preserve recovery/best/archive references and copy/read back required evidence outside the target. Inspect tracked changes, conflicts, and ignored/untracked content. Removal snapshots working-copy state, but ignored files and files left untracked are not protected. Never remove unrelated, ambiguously owned, still-referenced, or non-disposable content.

Leave the target and move any active harness session to a surviving workspace before removal:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
test ! -e "$absolute_destination"
```

Verify both deregistration and directory disappearance: directory-deletion failures may only warn. On failure or incomplete cleanup, retain remaining state and report the blocker; never force-delete or fall back to Git removal. Use `jj workspace forget` only to unregister while preserving files. JJ manages colocated Git metadata; do not run separate Git cleanup. Keep bookmark deletion separately authorized and preserve all references still needed.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

# `ce-worktree`

> Put the work in an isolated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already create a workspace at session start, so the common case is that you are already isolated. The skill checks that first, then prefers a compatible harness-native workspace tool, and only uses native `jj workspace add --colocate` when no native tool exists and the harness can adopt the result. Never nest workspaces or create one the harness cannot see.

There is no bundled script. The agent runs inline JJ with its working directory set to the target workspace's absolute root, using the latest JJ interface. Never invoke the Git executable. Harness ownership and session-adoption capabilities determine whether creation is supported.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Makes sure isolation exists. Detects an existing workspace, prefers a compatible harness tool, else `jj workspace add --colocate` under local `.tmp/workspaces/<dated-identity>` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name, revision, and applicable bookmarks reported; otherwise a blocker |
| Skip when | Single-task work that fits in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **isolate an existing ref**. If this checkout is already isolated, every form works in place rather than nesting; alignment to a requested ref still requires a clean workspace, exact target verification, and authorization.

```text
# New work. Detect isolation first. If none, create .tmp/workspaces/20261008-account-notifications from verified trunk (illustrative local date).
/ce-worktree for the account-notifications feature

# Already isolated: report existing name, absolute path, revision, and bookmarks; stay here
/ce-worktree

# Isolate an existing bookmark without renaming it
/ce-worktree isolate feature/account-notifications

# Isolate the exact PR head; workspace identity 20261008-pr-1234 is separate from its push bookmark
/ce-worktree isolate PR 1234

# Isolate an existing revision; workspace identity 20261008-review-abcdef1
/ce-worktree isolate abcdef1
```

JJ permits multiple workspaces based on the same revision. Do not impose Git's one-branch-one-worktree restriction. Existing PR/source bookmarks and fork-safe push targets remain unchanged; the dated workspace identity is not a replacement bookmark.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating a workspace without resolving the source's absolute root can put work in the wrong directory tree
- A behind-the-back workspace is invisible to the harness. It cannot reliably list, open, or clean up that tree
- If local `.tmp/` is not ignored, workspace files and temporary evidence can enter repository status
- Random names hide what the workspace is for; new workspaces need a stable dated task identity

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root`, inspect `jj workspace list` and the harness's ownership/session information from that absolute root. Directory names or colocated metadata alone do not prove isolation. Already isolated means report the existing name, absolute path, revision, and bookmarks and work in place, even if its name is not dated or it is not colocated. Do not rename, recreate, or modify existing metadata to enforce new-creation rules. In existing-ref mode, an empty `@` directly above the exact target is already aligned. Only align a clean workspace when authorized; preserve unrelated tracked, ignored, untracked, and conflicted work. Uncertain isolation or unsafe alignment is a blocker, not permission to reset or nest.

**2. Prefer the harness tool.** Use its supported colocated JJ capability, retaining harness ownership and lifecycle authority. Request the exact verified base and the dated identity described below. From the result's absolute root, verify its registered name, destination basename, revision, and `jj git colocation status`, then adopt it through the supported session-move capability. Unsupported colocation or required naming is a compatibility blocker, not permission for a Git-only fallback or a second workspace behind the harness's back.

**3. Native JJ creation.** Only when no native workspace tool exists, no isolation already exists, and the harness can adopt an externally created workspace. Keep destinations and all temporary files under the source root's local `.tmp/`, for example `.tmp/workspaces/`. Inspect ignore rules locally and ensure the root `.gitignore` covers `.tmp/` before creation; do not use Git or global temporary storage.

Capture the local creation date once as `YYYYMMDD` and derive a meaningful kebab-case slug from the task, PR, or revision: `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing. Use one identity for both the registered JJ name and destination basename. Check registrations and filesystem destinations, including dangling symlinks; append `-2`, `-3`, etc. on collisions with unrelated state, never overwrite or use timestamps, PIDs, or random identifiers. Record the selected identity/date outside the destination before creation. Retries, resumes, and midnight boundaries retain it; first check whether creation already succeeded and can safely resume. Unresolved partial state is a blocker, not a reason to silently pick a new name.

Both modes resolve an exact verified base commit. **New work** inspects configured remote/default bookmarks and repository instructions; refresh the selected bookmark with `jj git fetch --remote <verified-remote> --bookmark <verified-bookmark>` when applicable. Refresh failure is non-fatal only with a verified local base, and must be disclosed. **Existing ref** resolves the requested bookmark, tag, revision, or PR exactly, never substituting another ref. For a PR, use repository-scoped `gh` with `GIT_DIR=$(jj git root)` from the source root to verify the head repository, remote, bookmark, and commit, then fetch and verify that exact head with JJ. Preserve source bookmarks and fork-safe push destinations.

If creation, colocation verification, or harness-session adoption fails, isolation is not established. Preserve partial state and report the blocker. Do **not** continue in the current checkout or bypass a permission denial: ask whether to work there anyway or stop, using the host's available blocking question capability (or numbered chat options when unavailable), then wait for the answer.

---

## Quick Example

You are in a harness-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies its registration and harness ownership. You are already isolated. It reports the existing name, absolute path, revision, and bookmarks and continues in place without changing its name or metadata.

In a checkout with no native tool but supported harness adoption, the same "new work" prompt confirms `.tmp/` is ignored, records a collision-free identity such as `20261008-login`, and resolves the verified base. With `workspace_root` and `absolute_destination` both absolute and the destination basename equal to `workspace_name`:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify registration, revision, and name/basename equality, then move the active harness session to the destination through its supported capability (for example, OpenCode `session_move`). A shell `cd` alone is not session adoption. Every JJ command must run from the target workspace's absolute root; `jj -R` alone does not set its working directory.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent already knows JJ workspace creation? The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers supply a meaningful task, PR, or revision slug, normalized to `YYYYMMDD-<meaningful-kebab-case-slug>` for new workspaces. The selected dated identity is stable across retries and matches the destination basename; existing isolation names and PR/source bookmarks stay unchanged.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated JJ workspace from verified trunk |
| `isolate <bookmark\|tag\|revision>` | Create a dated JJ workspace based on that exact ref |
| `isolate PR <n>` | Create a dated JJ workspace based on the verified PR head; preserve its source bookmark and push target |

List and inspect using JJ from the workspace's absolute root. Switching active work also requires supported harness-session adoption:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj workspace root)
```

Completion alone does not authorize cleanup. Respect the user's cleanup authorization and harness-owned lifecycle authority. Before retiring a run-owned workspace:

1. Stop its workers; verify the exact registered name, absolute path, and run ownership. Never remove unrelated, ambiguously owned, still-referenced, or non-disposable content.
2. From its absolute root, inspect tracked changes, conflicts, and ignored/untracked files. Prove integration when required by the caller. Preserve recovery references; copy required evidence outside the target directory and read it back. Removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot.
3. Leave the target and move any active harness sessions to a surviving workspace through the supported session-move capability. Subject to harness lifecycle authorization, remove it from that surviving workspace's absolute root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
   ```

4. Verify both workspace deregistration and directory disappearance. Success alone is insufficient because directory-deletion failures can be warnings. On failure or incomplete cleanup, retain remaining state and report the blocker; never force-delete or fall back to Git removal. JJ manages colocated metadata, with no separate Git cleanup. Keep bookmark deletion separate and preserve best/archive/recovery bookmarks and references still needed.

Use `jj workspace forget <verified-workspace-name>` only for an authorized unregister-only operation that preserves files, never before directory deletion. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [Git migration guide](https://docs.jj-vcs.dev/latest/git-experts/).

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

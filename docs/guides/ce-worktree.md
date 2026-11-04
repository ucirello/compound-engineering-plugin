# `ce-worktree`

> Put the work in an isolated, colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already provide isolation at session start. Detect that first and reuse its verified existing name and path, even if they do not match new-creation naming or colocation requirements; do not rename, recreate, or modify existing isolation merely to enforce those requirements. Prefer the harness's supported colocated JJ capability and lifecycle. Nesting isolation or creating a workspace the harness cannot adopt is worse than working where you already are.

There is no bundled script. The agent runs native JJ from the applicable absolute workspace root. Harness-specific creation and session adoption must honor ownership and lifecycle contracts; unsupported naming or colocation is a compatibility blocker, not permission to bypass them.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation first; otherwise creates and verifies a colocated JJ workspace under local `.tmp/` with supported harness adoption |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name, revision, bookmarks, and session adoption reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means an existing bookmark, PR, or revision. If already isolated, work in place rather than nesting; a requested revision transition must preserve unrelated work and existing ownership.

```text
# New work. Detect isolation first; otherwise use a verified base and dated local workspace.
/ce-worktree for the account-notifications feature

# Already isolated: report path, registered name, revision, and bookmarks; stay here
/ce-worktree

# Create isolation at an existing bookmark, preserving that bookmark
/ce-worktree isolate feature/account-notifications

# Isolate the verified PR head; preserve its source bookmark and push destination
/ce-worktree isolate PR 1234

# Isolate an existing verified revision
/ce-worktree isolate abcdef1
```

JJ workspaces can share revisions, but changes and bookmarks still require ownership checks. Reuse verified existing isolation without repurposing another session's workspace. A workspace identity never renames an existing PR/source bookmark.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative destinations can resolve against the wrong workspace
- A behind-the-back workspace can be invisible to the harness's session and cleanup lifecycle
- Local `.tmp/` must be ignored so nested workspace data is not recorded
- Random labels hide the task and are not valid new-workspace identities

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root`, inspect `jj workspace list`, `jj status`, and harness/session metadata from the absolute root. Identify registration, isolation, and ownership rather than inferring them from directory spelling. Reuse existing isolation under its existing name; ambiguous ownership or a non-JJ checkout is a safe compatibility blocker, not permission to initialize, reset, or convert it.

**2. Prefer the harness tool.** Request its supported colocated JJ creation capability with the exact selected date-prefixed name, absolute destination, and verified base. Verify the result and adopt/move the active session through the supported interface. If those guarantees are unavailable, stop through the existing safe decision path; no Git-only fallback or silent rename is allowed.

**3. Native JJ creation.** Only if no native creator exists and supported session adoption is available. Verify the exact base from the actual task/default remote rather than assuming `main` or `origin`; use authorized `jj git fetch` where needed and disclose stale/offline local bases. Ensure local `.tmp/` is ignored. Capture the local date once and persist one `YYYYMMDD-meaningful-kebab-case-slug` identity in a run receipt outside the destination. Derive the slug from the task, PR, or revision; normalize caller-supplied dated names without double-prefixing. Keep that identity across retries, resumes, and midnight. Use it for both the registered name and destination basename, preserving the local `.tmp/` parent layout. Check registrations and existing paths; append `-2`, `-3`, etc. without overwriting unrelated state.

Examples: `20261008-fix-email-validation`, `20261008-pr-214`, and `20261008-review-efcb657`. Fresh work, PRs, revisions, and caller-selected names all follow this one identity rule. Preserve existing PR/source bookmarks and verify repository, remote, bookmark, and exact PR head before fetching or selecting a revision. Repository-scoped `gh` uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; never use checkout helpers that invoke Git.

From the source workspace's absolute root, create and verify explicitly:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify the exact registration/path/base relationship, status/conflicts, unchanged source bookmarks, and harness-session adoption. Permission, compatibility, or verification failures preserve partial state and report a blocker; never work in the primary checkout or retry a permission workaround without authorization.

---

## Quick Example

You are in harness-managed isolation created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the registration, absolute root, and session ownership. It reports the existing name and bookmarks and continues in place, without renaming or recreating it.

With supported adoption but no native creator, the same prompt persists an identity such as `20261008-fix-login`, verifies the base and collision-free absolute `.tmp/` destination, runs the explicit colocated JJ creation above, verifies colocation, and adopts the session before proceeding.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all? The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers supply task/PR/revision context or a meaningful name; new names are normalized to the stable dated identity above, not used to rename source bookmarks.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: dated workspace from a verified base |
| `isolate <bookmark\|tag\|revision>` | Dated workspace at that exact ref; source bookmarks unchanged |
| `isolate PR <n>` | Dated `YYYYMMDD-pr-<n>` workspace at the verified PR head |

List and navigate through native JJ and absolute paths:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_absolute_destination"
```

Completion alone does not authorize cleanup. For separately authorized run-owned disposable workspace retirement: stop its workers, leave the target, move active harness sessions to a surviving workspace, and verify exact registered name, absolute path, and run ownership. Prove integration where required and preserve recovery/best/archive references. Copy required evidence and receipts outside the target and read them back. Inspect tracked changes, conflicts, and ignored/untracked content: removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot. Never remove unrelated, ambiguously owned, still-referenced, or non-disposable content. Respect harness-owned lifecycle authority.

From the surviving workspace's absolute root use `(cd "$surviving_root" && jj workspace remove "$verified_workspace_name")`. JJ owns colocated metadata cleanup; never perform separate Git cleanup or directory deletion. Verify both deregistration and directory disappearance, since deletion failure may be a warning. Incomplete cleanup retains remaining state and reports the blocker, never force-deletes. Keep bookmark deletion separate and preserve needed recovery references. Reserve `jj workspace forget` for an explicit unregister-only request that preserves files, verifying both deregistration and retained files. See [JJ workspace documentation](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already provide isolation at session start. Detect that first, then prefer the harness's supported colocated JJ workspace capability and lifecycle. Only create a native JJ workspace when neither existing isolation nor a suitable harness capability applies. Do not nest isolation or create a workspace the harness cannot adopt.

There is no bundled script. Run JJ from the target workspace's absolute root. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers a compatible harness tool, else `jj workspace add --colocate` under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new colocated JJ workspace, with absolute path, workspace name and source bookmark reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this checkout already has verified isolation, every form works in place rather than nesting, preserving unrelated work.

```text
# New work. Detect isolation first. If none, create a dated workspace from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a worktree to an existing branch
/ce-worktree isolate feature/account-notifications

# Attach a workspace to the verified PR head, preserving its source bookmark for pushback
/ce-worktree isolate PR 1234

# Attach a worktree at an existing commit
/ce-worktree isolate abcdef1
```

Resolve the exact requested revision and inspect existing workspace registrations before creating anything. Reuse verified existing isolation under its existing name, even if it is undated or not colocated. Do not rename, recreate or silently modify an existing workspace to enforce new-creation requirements. Preserve PR/source bookmarks unchanged.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative workspace destinations can resolve into a directory tree you are not using
- Behind-the-back workspace creation may be invisible to the harness, which cannot list, open or clean it up
- If local `.tmp/` is not ignored, workspace artifacts can enter the source change
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root`, inspect `jj workspace list` and the harness's ownership information from that absolute root. Existing verified isolation means report its name/path and work in place. For attach mode, resolve the exact requested head and preserve unrelated work; dirty/conflicted state or ambiguous targets require the safe decision path, not a reset.

**2. Prefer the harness tool.** Use its supported colocated JJ workspace capability, requesting and verifying the dated identity below for a new workspace. Verify colocation from the created absolute root with `jj git colocation status`. If naming, colocation or session adoption is unsupported, report a compatibility blocker through the safe decision path; do not bypass harness ownership or fall back to Git.

**3. Native JJ creation.** Only when neither applies and the harness explicitly supports adopting a manually created JJ workspace. Ensure local `.tmp/` storage is ignored. Resolve and verify the exact base revision before creation; never silently substitute another ref. Capture the local date once. Derive a meaningful kebab-case slug from the task, PR or revision, normalizing caller-supplied names without double-prefixing. New identities use `YYYYMMDD-<slug>`, for example `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Use that same identity for the registered workspace name and destination basename under the existing absolute local `.tmp/` parent layout. Check registrations and destinations for collisions and append `-2`, `-3`, etc.; never overwrite. Preserve the chosen identity across retries, resumes and midnight. Do not substitute timestamps, PIDs or random identifiers.

The two modes share native creation. **New work** starts from the verified default bookmark. **Attach** starts from the exact verified bookmark, tag, commit or PR head, preserving its repository, remote and pushback mapping. For repository-scoped GitHub calls, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; do not invoke the Git executable.

If creation fails on sandbox or permissions, do not silently continue in the current checkout. Report the failure and follow the existing safe decision path: work here only when authorized, otherwise stop.

---

## Quick Example

You are in a harness-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the existing registration and harness ownership, reports its existing path and name, and continues in place without renaming it.

In a plain terminal workspace with no suitable harness tool, resolve the verified base and absolute owned destination, then run:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$dated_identity" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Adopt the new absolute root in the active harness session before executing work there.

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

On-demand isolation. Callers pass a task, PR or revision-derived meaningful name; normalize it to the stable dated identity above for new creation, without changing source bookmarks.

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
| `isolate <bookmark\|tag\|commit>` | Create a dated workspace at that exact verified revision, preserving source bookmarks |
| `isolate PR <n>` | Create a dated workspace at that exact verified PR head, preserving the PR/source bookmark and push mapping |

List and inspect from an absolute surviving workspace root:

```bash
(cd "$surviving_workspace_root" && jj workspace list)
(cd "$workspace_root" && jj status)
```

Completion alone does not authorize cleanup. Respect user authorization and harness-owned lifecycle authority. Stop workers first, leave the target directory and move any active harness session to a surviving workspace. Verify the exact registered name, absolute path and run ownership. Prove integration when required, preserve recovery references, and copy/read back required evidence outside the target. Inspect tracked changes, conflicts and ignored/untracked content: the removal snapshot does not protect ignored files or files left untracked. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

When authorized to retire a run-owned workspace and delete its files, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. JJ owns colocated metadata cleanup; do not run a separate Git cleanup. Verify both deregistration and directory disappearance, since deletion failures can be warnings. On failure or incomplete cleanup, retain remaining state and report the blocker; never force-delete or fall back to Git. Use `jj workspace forget` only for unregistering while preserving files. Bookmark deletion is separate; preserve best/archive/recovery bookmarks and any still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

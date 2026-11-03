# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing existing work.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Many harnesses already create isolation at session start. Detect and reuse that verified isolation first, under its existing name, without renaming or recreating it to enforce new naming or colocation rules. Otherwise prefer the harness's supported colocated JJ workspace capability, respecting its ownership and lifecycle. A harness that cannot honor required colocation or the requested new-workspace name is a compatibility blocker, not permission to bypass it.

There is no bundled script. Run native JJ from the absolute target workspace root. OpenCode sessions must adopt new isolation through the supported session-move interface. Never directly invoke Git. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers harness-owned colocated JJ creation, otherwise explicitly creates a colocated workspace under the source workspace's absolute `.tmp/` layout |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name, and verified revision reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused rather than nested; changing its revision still requires the skill's clean-state and authority checks.

```text
# New work: detect isolation first; new identity e.g. 20261008-account-notifications.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Isolate the verified existing bookmark without renaming it
/ce-worktree isolate feature/account-notifications

# Isolate the verified PR head; workspace e.g. 20261008-pr-1234, source bookmark unchanged
/ce-worktree isolate PR 1234

# Isolate the verified revision; workspace e.g. 20261008-review-abcdef1
/ce-worktree isolate abcdef1
```

Inspect registered workspaces before creating anything. Report and reuse an appropriate existing owned workspace only under its lifecycle contract; do not overwrite registrations or destinations. Workspace identity is separate from PR/source bookmarks, which remain unchanged.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Repository selection alone does not set command cwd; relative paths can resolve against the wrong workspace
- Behind-the-back creation can be invisible to the harness and violate its lifecycle contract
- Workspace storage must remain under ignored local `.tmp/`, outside the source's tracked content
- Random labels hide purpose and are not compliant new `ce-worktree` identities

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list`, and use harness ownership evidence. Report and reuse verified isolation under its existing name. Do not rename, recreate, or silently alter it just to satisfy new-creation rules. Preserve unrelated tracked, conflicted, ignored, and untracked work; uncertain isolation or target identity follows the safe decision path.

**2. Prefer the harness tool.** Request its supported colocated JJ capability and the exact required date-prefixed name. Verify its resulting name, absolute path, revision, and colocation without bypassing ownership. Unsupported naming or colocation blocks creation; reuse of existing isolation does not require changing its name.

**3. Native JJ creation.** Only when no existing isolation or harness-owned lifecycle applies. Verify the intended base to one exact commit, retaining the configured remote/ref and reporting unavailable data rather than substituting a default. Keep the existing local `.tmp/` parent layout, ensure `.tmp/` is ignored, and choose an absolute owned destination.

Both modes use one persisted identity for the JJ workspace name and destination basename: `YYYYMMDD-<meaningful-kebab-case-slug>`. Capture the local creation date once before selection; derive the slug from task, PR, or revision. Normalize caller-supplied names without double-prefixing an already dated identity. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Check both registered names and filesystem entries; append `-2`, `-3`, etc. on collisions without overwriting. Persist and reuse the selected date/name across retries, resumes, and midnight; never substitute timestamps, PIDs, or randomness. PR/source bookmarks remain unchanged. Resolve fork/head authority explicitly; repository-scoped `gh` uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, never a Git-backed checkout helper.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify the registered name, matching destination basename, and exact base before edits, then adopt the destination in the harness session.

If creation or verification fails, do **not** continue in the current checkout or evade permissions. Report the blocker through the existing safe decision path; unattended runs stop rather than inventing consent.

---

## Quick Example

You are in harness-managed isolation created at session start. `ce-work` offers isolation. `/ce-worktree` verifies its registered name/path and ownership, reports the existing identity, and continues without renaming it.

In a plain terminal with no owning harness lifecycle, new work resolves the verified base, selects a stable name such as `20261008-fix-login`, and creates it explicitly with `jj workspace add --colocate` under the absolute local `.tmp/` parent. It verifies colocation and adopts the new root before work.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

The skill is the order: detect first, defer to the harness, verify colocation and identity, and do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass meaningful task/PR/revision context or a normalized date-prefixed workspace name, not a random label or a new name for an existing source bookmark.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated workspace at the verified base |
| `isolate <bookmark\|tag\|commit>` | Isolate that exact verified ref; preserve its identity |
| `isolate PR <n>` | Isolate the verified PR head; preserve source bookmarks and push authority |

List and enter native JJ workspaces from absolute roots:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_existing_workspace_root"
```

Completion alone does not authorize cleanup. Respect harness-owned lifecycle and existing cleanup authority. Stop workers first; leave the target and move every active harness session to a surviving absolute workspace. Verify the exact registered name/path and run ownership, prove integration where required, retain recovery references, and copy/read back required evidence outside the target. Inspect tracked changes, conflicts, ignored and untracked content: removal snapshots do not protect ignored or untracked files. Never remove unrelated, ambiguous, referenced, or non-disposable content.

Only after those safeguards and authorization, run `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Verify **both** deregistration and directory disappearance; a successful exit may still contain deletion warnings. On failure retain remaining state and report the blocker; never force-delete, use Git removal, or combine `workspace forget` with directory deletion. `jj workspace forget` is reserved for explicitly unregistering while preserving files. JJ owns colocated metadata cleanup. Bookmark deletion is separate: preserve best/archive/recovery bookmarks and any still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

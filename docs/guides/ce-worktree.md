# `ce-worktree`

> Put the work in an isolated, colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Most coding harnesses already create isolation at session start. Detect that first and reuse its verified existing name and path unchanged. Otherwise use the harness's supported colocated JJ lifecycle, including registration and session adoption. Unsupported naming, colocation or lifecycle is a compatibility blocker, not permission to create invisible state or use a Git-only fallback.

There is no bundled script. The agent runs native JJ from the target workspace's absolute root as the actual command working directory, preserving the host's lifecycle authority. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation first; otherwise explicitly creates and verifies a colocated JJ workspace within the supported harness lifecycle |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a verified adopted workspace, with absolute path, registered name, revision and source bookmarks reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused rather than nested; changing its revision still requires authority and preservation of unrelated work.

```text
# New work. Detect isolation first; otherwise use a verified trunk revision.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): preserve its name/path, stay here
/ce-worktree

# Isolate an exact existing bookmark without renaming it
/ce-worktree isolate feature/account-notifications

# Isolate an exact verified PR head, preserving its source/push bookmarks
/ce-worktree isolate PR 1234

# Attach a worktree at an existing commit
/ce-worktree isolate abcdef1
```

If another workspace already serves the source, report its verified path and offer reuse rather than forcing takeover. A dated workspace identity never renames PR or source bookmarks.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating another workspace without checking existing isolation can nest or duplicate state
- Behind-the-back creation can be invisible to the harness (Orca, Cursor, and similar), preventing listing, navigation and lifecycle cleanup
- If the local `.tmp/` parent is not ignored, nested workspace content may be accidentally tracked
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root, JJ workspace registrations and native harness inventory/session metadata. Compare resolved paths, not raw strings. A subdirectory, submodule or unrelated nested repository is not isolation evidence. Preserve existing names, even if undated or non-colocated; do not rename, recreate or silently modify them to enforce new-creation rules.

**2. Prefer the harness lifecycle.** Its create capability must support explicit JJ colocation and the required name/destination. If documented shell-created workspace registration/adoption is supported, use it; moving a shell directory alone does not adopt the harness session. Unsupported requirements block safely, never bypass ownership.

**3. Verify source and dated identity.** Resolve the intended base, bookmark, tag, revision or PR to an exact commit; preserve verified fork push identity. A failed remote refresh may use an already verified local-only base only when consistent with intent; never silently substitute another ref. Repository-scoped `gh` runs from the target absolute root with `GIT_DIR=$(jj git root)`; never execute Git directly.

Capture the local creation date once in a receipt under the source root's `.tmp/rocketclaw/`. Derive a meaningful kebab slug from fresh work, PR or revision. Normalize caller names, removing an existing date prefix before adding the captured date exactly once. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Use this **one identity** for both registered name and destination basename under the absolute local `.tmp/rocketclaw/workspaces/` parent. Verify that parent is ignored. Check registrations and filesystem destinations (including symlinks); append `-2`, `-3`, etc. on collisions without overwriting anything. Persist the selected identity across retries, resumes and midnight. No PID, random or timestamp naming substitutes. Existing isolation names and PR/source bookmarks remain unchanged.

**4. Create, verify, adopt.** Within the supported lifecycle, from the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify exact registration, root, base relationship and unchanged source bookmarks, then adopt the active harness session (OpenCode `session_move`) and verify its directory before resuming workers. Permission, sandbox, colocation or adoption failure retains state/evidence and reports the incomplete stage; it never authorizes work in the original checkout or a permission workaround. Use the existing safe decision path to choose in-place work or stop.

---

## Quick Example

You are in an Orca-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the registered path and harness session ownership, reports the existing name unchanged, and continues there.

For fresh email-validation work where the lifecycle supports creation/adoption, a captured date of `20261008` selects `20261008-fix-email-validation` as both workspace name and absolute destination basename. After exact-base verification, explicit colocated creation and colocation checks, the harness adopts it. If that identity collides, select and persist `20261008-fix-email-validation-2` after checking both inventories.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all? The skill is the order: detect first, defer to the harness, verify exact source and colocation, adopt the session, and do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass task/PR/revision identity or a meaningful name to normalize into the captured-date identity—not a random label or a separate workspace/directory name.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: dated colocated workspace at the verified trunk revision |
| `isolate <bookmark\|tag\|commit>` | Dated colocated workspace at that exact ref, preserving source bookmarks |
| `isolate PR <n>` | Dated colocated workspace at that exact verified PR head, preserving push identity |

List and inspect from a verified absolute workspace root:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj root)
```

Cleanup requires separate authorization for the exact run-owned disposable workspace; completion alone is not permission. Stop workers, inspect tracked changes/conflicts and ignored/untracked content from the target, verify exact registered name, resolved absolute path, run/harness ownership, integration and recovery references. JJ's removal snapshot does not protect ignored or untracked files. Preserve unrelated, ambiguous, still-referenced or non-disposable state. Copy required evidence outside the target into a surviving workspace's local `.tmp/` and read it back. Move the active harness session and all shell/process working directories to that surviving absolute root before removal. If the native lifecycle cannot honor these safeguards, stop.

Only then, from that surviving root, use `(cd "$surviving_root" && jj workspace remove "$verified_workspace_name")`. Verify **both deregistration and directory disappearance**: deletion failure may only produce a warning. On failure or remaining state, retain it and report the blocker; never force-delete or fall back to Git removal. `jj workspace forget` is reserved for explicit unregister-only behavior preserving files, never followed by deletion. Bookmark deletion is separate; preserve best/archive/recovery bookmarks and all still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

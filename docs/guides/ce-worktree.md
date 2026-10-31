# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing existing work.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Many harnesses already provide isolation at session start. Detect and reuse existing isolation first, preserving its verified name and colocation state even if it predates the naming convention. Otherwise prefer the harness's supported colocated JJ workspace capability, preserving its ownership and lifecycle. Unsupported required naming or colocation is a compatibility blocker, not permission to bypass the harness or create an invisible workspace.

There is no bundled script. Run JJ from each target workspace's absolute root; do not invoke Git directly. Repository-scoped `gh` calls use `GIT_DIR=$(jj git root)` from that root. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers harness-owned colocated JJ creation, otherwise explicitly creates a colocated workspace under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new workspace, with verified registered name, absolute path, revision and bookmark reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused, not renamed or recreated; changing its revision must preserve unrelated work and follow the skill's safe decision path.

```text
# New work: detect isolation, otherwise use .tmp/workspaces/20261008-account-notifications from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a workspace to an exact verified bookmark; preserve bookmark identity
/ce-worktree isolate feature/account-notifications

# Attach to the verified PR head; workspace identity 20261008-pr-1234, PR/source bookmarks unchanged
/ce-worktree isolate PR 1234

# Attach at a verified revision; workspace identity 20261008-review-abcdef1
/ce-worktree isolate abcdef1
```

Check registered workspaces and destination paths before creating anything. Reuse appropriate existing isolation without overwriting state; a genuinely separate workspace requires its own collision-free identity and verified revision.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative destinations can place a workspace outside the intended owned directory; resolve absolute roots and destinations first
- Behind-the-back workspace creation can be invisible to the harness (Orca, Cursor, and similar), defeating its lifecycle
- If local `.tmp/` is not ignored, nested workspace content can be captured in the parent
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root`, inspect `jj workspace list` and harness state, and verify the current absolute root and registered name. Reuse existing isolation unchanged. Do not infer isolation from relative path spelling or mutate an existing workspace merely to enforce new naming or colocation rules.

**2. Prefer the harness tool.** Request supported colocated JJ creation with the required dated identity and verify its returned state. Adopt the resulting workspace through the harness's session mechanism. If its naming/colocation capability is insufficient, report the compatibility blocker through the existing safe decision path; do not bypass ownership or permissions.

**3. Native JJ creation.** Only when no existing isolation or harness-owned creation applies. Ensure local `.tmp/` is ignored, resolve and verify the exact task base, and create from the source workspace's absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Every new `ce-worktree` name and destination basename is the same `YYYYMMDD-<meaningful-kebab-case-slug>` identity. Capture the local creation date once; normalize caller-supplied names without double-prefixing, derive the slug from task, PR or revision, and persist the selected identity across retries, resumes and midnight. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Preserve the existing absolute local `.tmp/` parent layout. Check both registrations and destination paths; append `-2`, `-3`, etc. for collisions without overwriting. No timestamp, PID or random naming substitutes.

The modes share this creation contract. **New work** uses the verified default/tracking revision. **Attach** resolves the exact bookmark, tag, commit or PR head, preserving its source bookmark and fork-safe push identity separately from the dated workspace name. Fetch through `jj git fetch` when required; never silently substitute another revision when exact resolution fails.

If creation or colocation verification fails, do **not** silently continue in the current workspace. Report the actual permission, capability or target blocker through the existing safe decision path; do not reset, force or use a Git-only fallback.

---

## Quick Example

You are in an Orca-managed isolated workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the current registration and harness ownership, reports the existing path/name, and continues in place without renaming it.

In a plain terminal workspace without a harness primitive, the same prompt verifies its base and local ignored `.tmp/` parent, selects a stable dated login-task identity, creates with `jj workspace add --colocate` as above, verifies `jj git colocation status`, and adopts the absolute destination.

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

On-demand isolation. Callers pass task/PR/revision context or a meaningful name to normalize into the required dated identity, not a random label. Existing source bookmarks remain unchanged.

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
| `isolate <bookmark\|tag\|commit>` | Create a dated colocated workspace at that exact verified ref |
| `isolate PR <n>` | Create a dated colocated workspace at the verified PR head, preserving source bookmarks |

Listing and switching use JJ and absolute paths:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_absolute_workspace_root"
```

Completion alone does not authorize cleanup. Respect harness-owned lifecycle and existing authorization. Before retiring run-owned files: stop workers; leave the target and move any active harness session to a surviving workspace; verify exact registered name, absolute path and run ownership; prove integration when required; preserve recovery references; copy required evidence outside the target and read it back. Inspect tracked changes, conflicts, ignored and untracked content. Removal snapshots working-copy state, but ignored/untracked files are not protected. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

From the surviving workspace's absolute root, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance; a successful exit can still carry directory-deletion warnings. If either check fails, retain remaining state and report the blocker—no force deletion or Git cleanup fallback. `jj workspace forget` is only for unregistering while deliberately preserving files, never a prelude to directory deletion. Keep bookmark deletion separate and preserve best/archive/recovery or still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

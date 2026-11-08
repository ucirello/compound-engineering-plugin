# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing current work.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already provide isolation at session start, so the common case is that you are already isolated. The skill checks that first, then prefers the harness's supported colocated JJ workspace capability, and only creates a native JJ workspace when neither applies. Nesting isolation or creating a workspace the harness cannot adopt is worse than working where you already are.

There is no bundled script. The agent runs inline JJ from the target workspace's absolute root and uses native session adoption, so the same isolation contract applies on Claude Code, Codex, Gemini, OpenCode, and Pi. See [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Makes sure isolation exists. Detects existing isolation, prefers supported harness-owned JJ capability, else `jj workspace add --colocate` under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a colocated JJ workspace, with absolute path, registered name, source revision and bookmark reported |
| Skip when | Single-task work that fits in the current workspace |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused under its existing name, even if it predates the new naming format; never rename or recreate it just for naming or colocation. An attach request still requires safe exact-target validation without discarding existing work.

```text
# New work. Detect isolation first; otherwise use a verified base and dated local .tmp/ destination.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and verified identity, stay here
/ce-worktree

# Isolate a verified existing bookmark; preserve its name
/ce-worktree isolate feature/account-notifications

# Isolate a verified PR head; preserve its source bookmark and fork push destination
/ce-worktree isolate PR 1234

# Isolate an existing verified commit
/ce-worktree isolate abcdef1
```

JJ workspace identity is separate from source bookmarks. Inspect registrations and paths before creating anything; do not import Git's one-branch-per-worktree restriction. Reuse appropriate existing isolation without overwriting it, and preserve PR/source bookmarks unchanged.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating isolation without resolving absolute source and destination roots can put work in the wrong directory tree
- A behind-the-back workspace creation can be invisible to the harness (Orca, Cursor, and similar). It cannot list, open, or clean up that workspace
- If local `.tmp/` is not ignored, scratch content can be recorded with project changes
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root` and inspect `jj workspace list` plus the harness's actual workspace contract from the absolute source root. Verify registered identity, path and task context rather than guessing from path spelling. Already isolated means report the path and existing name and work in place. Preserve unrelated tracked, conflicted, ignored and untracked work; an uncertain target or incompatible isolation takes the safe decision path, never a reset or guessed checkout.

**2. Prefer the harness tool.** Use its supported colocated JJ workspace capability where available and verify the result without bypassing ownership or lifecycle. Newly created workspaces must support the dated naming contract below. Unsupported naming or colocation is a compatibility blocker, not permission to fall back to a Git-only workspace. Adopt the destination through supported native session movement when required.

**3. Native JJ creation.** Only when neither applies. Ensure local `.tmp/` is ignored, resolve the task's configured base/remote, fetch with `jj git fetch` when appropriate, and record the exact verified base commit. Do not assume a default bookmark or silently substitute a different revision after failure. Run commands from the source workspace's absolute root and use an absolute owned destination under its local `.tmp/` parent.

Both modes use one stable `YYYYMMDD-<meaningful-kebab-case-slug>` identity for the JJ workspace name and destination basename. Capture the local creation date once; derive the slug from task, PR or revision, such as `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing; retain an already selected date/name across retries, resumes and midnight. Check both workspace registrations and destination paths; append `-2`, `-3`, etc. on collisions, never overwrite and never substitute timestamps, PIDs or random names. Keep the existing absolute local `.tmp/` parent layout and source/PR bookmarks unchanged.

For PRs, verify head repository, remote, source bookmark and exact commit using repository-scoped `gh` with `GIT_DIR=$(jj git root)` from the source root, then retrieve that exact source with JJ. Preserve its fork push mapping. Creation does not justify `gh pr checkout` or direct Git execution.

If creation, colocation, naming, permissions or harness adoption fails, the skill does **not** continue silently in the current workspace. You chose isolation for a reason. Preserve state, report the blocker, and use the existing safe decision path to work here with authorization or stop; never bypass permissions.

---

## Quick Example

You are in an Orca-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the existing registered workspace and harness ownership. You are already isolated. It reports the existing absolute path and name and continues in place without renaming it.

In a plain terminal workspace with no harness workspace tool, the same prompt resolves the verified base and stable dated identity, then creates and verifies isolation:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify the new working-copy tree matches the intended base: JJ normally creates an empty child of the specified revision. Move the active harness session to the destination through its supported native interface rather than merely changing a shell's directory.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits in the current workspace
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent already knows JJ workspaces? The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass task, PR, revision or meaningful name intent, normalized to the stable dated workspace identity above, not a separate random workspace name. Existing PR/source bookmarks remain unchanged.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated workspace from the verified base |
| `isolate <bookmark\|tag\|commit>` | Isolate the exact verified revision without renaming its source bookmark |
| `isolate PR <n>` | Isolate the verified PR head with dated workspace identity, preserving source/push mapping |

List and inspect from the relevant absolute workspace root. The skill does not wrap the JJ interface:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$absolute_destination" && jj status)
```

Completion alone does not authorize cleanup. Retire only authorized disposable run-owned workspaces, respecting harness lifecycle authority. Stop workers first; leave the target and move any active harness session to a surviving workspace. Verify the exact registered name, absolute path and run ownership. Prove integration when required, retain recovery references, and copy required evidence outside the target and read it back. Inspect tracked changes, conflicts, ignored and untracked content: the removal snapshot does not protect ignored files or files left untracked. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

From a surviving workspace's absolute root, use:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify **both** deregistration and directory disappearance; successful exit alone is insufficient because deletion failures can be warnings. On failure retain remaining state and report the blocker, never force-delete or use separate Git cleanup. Reserve `jj workspace forget` for explicitly unregistering while preserving files. Bookmark deletion is separate; preserve best/archive/recovery and still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

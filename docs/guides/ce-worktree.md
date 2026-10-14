# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already provide isolation at session start. Detect that first, then prefer supported harness-native colocated JJ creation. Explicit JJ creation is allowed only when the harness can adopt it. Never nest isolation or create a workspace the harness cannot see; there is no Git-only fallback.

There is no bundled script. The agent runs JJ from the target workspace's absolute root and respects the active harness's session and lifecycle contract. Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers supported harness-native colocated JJ creation, else explicitly creates an adoptable workspace under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new workspace, with absolute path, registered name, revision and bookmarks reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **existing ref**. Existing isolation is reused under its verified name, even if undated or noncolocated; do not rename, recreate or silently change it to enforce new-creation rules. Verify target alignment and preserve unrelated work.

```text
# New work. Detect isolation first; a new identity might be 20261008-account-notifications.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path, name and revision, stay here
/ce-worktree

# Isolate an existing bookmark, preserving its name and push target
/ce-worktree isolate feature/account-notifications

# Isolate a verified PR head; workspace identity 20261008-pr-1234, source bookmark unchanged
/ce-worktree isolate PR 1234

# Isolate a verified revision; workspace identity 20261008-review-abcdef1
/ce-worktree isolate abcdef1
```

JJ permits independent working-copy changes above the same revision. A workspace identity is not a bookmark: preserve existing PR/source bookmarks and fork-safe push mappings rather than moving them to match an isolation name.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating nested isolation can put the work in a directory tree you are not using
- Behind-the-back workspace creation is invisible to a harness that cannot adopt it
- If local `.tmp/` is not ignored, scratch state can enter the change
- Random names hide what the workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root` and match its absolute path to `jj workspace list` and harness ownership metadata. A subdirectory, submodule or repository alone is not proof of isolation. Inspect revision and colocation from that absolute root. Reuse verified existing isolation and its name. In existing-ref mode, an empty `@` directly above the verified target is already aligned; only align clean state when authorized, never reset or discard unrelated tracked, ignored or untracked work.

**2. Prefer the harness tool.** Use a supported colocated JJ capability and verify actual base, registration, name, path and colocation. Request the selected dated name and matching destination basename, then adopt the workspace through the supported session-move tool. Unsupported naming or colocation is a compatibility blocker, not permission to bypass harness ownership.

**3. Explicit JJ creation.** Only without existing isolation or supported native creation, and when the harness can adopt the result. Ensure `.tmp/` is ignored, verify an exact base and absolute destination, and run `jj workspace add --colocate` from the source absolute root. Refresh the verified remote with JJ when appropriate; offline/local-only use requires a verified usable local base and disclosure, not a guessed trunk.

The two modes share the naming contract. Capture the local `YYYYMMDD` creation date once and persist it across retries, resumes and midnight. Derive a meaningful kebab-case task, PR or revision slug; normalize caller-supplied names without double-prefixing. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Use one identity for workspace name and destination basename, preserving the absolute local `.tmp/` parent layout. Check registrations and destinations for collisions and append `-2`, `-3`, etc. without overwriting state. Never substitute timestamps, PIDs or randomness. PR isolation verifies head repository, remote, source bookmark and exact commit; source bookmarks remain unchanged.

If creation, required capability verification or adoption fails, including sandbox/permissions, the skill does **not** continue in the current checkout. It reports the blocker and follows the existing safe decision path: work here only with explicit confirmation, or stop. No Git-only fallback or permission workaround.

---

## Quick Example

You are in a harness-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the registered path and ownership, reports the existing name and revision, and continues in place without renaming or recreating it.

In a checkout with no native creation tool but supported session adoption, the same prompt verifies the base, captures a dated identity and absolute local destination, then runs:

```bash
(cd "$workspace_root" && jj workspace add --colocate \
  --name "$selected_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify registration, name/basename, path and base relationship; move the active harness session to that root before editing. `jj -R` alone does not set command cwd.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent knows `jj workspace add --colocate`? The skill is the order: detect first, defer to the harness, verify naming and colocation, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass a meaningful task, PR or revision identity, normalized to the stable dated workspace name above, not a random label or a renamed source bookmark.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: dated colocated workspace from a verified base |
| `isolate <bookmark\|tag\|commit>` | Isolate the verified revision, preserving source bookmarks |
| `isolate PR <n>` | Isolate the verified PR head and preserve its fork-safe push mapping |

List and navigation use JJ and absolute workspace paths:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$absolute_destination"
```

Completion alone does not authorize cleanup. For authorized run-owned disposable isolation, stop and await workers/processes; leave the target and move active harness sessions to a surviving workspace. Verify exact registered name, absolute path, run ownership and absence of remaining references. Prove integration when required, preserve recovery/best/archive bookmarks, and inspect tracked changes, conflicts and ignored/untracked content. Removal snapshots working-copy state, but does not protect ignored or left-untracked files. Copy required evidence outside the target into surviving local `.tmp/` and read it back before removal. Respect harness-owned lifecycle authority; unsafe or ambiguous disposal is a blocker.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
```

Verify both deregistration and directory disappearance: successful exit may still include deletion warnings. Retain remaining state and report incomplete cleanup; never force-delete or fall back to Git removal. Reserve `jj workspace forget` for explicitly authorized unregister-only operations preserving files, never followed by directory deletion. Bookmark deletion is separate; preserve recovery and still-needed references.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

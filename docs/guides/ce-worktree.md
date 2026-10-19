# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current workspace.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already create isolation at session start, so the common case is that you are already isolated. The skill checks that first, then prefers the harness's supported colocated JJ workspace capability, and only falls back to `jj workspace add --colocate` when neither applies. Nesting isolation or creating a workspace the harness cannot see is worse than working where you already are.

There is no bundled script. The agent runs inline JJ from the target workspace's absolute root, using the harness's supported session adoption and lifecycle contract on Claude Code, Codex, Gemini, OpenCode, and Pi.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Makes sure isolation exists. Detects an existing workspace, prefers a compatible harness tool, else `jj workspace add --colocate` under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name, base and source bookmark reported |
| Skip when | Single-task work that fits in the current workspace |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If already isolated, every form reuses that workspace under its verified existing name, rather than nesting or renaming it. Selecting another target there requires clean-state and ownership checks; unrelated work is never discarded.

```text
# New work. Detect isolation first. Otherwise create .tmp/workspaces/20261008-account-notifications from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path, name and bookmark, stay here
/ce-worktree

# Isolate an existing source bookmark; keep that bookmark unchanged
/ce-worktree isolate feature/account-notifications

# Isolate a verified PR head; workspace identity 20261008-pr-1234, original source bookmark unchanged
/ce-worktree isolate PR 1234

# Isolate a verified revision; workspace identity 20261008-review-abcdef1
/ce-worktree isolate abcdef1
```

If the target is already owned by an existing workspace or session, report that absolute path and prefer supported adoption. Do not force a second workspace, move its bookmarks, or modify another session's state. Separate parallel isolation requires the workflow's explicit isolation and ownership decision.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already isolated:

- Relative destinations can place a workspace in a directory tree you are not using; resolve absolute paths first
- Behind-the-back creation can be invisible to the harness (Orca, Cursor, and similar), preventing supported adoption or cleanup
- If local `.tmp/` is not ignored, workspace contents can enter the source snapshot
- Random workspace names hide what the tree is for; new names use one stable local-date-prefixed identity

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list` there, and inspect harness-provided ownership. Compare canonical absolute paths, not raw relative strings. Already isolated means report the registered name, path, revision and bookmarks and work in place. Preserve its existing name even if undated, and do not recreate, rename, or silently modify colocation. In attach mode verify the target and clean state before selecting it; uncertainty follows the safe decision path.

**2. Prefer the harness tool.** Use its supported colocated JJ workspace capability where available, preserving its ownership and lifecycle contract. Request and verify the required dated identity for a newly created workspace, then adopt it through the supported session mechanism. Unsupported colocation, naming or adoption is a compatibility blocker, not permission for Git-only isolation or a hidden fallback. Existing isolation is not renamed to satisfy new-creation rules.

**3. JJ fallback.** Only when neither applies. Ensure `.tmp/` is ignored, select and verify the exact base revision and any remote, and preserve the absolute destination's local `.tmp/` parent layout. Capture the local creation date once, derive a meaningful kebab-case task/PR/revision slug, and use `YYYYMMDD-<slug>` for both the registered workspace name and destination basename. Normalize caller-supplied names without double-prefixing; preserve the selected identity across retries, resumes and midnight. Check both registrations and destinations for collisions; append `-2`, `-3`, etc., without overwriting. Do not substitute timestamps, PIDs or randomness. For example: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`.

The two modes share the fallback. **New work** uses the verified default remote bookmark or verified local base. **Attach** uses the exact verified bookmark, tag, revision or PR head. For PRs verify the head repository, remote, source bookmark and immutable commit; preserve original PR/source bookmarks and push destinations, including forks. Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Missing/offline remotes may use a verified local base with explicit staleness disclosure, never a guessed target.

If creation, naming, colocation verification, adoption, sandbox or permissions fail, the skill does **not** silently continue in the current workspace. Report the blocker through the existing safe decision path; do not bypass permissions or fall back to a Git-only workspace.

---

## Quick Example

You are in an Orca-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the existing registration, absolute path and harness ownership. It reports that existing name and bookmarks and continues in place without renaming it.

In a plain terminal workspace with no native tool, resolve the source root, ignored local destination and verified base first, then create and verify explicitly:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$selected_dated_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

The destination basename must equal `$selected_dated_name`. Adopt the new workspace through the supported harness session mechanism when applicable; merely changing a shell directory does not move the harness session.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits in the current workspace
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent already knows JJ workspace creation? The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass a meaningful task, PR or revision slug, normalized to the stable dated workspace identity above, not a random label. Do not rename source bookmarks to match the workspace.

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
| `isolate <bookmark\|tag\|revision>` | Isolate that verified revision; preserve source bookmarks |
| `isolate PR <n>` | Isolate the verified PR head with a dated `pr-<n>` workspace slug; preserve its original source bookmark |

List and inspect from an absolute workspace root. Session adoption is harness-owned:

```bash
(cd "$workspace_root" && jj workspace list)
```

Cleanup requires existing authorization and verified run ownership; completion alone does not authorize removing a user's workspace. Stop workers, leave the target, and move any active harness session to a surviving workspace before removal. Respect harness lifecycle authority. Verify the exact registered name, absolute path and ownership; prove integration when required, preserve recovery references, and copy/read back required evidence outside the target. Inspect tracked changes, conflicts, and ignored/untracked content. Removal snapshots working-copy state, but ignored files and files left untracked are not protected. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
test ! -e "$verified_absolute_target"
```

Verify both deregistration and directory disappearance: deletion failures can be warnings despite a successful exit. If incomplete, retain remaining state and report the blocker; never force-delete or use Git removal. Reserve `jj workspace forget` for unregister-only operations that intentionally preserve files. Colocated Git metadata is managed by JJ's lifecycle. Bookmark deletion is separate; preserve best/archive/recovery bookmarks and references still needed. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

# `ce-worktree`

> Put the work in an isolated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Harnesses may already provide isolation at session start. The skill checks that first, then prefers a compatible harness-native colocated JJ workspace capability. Shell-driven creation is available only with supported harness adoption and authorization. Nesting isolation or creating a workspace the harness cannot see is worse than working where you already are.

There is no bundled script. The agent runs JJ from the target workspace's absolute root. Harness capability and lifecycle contracts remain authoritative; a Git-only primitive is not a fallback.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers compatible harness-native creation, otherwise uses explicitly colocated JJ creation with supported session adoption under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, registered name, revision and relevant bookmarks reported |
| Skip when | Single-task work that fits in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. If this workspace is already verified isolation, every form works in place rather than nesting, preserving unrelated tracked, ignored and untracked work.

```text
# New work: detect isolation first; if needed create a dated workspace from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated: report the existing path and name unchanged, stay here
/ce-worktree

# Attach a workspace to an existing bookmark
/ce-worktree isolate feature/account-notifications

# Attach a workspace to a verified PR head, preserving its source bookmark and push route
/ce-worktree isolate PR 1234

# Attach a workspace at an existing revision
/ce-worktree isolate abcdef1
```

JJ workspace names and bookmarks are separate; do not impose a one-bookmark-one-workspace restriction. Check existing isolation and concurrent ownership before creating or aligning anything. Reuse a verified existing workspace under its existing name, even if that name is not dated or it is not colocated. Do not rename, recreate or modify it merely to enforce new-creation requirements.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating nested isolation can put work in a directory the active session is not using
- Behind-the-back creation can leave a workspace the harness cannot list, adopt or retire
- Unignored local workspace storage can be accidentally included in a change
- Random names hide what a workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve `jj workspace root`, inspect `jj workspace list` from that absolute root and check harness/caller ownership metadata. Multiple registrations alone do not prove the primary checkout is isolated. Ambiguous ownership blocks creation. Report verified existing isolation and work in place; align an attach request only after verifying the target and preserving unrelated work. Dirty/conflicted or uncertain state follows the safe decision path, never reset/discard.

**2. Prefer the harness tool.** Request its supported colocated JJ workspace creation with the exact required name, destination and verified base, then verify registration, colocation and session adoption. Unsupported naming or colocation is a compatibility blocker, not permission to bypass ownership or silently accept a different name.

**3. Authorized native JJ creation.** Only when no native primitive exists and the harness can adopt and track the external workspace. Preserve the approved absolute local `.tmp/` parent layout and verify it is ignored, contained and owned. Resolve the exact base from task and repository configuration, using native `jj git fetch` where authorized; do not assume a default bookmark or remote. An unavailable remote is non-fatal only when a local base is verified and the task permits it, with stale/local coverage disclosed.

**New work** uses verified trunk; **attach** uses the exact requested bookmark, tag, revision or PR head. For PRs verify head repository, remote, bookmark, commit and fork-safe push route. Preserve PR/source bookmarks unchanged. Repository-scoped `gh` runs from the absolute target root with `GIT_DIR=$(jj git root)`; never invoke the Git executable.

Capture the local date once (`date +%Y%m%d`) and persist the selected name before creation. Every new name is `YYYYMMDD-<meaningful-kebab-case-slug>`, derived from the task, PR or revision: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing. Use one identity for the workspace name and destination basename. Check both registrations and destinations, including symlinks; append `-2`, `-3`, etc. on collision without overwriting state. Preserve the chosen identity across retries, resumes and midnight boundaries; timestamps, PIDs and randomness are not naming substitutes.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$selected_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$new_workspace_root" && jj git colocation status)
```

Verify exact name/path/base, name matching destination basename, and colocation from the new absolute root. Adopt the workspace with the harness-supported session move capability and verify the active session directory; changing shell cwd alone is insufficient. Failure of creation, permission, capability or adoption does **not** authorize continuing in the original checkout. Report retained state and offer the existing safe choice to work there explicitly or stop. Never evade a denial or use a Git-only fallback.

---

## Quick Example

You are in a harness-managed isolated workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies registration and harness ownership, reports the existing path and name unchanged, and continues in place.

With no native creation tool but supported adoption, the same prompt verifies an ignored absolute `.tmp/` destination and base, selects a dated identity, runs the explicit colocated creation above, verifies colocation and moves the active session through the harness.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

The skill is the order: detect first, defer to the harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass a task, PR or revision identity; newly selected names follow the dated identity contract above, not a separate bookmark name or random label.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated workspace from verified trunk |
| `isolate <bookmark\|tag\|revision>` | Attach a dated workspace to that verified ref |
| `isolate PR <n>` | Attach a dated workspace to the exact PR head, preserving its source bookmark |

List and navigate with native JJ and the harness-supported session move capability:

```bash
(cd "$workspace_root" && jj workspace list)
```

### Authorized retirement

Completion alone does not authorize deletion. Respect harness lifecycle authority and existing cleanup consent. Stop workers and processes first; leave the target directory and move any active harness session to a surviving workspace, verifying that move. Verify the exact registered name, absolute path and run ownership. Prove integration where required; preserve best/archive/recovery bookmarks and needed references. Copy required evidence outside the target and read it back before removal.

Inspect tracked changes, conflicts, ignored and untracked content. Removal snapshots working-copy state, but ignored and untracked files are not protected by that snapshot. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration and directory disappearance: a zero exit alone is insufficient because deletion failures may be warnings. On incomplete cleanup retain remaining state and report the blocker; never force-delete the directory or use Git cleanup. Bookmark deletion is separate and must preserve needed recovery references. Use `jj workspace forget` only to unregister while preserving files, never followed by directory deletion.

See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [command mapping](https://docs.jj-vcs.dev/latest/git-command-table/).

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

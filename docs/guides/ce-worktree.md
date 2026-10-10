# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a workspace tool rather than a core-loop step. Most coding harnesses already provide isolation at session start. The skill checks that first, then prefers compatible harness-native colocated JJ creation and adoption. Manual JJ creation is allowed only when the harness supports adoption and owns the lifecycle. Never create a workspace the harness cannot see or fall back to Git-only isolation.

There is no bundled script. The agent runs JJ from the target workspace's absolute root and uses the harness's supported session-adoption capability. Compatibility must be verified rather than inferred from a harness name.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers compatible harness-native creation/adoption, otherwise explicitly creates a colocated JJ workspace under local `.tmp/rocketclaw/workspaces/<dated-identity>` when permitted |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Existing verified isolation or a new workspace, with absolute path, registered name, base revision, bookmark/PR mapping and adoption receipt reported; otherwise a blocker |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused under its existing name without nesting, renaming, or recreating it to impose naming or colocation.

```text
# New work. Detect isolation first; otherwise create local .tmp isolation from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated: report existing registered name, path and bookmark, stay here
/ce-worktree

# Isolate an existing bookmark without changing its name
/ce-worktree isolate feature/account-notifications

# Isolate a verified PR head; preserve its source bookmark and fork push mapping
/ce-worktree isolate PR 1234

# Attach a worktree at an existing commit
/ce-worktree isolate abcdef1
```

JJ workspaces may share a base revision. Preserve source/PR bookmarks; workspace names are separate identities. Existing isolation is retained, and changing its target requires clean verified state and appropriate authority, never reset/discard or a guessed head.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating nested isolation can resolve it into a directory tree the harness is not using
- Behind-the-back creation is invisible to the harness; it cannot own or retire that workspace
- If local `.tmp/` is not ignored, workspace artifacts can enter the working-copy snapshot
- Auto-generated names like `worktree-jolly-beaming-raven` hide what the tree is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** From the absolute root inspect `jj root`, `jj workspace list`, `jj status`, and the current revision/parent. Match canonical path, registered name and harness ownership; a workspace name or Git submodule alone is not proof. Already isolated means report and reuse its existing name and state, even nondated or non-colocated. An empty `@` immediately above the verified requested head is already aligned. Dirty/conflicted or unrelated state requires a safe decision.

**2. Prefer the harness tool.** Verify its supported colocated JJ creation/adoption can honor the exact base, dated identity and lifecycle. Verify resulting colocation and registration. Unsupported naming or colocation is a compatibility blocker, not a workaround. Existing isolation is never recreated to enforce new-creation constraints.

**3. Native JJ creation/adoption.** Only when no isolation exists and the harness permits shell creation and adoption. Verify the exact base and remote, local `.tmp/` ignore rules and absolute owned destination. Capture the local date once as `YYYYMMDD`; derive a task/PR/revision kebab-case slug and normalize caller-supplied names without double date-prefixing. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Use one identity for registered name and destination basename; check registrations and filesystem entries, including symlinks, for collisions and append `-2`, `-3`, etc. Preserve the selected identity across retries, resumes and midnight; never use timestamp/PID/random substitutes or overwrite state.

The two modes share native creation. **New work** starts above verified trunk/default or an acceptable verified local base. **Attach** resolves the exact bookmark, PR head or revision. For PRs verify head repository, remote, bookmark, commit and push authority; preserve existing source bookmarks. Repository-scoped queries use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Fetch through JJ and verify the revision; do not use a Git checkout bridge. Preserve acceptable verified local-base behavior on fetch failure and disclose staleness.

If creation or adoption fails on compatibility, sandbox or permissions, the skill does **not** continue in the current checkout. Preserve partial state and use the existing safe decision path to work here only with authorization or stop. Never reset, bypass denied permissions, or fall back to Git.

---

## Quick Example

You are in harness-owned isolation created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the registered path and ownership, reports the existing name and bookmark, and continues in place without renaming it.

Where shell creation and native adoption are supported, the same prompt confirms local `.tmp/` is ignored, verifies the base and selects a collision-free dated identity, then runs:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify exact registration, base and path, then move the active harness session with its native session-move capability before editing. A shell `cd` alone does not adopt a workspace.

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

On-demand isolation. Callers pass meaningful task/PR/revision context or a name normalized into the dated identity above, not a random label. Existing source/PR bookmarks remain unchanged.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated JJ workspace above verified trunk |
| `isolate <bookmark\|revision>` | Isolate the verified ref without renaming its bookmark |
| `isolate PR <n>` | Isolate the exact PR head, preserving source/fork push mapping |

Inspect and move from absolute workspace roots. JJ owns the colocated Git metadata lifecycle:

```bash
(cd "$workspace_root" && jj workspace list)
# After all retirement safeguards below, from a surviving workspace:
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Completion is not deletion authorization. Respect harness lifecycle ownership and existing cleanup authority. Before retiring disposable run-owned isolation: stop workers, leave the target and move active sessions to a surviving workspace; verify the exact registered name, absolute path and run ownership; prove integration when required; preserve recovery references and copy/read back required evidence outside the target under local `.tmp/`. Inspect tracked changes, conflicts, ignored and untracked content: removal snapshots do not protect ignored/untracked files. Never remove unrelated, ambiguously owned, still-referenced or nondisposable content.

After `jj workspace remove`, verify both deregistration and directory disappearance; a successful exit can still include deletion warnings. On failure preserve remaining state and report the blocker, never force-delete or use Git removal. Keep bookmark deletion separate and preserve best/archive/recovery references still needed. `jj workspace forget` is only authorized unregistering while preserving files, not destructive cleanup. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

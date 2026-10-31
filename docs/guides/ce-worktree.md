# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Many coding harnesses already provide isolation at session start. Detect and reuse it under its verified existing name, even if it predates current naming rules. Prefer the harness's supported colocated JJ workspace capability. Shell creation is allowed only with authorized harness adoption; never create isolation the harness cannot see or bypass its lifecycle authority.

There is no bundled script. The agent runs native JJ from the target workspace's absolute root, using the harness's supported session-adoption interface.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, then prefers harness-native colocated JJ creation, else authorized `jj workspace add --colocate` under local `.tmp/workspaces/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new isolated workspace, with absolute path, name, revision and relevant bookmarks reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing isolation is reused rather than nested; a revision change requires authority and preserved unrelated work.

```text
# New work. Detect isolation first; otherwise create .tmp/workspaces/YYYYMMDD-account-notifications at verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report path and branch, stay here
/ce-worktree

# Attach a workspace to an existing bookmark (preserve that bookmark name)
/ce-worktree isolate feature/account-notifications

# Attach at a verified PR head; preserve its source bookmark and remote push identity
/ce-worktree isolate PR 1234

# Attach a worktree at an existing commit
/ce-worktree isolate abcdef1
```

JJ permits multiple workspaces based on the same revision. Existing isolation still takes priority; do not rename or recreate it merely to enforce new naming or colocation requirements. Report compatibility blockers through the safe decision path.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating nested isolation without checking registrations can leave the agent working in the wrong directory
- Behind-the-back creation is invisible to a harness that cannot adopt, list or clean up the workspace
- If local `.tmp/` is not ignored, artifacts can be included in the working-copy snapshot
- Random names hide purpose; newly created workspaces use a stable dated task identity

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list` and harness metadata, and establish the registered name, path and lifecycle owner. Verify `jj git colocation status` from that absolute root. Reuse existing isolation unchanged; do not infer it from Git directory shape. An unmet requirement is a compatibility blocker, not authority to modify existing isolation. Switching its revision requires caller authority and clean/conflict-free state with unrelated tracked, ignored and untracked work protected.

**2. Prefer the harness tool.** Request the verified base, absolute destination and exact dated name through its supported colocated JJ capability. Verify the results and adopt the workspace through the supported session interface. Unsupported naming/colocation or adoption is a compatibility blocker; do not bypass ownership with a Git-only tool.

**3. Authorized native JJ creation.** Only when there is no native creation tool and harness adoption is supported and authorized. Ensure `.tmp/` is ignored by inspecting local rules without Git. Resolve the actual configured/default base or exact requested ref and capture its full commit ID. Refresh its verified remote with `jj git fetch` when applicable; report staleness if using the same verified local base, never substitute another explicit ref.

Capture the local creation date once. Normalize a meaningful kebab-case task, PR or revision slug, stripping a caller-supplied leading date to avoid double-prefixing. Use one `YYYYMMDD-<slug>` identity for both the workspace name and destination basename: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Check registrations and filesystem destinations (including symlinks), append `-2`, `-3`, etc. on collisions, and never overwrite state. Persist the selected identity/base/path outside the new workspace and preserve it across retries, resumes and midnight boundaries; no timestamp, PID or random naming substitutes. Keep PR/source bookmarks unchanged. For a PR, verify head repository, remote, source bookmark and exact commit with repository-scoped `gh` using `GIT_DIR=$(jj git root)` in the source root.

Create explicitly and verify, never relying on defaults:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

The destination is `$workspace_root/.tmp/workspaces/$workspace_name`. Verify registration/path/base and move the harness session through its supported interface, then use the destination's absolute root as tool cwd. If creation, naming, colocation, adoption or permissions fail, preserve state and report it. Do not continue in the original checkout without the existing safe decision/confirmation path; no reset, Git fallback or permission workaround.

---

## Quick Example

You are in harness-managed isolation created at session start. `/ce-worktree` verifies its registration, absolute path and owner, reports the existing name and bookmarks, and continues in place without renaming or recreating it.

With supported adoption but no native creator, a fresh task captures the date, selects an unused identity such as `20261008-fix-login`, verifies its base, creates explicitly with `--colocate`, verifies colocation, and adopts the absolute `.tmp/workspaces/20261008-fix-login` destination.

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

On-demand isolation. Callers pass a meaningful task, PR or revision slug; newly selected workspace names follow the dated identity rule above. Existing source bookmarks do not change names.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated workspace at verified trunk |
| `isolate <bookmark\|tag\|commit>` | Create at the exact verified ref, unless already isolated |
| `isolate PR <n>` | Create at the verified PR head, preserving source/push identity |

List and inspect from the absolute workspace root:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj git colocation status)
```

Completion alone does not authorize cleanup. Respect explicit cleanup authority and the harness lifecycle. Stop and await workers; verify exact registered name, absolute path, run ownership and no live references. Prove integration where required, retain recovery/archive/best bookmarks, and copy required evidence and recovery IDs outside the target and read it back. Inspect tracked changes, conflicts, ignored and untracked files: ignored/untracked content is not protected by removal's snapshot. Unrelated, ambiguous or nondisposable content blocks deletion. Move any active harness session to a surviving workspace and leave the target in all tool/shell working directories before removing it:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration with `jj workspace list` and directory disappearance; successful exit alone is insufficient because deletion failures may be warnings. On incomplete cleanup preserve remaining state and report the blocker; never force-delete or fall back to Git cleanup. Use `jj workspace forget` only to unregister while preserving files. Bookmark deletion is separate, authorized independently, and must preserve recovery/archive/best and still-needed references. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing existing work.

`ce-worktree` is the **isolation** skill, a JJ workflow tool rather than a core-loop step. Most coding harnesses already create isolation at session start. Detect and reuse that first, then prefer the harness's supported colocated JJ workspace capability. Only when no harness owns the lifecycle may native JJ create isolation directly. Do not nest workspaces or create one the harness cannot adopt.

There is no bundled script. The agent runs native JJ from the target workspace's absolute root and adopts the resulting workspace through the active harness's supported session interface.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers harness-owned colocated JJ creation, else explicitly uses `jj workspace add --colocate` under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a new colocated workspace, with absolute path, registered name, revision and task bookmark reported |
| Skip when | Single-task work that fits on a branch in the current checkout |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Existing verified isolation is reused under its existing name, even if undated or not colocated. Never rename, recreate or silently change it to enforce new-creation requirements. A conflicting requested target uses the safe decision path without discarding work.

```text
# New work. Detect isolation first; otherwise verify base and create local .tmp isolation.
/ce-worktree for the account-notifications feature

# Already isolated: report existing absolute path and registered name, stay here
/ce-worktree

# Isolate an existing bookmark without renaming that source bookmark
/ce-worktree isolate feature/account-notifications

# Isolate the exact verified PR head; preserve its PR/source bookmark
/ce-worktree isolate PR 1234

# Isolate an exact verified revision
/ce-worktree isolate abcdef1
```

Inspect JJ workspace registrations and harness ownership before creating anything. Reuse appropriate existing isolation rather than imposing Git's branch-checkout restrictions on JJ. Ambiguous ownership or targets block creation.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative destinations can resolve into the wrong directory tree
- Behind-the-back creation can bypass a harness's ownership and lifecycle contract
- Unignored temporary workspace directories can enter the source snapshot
- Random names hide what the workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list` and the harness's isolation record, and verify the registered name/path. Already isolated means report and reuse it without renaming or recreating it. Do not change revisions through unrelated tracked, ignored or untracked work.

**2. Prefer the harness tool.** Use its supported colocated JJ workspace capability and lifecycle contract. Request and verify the required dated name and destination basename; unsupported naming or colocation is a compatibility blocker, not permission to bypass the harness or use Git-only isolation. Adopt the new absolute workspace root through the supported session interface.

**3. Native JJ creation.** Only when no harness owns the lifecycle. Ensure `.tmp/` is ignored. Capture the local creation date once; derive a meaningful kebab-case slug from task, PR, revision or caller input. Normalize an already dated caller name without double-prefixing. Use one `YYYYMMDD-<slug>` identity for the JJ name and destination basename under the existing local `.tmp/` parent. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Preserve the selected identity across retries, resumes and midnight. Check both registrations and destinations; append `-2`, `-3`, etc. for collisions without overwriting anything. Do not use timestamps, PIDs or random IDs instead.

The two modes share verified base selection. **New work** resolves the actual configured default bookmark/remote or a verified local base, never guesses a trunk. **Attach** resolves exactly the requested bookmark, tag, commit or PR head. For PRs verify head repository, remote, source bookmark and commit; preserve the PR/source bookmark unchanged. Run repository-scoped `gh` from the absolute target root with `GIT_DIR=$(jj git root)`; never use `gh pr checkout` as a workspace bridge.

If creation, adoption, naming or colocation verification fails, do not silently continue in the source workspace, reset state or bypass permissions. Use the workflow's existing safe decision path; non-interactive callers report the blocker.

---

## Quick Example

You are in a harness-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` verifies the existing registration and harness ownership, reports its unchanged name/path, and continues there.

In a plain terminal workspace with no harness lifecycle owner, select the stable dated identity and absolute local `.tmp/` destination, verify the base and collision checks, then run:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Require verified colocation, then adopt that absolute directory as the command/session working directory. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all? The skill is the order: detect first, defer to the harness, explicitly verify colocation and stable naming, and do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers derive a meaningful dated workspace identity from the task, PR or revision; this does not rename task/PR/source bookmarks. Existing isolation keeps its existing name.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: dated colocated workspace at a verified base |
| `isolate <branch\|tag\|commit>` | Dated colocated workspace at exactly that verified ref |
| `isolate PR <n>` | Dated colocated workspace at that verified PR head; preserve source bookmark |

List and inspect from an absolute surviving workspace root:

```bash
(cd "$surviving_workspace_root" && jj workspace list)
cd "$verified_workspace_root"
```

Completion alone does not authorize cleanup. Respect user authorization and harness lifecycle ownership. Before retiring run-owned disposable isolation: stop workers; leave the target and move active harness sessions to a surviving workspace; verify exact registered name, absolute path and run ownership; prove integration where required; preserve recovery/best/archive references; copy and read back required evidence outside the target. Inspect tracked changes, conflicts, ignored and untracked content: removal snapshots the working copy but does not protect ignored or untracked files. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.

Only after those safeguards, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance: a successful exit may still carry a deletion warning. On failure or incomplete removal, retain remaining state and report the blocker; never force-delete or fall back to Git removal. `jj workspace forget` is reserved for unregistering while preserving files. JJ manages colocated worktree metadata. Bookmark deletion is separate; preserve any references still required.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

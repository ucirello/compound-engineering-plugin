# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Detect existing isolation first, prefer a supported harness-native JJ workspace capability, and create a workspace with native JJ only when the harness can adopt it. Never nest isolation or create a workspace invisible to its owning harness. There is no bundled script and no direct Git executable fallback. See the [skill](../../skills/ce-worktree/SKILL.md) for its complete decision path.

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Verifies existing isolation, or creates a colocated JJ workspace under local `.tmp/` |
| When to use it | Starting isolated work, or when `ce-work` / `ce-code-review` offers isolation |
| What it produces | Verified absolute path, registered workspace name, revision, bookmarks and lifecycle owner, or a blocker |
| Skip when | Work fits in the current checkout, or verified existing isolation already suffices |

## Example invocations

Empty arguments or a work description mean **new work**. `isolate` plus a ref means **existing ref**. Every form reuses verified existing isolation rather than nesting it.

```text
/ce-worktree for the account-notifications feature
/ce-worktree
/ce-worktree isolate feature/account-notifications
/ce-worktree isolate PR 1234
/ce-worktree isolate abcdef1
```

Resolve an existing bookmark, tag, PR head or revision to its exact commit. Verify PR head repository, remote and bookmark, including fork ownership. Keep source/PR bookmarks and push relationships unchanged. JJ workspaces can share a revision; do not impose Git's one-branch-one-worktree restriction. Preserve the intended review/fix range.

## The Problem

Creating isolation by default can nest workspaces, bypass harness ownership, expose scratch files to tracking, or hide purpose behind opaque names. Isolation is an ordered decision, not a creation script.

## The Solution

**1. Detect existing isolation.** Resolve the absolute workspace root with `jj workspace root`. From that root inspect `jj workspace list`, `jj status` and `jj git colocation status`, together with harness ownership/session information. Multiple registrations or colocation alone do not prove isolation. Reuse verified existing isolation under its current name, even if undated; do not rename, recreate or silently change colocation. Report ambiguous state through the skill's safe decision path. For an existing-ref request verify the target before aligning; an empty `@` immediately above it is already aligned. Preserve unrelated tracked, conflicted, ignored and untracked work.

**2. Select a stable identity for new creation.** Capture the local creation date once. Every newly created workspace, including caller-selected names, uses `YYYYMMDD-<meaningful-kebab-case-slug>`, for example `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize supplied names without double-prefixing a valid dated identity. Preserve the selected name/date across retries, resumes and midnight boundaries. Use one identity for both JJ workspace name and destination basename. Keep the existing absolute local `.tmp/` parent layout, defaulting to `<absolute-source-root>/.tmp/workspaces/<identity>`. Check registrations and destination paths; append `-2`, `-3`, etc. for collisions without overwriting state. Never substitute timestamps, PIDs or random names. Names do not rename source/PR bookmarks.

**3. Prefer the harness capability.** Request supported colocated JJ creation with the selected dated name, absolute destination and verified base. Verify the actual registration, name, matching basename, revision and colocation. Unsupported naming, colocation or session adoption is a compatibility blocker, not permission to bypass harness ownership or fall back to a Git-only tool.

**4. Native JJ creation with harness adoption.** Only when permitted by the harness lifecycle, verify the actual requested project base/remote and exact commit. Refresh with native JJ where appropriate; disclose a failed refresh and use an existing local base only when acceptable to the workflow. Never substitute another ref. Ensure `.tmp/` is ignored, preserving existing rules. Repository-scoped `gh` runs from the absolute target root with `GIT_DIR=$(jj git root)` exported. Create explicitly:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
(cd "$absolute_destination" && jj workspace list)
(cd "$absolute_destination" && jj status)
```

Verify exact registered name/path, dated basename and working-copy parent equal to the verified base. Adopt the destination using the harness's supported session-move capability (OpenCode: `opencode.session_move`); shell `cd` alone does not adopt a session. Run later commands from the destination's absolute root so file lists remain repository-relative.

On permission, naming, adoption or verification failure preserve state and use the skill's safe decision path. Do not silently continue in the original checkout, reset work or bypass permissions.

## Quick Example

In harness-managed isolation, `/ce-worktree` reports the existing verified path and name and continues there unchanged. In a normal workspace without supported native creation, it verifies the requested base, selects a stable identity such as `20261008-fix-email-validation`, creates the matching destination under local `.tmp/` with `--colocate`, verifies colocation and registration, and moves the harness session there before work.

## Chain Position

On-demand isolation. Callers pass task, PR or revision context or a meaningful name normalized by the same dated naming rule.

```text
/ce-work         -> /ce-worktree (optional isolation before implementation)
/ce-code-review  -> /ce-worktree (review without touching in-progress work)
```

## Reference and cleanup

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation; otherwise derive a new-work identity from context |
| `<work description>` | Create isolation above the verified project base |
| `isolate <bookmark\|tag\|commit>` | Resolve the exact ref and preserve review/fix scope |
| `isolate PR <n>` | Verify and retrieve the exact PR head without renaming its source bookmark |

List with `jj workspace list` from the absolute workspace root; switch through the harness's session capability. Completion alone does not authorize cleanup. Respect harness-owned lifecycle and existing cleanup authority.

Before retiring a run-owned disposable workspace: stop workers, leave it, and move active harness sessions to a surviving workspace. Verify exact registered name, absolute path and ownership. Prove integration when required; preserve best/archive/recovery bookmarks and other needed references. Inspect tracked changes, conflicts, ignored and untracked content. Removal snapshots working-copy state, **not ignored or left-untracked files**. Copy required evidence outside the target and read it back before removal. Unrelated, ambiguously owned, still-referenced or non-disposable content blocks removal.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
```

Verify both deregistration and exact directory disappearance: directory-deletion failures may be warnings even with successful exit. On incomplete cleanup retain remaining state and report the blocker; never force-delete or fall back to Git removal. Bookmark deletion is separate and must preserve recovery references. Use `jj workspace forget` only for an explicit unregister-only operation that preserves files, never as deletion preparation.

Native reference: https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace

## See Also

- [`/ce-work`](./ce-work.md): offers isolation before implementation
- [`/ce-code-review`](./ce-code-review.md): offers isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in isolation without shipping

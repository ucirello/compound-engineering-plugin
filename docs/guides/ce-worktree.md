# `ce-worktree`

> Put the work in an isolated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Most coding harnesses already create isolation at session start, so the common case is that you are already isolated. The skill checks that first, then prefers a compatible harness-owned colocated JJ workspace capability. Otherwise it uses explicit JJ creation only when the harness can adopt the workspace without bypassing its lifecycle. Nesting a workspace or creating one the harness cannot see is worse than working where you already are.

There is no bundled script. The agent runs native JJ from the target workspace's absolute root; native tool mappings remain specific to Claude Code, Codex, Gemini, OpenCode, and Pi. Never invoke Git directly or use a Git-only fallback.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Makes sure isolation exists. Detects existing isolation, prefers a compatible harness tool, else `jj workspace add --colocate` under local `.tmp/workspaces/<dated-identity>` with explicit harness adoption |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a verified colocated JJ workspace, with absolute path, registered name, revision and relevant bookmark reported |
| Skip when | Single-task work that fits in the current workspace |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref selects an existing revision. If this checkout is already isolated, every form preserves its existing name and ownership rather than nesting; moving to a requested revision still requires a verified target and preservation of unrelated work.

```text
# New work. Detect isolation first. Otherwise create a dated JJ workspace from verified trunk.
/ce-worktree for the account-notifications feature

# Already isolated (common in Orca or Cursor): report existing name/path/bookmark, stay here
/ce-worktree

# Isolate the verified revision of an existing bookmark; keep its name unchanged
/ce-worktree isolate feature/account-notifications

# Isolate the verified PR head; preserve its source bookmark and push target
/ce-worktree isolate PR 1234

# Isolate a verified existing revision
/ce-worktree isolate abcdef1
```

JJ permits multiple workspaces based on the same revision. This does not authorize moving another workspace's bookmark, discarding work or bypassing harness ownership. Reuse verified existing isolation without renaming or recreating it merely to enforce new naming or colocation requirements.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Relative creation destinations can resolve into a directory tree you are not using
- Behind-the-back workspace creation can be invisible to the harness (Orca, Cursor, and similar). It cannot list, open, or clean up that tree
- If local `.tmp/` is not ignored, scratch and nested workspace content can enter the parent change
- Opaque random names hide what the workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute physical `jj workspace root`, inspect `jj workspace list`, status and current revision/bookmarks, and corroborate harness session metadata or the caller's receipt. A directory name or default JJ workspace alone proves neither isolation nor ownership. Report verified existing isolation and work in place. For a requested ref, resolve it first and align only when authorized and preserving unrelated tracked, ignored and untracked work. Ambiguity is a safe compatibility decision, not permission to initialize or convert a repository.

**2. Prefer the harness tool.** A native workspace primitive is suitable only if it honors the verified JJ base, explicit colocation, selected dated name/destination and session lifecycle. Request and verify these controls without bypassing ownership. Unsupported naming or colocation is a compatibility blocker, not permission to create noncompliant isolation. Preserve the supported session-adoption/handoff contract.

**3. Explicit JJ creation.** Only when new isolation is needed and harness adoption is supported. Verify local `.tmp/` ignore coverage, making only an authorized narrow ignore change if needed. Resolve the actual task/default bookmark and remote, refresh with JJ when appropriate, and record the exact base. A verified local-only base may be used with disclosure; never substitute a guessed default.

The modes share the same naming and creation contract. Capture the local creation date once (`date +%Y%m%d`) and persist it in the receipt. Derive a meaningful lowercase kebab-case slug from fresh work, PR or revision, such as `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing. Use one identity for both registered JJ workspace name and destination basename under the existing absolute local `.tmp/` parent layout. Check registrations and disk entries, including symlinks, for collisions; append `-2`, `-3`, etc., never overwrite or use timestamps, PIDs or random substitutes. Save the date, selected identity, absolute path, exact base and ownership outside the destination; reuse them across retries, resumes and midnight boundaries.

For a PR, export `GIT_DIR=$(jj git root)` in the target absolute workspace before repository-scoped `gh` metadata calls. Verify the head repository, bookmark, remote and exact commit; fetch through JJ and preserve source bookmark names and fork push targets. Never use `gh pr checkout` or another Git-backed workspace bridge.

If creation, verification, navigation, sandbox or permission checks fail, the skill does **not** continue in the current checkout. Report the blocker through the existing safe decision path: resolve it, explicitly authorize work here, or stop. Preserve partial state and evidence; no reset, discard, Git fallback or permission workaround.

---

## Quick Example

You are in an Orca-managed workspace created at session start. `ce-work` offers isolation. `/ce-worktree` corroborates its absolute path, JJ registration and harness receipt. You are already isolated. It reports the existing name, path and bookmark and continues in place without renaming or changing colocation.

In a plain terminal workspace, the same prompt first verifies supported harness adoption/navigation/lifecycle capability (or an explicit authorized handoff), blocking creation when that contract cannot be met. It verifies `.tmp/` ignore coverage, the exact base and a collision-free dated identity. From the surviving source workspace's absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$dated_identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify the registration/name/path/base and colocation, then adopt the absolute destination through supported harness session navigation (OpenCode `session_move` when available). If adoption is unsupported, report an explicit handoff limitation rather than claiming the session moved.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits on a branch in the current checkout
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all, when the agent already knows `jj workspace add --colocate`? The skill is the order: detect first, defer to compatible harness ownership, verify colocation, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers pass meaningful task/PR/revision context or a normalized dated identity, not a random label. New workspace names and destination basenames follow the dated contract; PR/source bookmarks remain unchanged.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: create a dated colocated JJ workspace from verified trunk |
| `isolate <bookmark\|tag\|commit>` | Isolate that exact verified revision |
| `isolate PR <n>` | Isolate the exact verified PR head; preserve source bookmark/push tracking |

List and navigation use native JJ and the harness's session capability. Always set cwd to the appropriate absolute root:

```bash
(cd "$surviving_workspace_root" && jj workspace list)
cd "$absolute_destination"
jj workspace root
```

Cleanup is separately authorized, never implied by completion. Stop/join workers, leave the target, and move any active harness session to a surviving absolute workspace root. Verify the exact registered name, absolute path, run ownership and lifecycle authority. Prove integration when required; preserve recovery/best/archive bookmarks and any still-needed references. Inspect tracked changes, conflicts, ignored and untracked content. Removal snapshots working-copy state, but ignored and untracked files are not protected. Unknown, unrelated, still-referenced or valuable content blocks removal.

Copy required evidence and recovery files outside the target and read them back before removal. Then, from the surviving absolute root, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. JJ owns colocated metadata cleanup. Respect harness-owned lifecycle authority; never remove it behind the owner. Verify **both** deregistration and directory disappearance: a successful exit can still include deletion warnings. If cleanup fails or is incomplete, retain state and report the blocker; never force-delete or fall back to Git. Bookmark deletion is separate. `jj workspace forget` is only for explicitly authorized unregistering while preserving files, not destructive cleanup.

Command references: [JJ workspace](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git command table](https://docs.jj-vcs.dev/latest/git-command-table/), and [JJ for Git experts](https://docs.jj-vcs.dev/latest/git-experts/).

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

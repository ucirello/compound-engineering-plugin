# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing existing work.

`ce-worktree` is the **isolation** skill rather than a core-loop step. Detect existing isolation first, prefer the harness's supported colocated JJ capability, and otherwise use native JJ instructions. Do not nest a workspace or create one the harness cannot adopt. There is no bundled creation script.

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detect existing isolation, prefer harness-owned JJ isolation, otherwise explicitly create a colocated JJ workspace |
| When to use it | Starting isolated work, or when `ce-work` / `ce-code-review` offers isolation |
| What does it produce? | Existing isolation reused, or a verified absolute path, workspace name, base revision and bookmarks |
| Skip when | Work fits in the current workspace or existing isolation already suffices |

## Example invocations

```text
/ce-worktree for the account-notifications feature
/ce-worktree
/ce-worktree isolate feature/account-notifications
/ce-worktree isolate PR 1234
/ce-worktree isolate abcdef1
```

New work uses the verified repository default and tracking remote, not a guessed ref. Attach mode resolves the exact bookmark, tag, revision or PR head, including the head repository and remote for forks. An unresolved or ambiguous target blocks creation; never fetch another ref as a substitute. Keep PR/source bookmarks unchanged. A named existing workspace is not recreated merely to attach another target; preserve unrelated work and use the skill's safe decision path.

## Isolation decision

1. **Detect existing isolation.** Inspect JJ workspace registration, absolute root and harness ownership. Reuse verified existing isolation under its existing name, even if not date-prefixed. Inspect colocation without renaming, recreating or silently modifying that workspace. An empty `@` directly above the exact verified target is already aligned. Dirty/conflicted state or uncertain ownership requires the safe stop/decision path, never reset or discard.
2. **Prefer the harness capability.** Request supported colocated JJ creation with the required name and destination. Verify those properties without bypassing the harness lifecycle. Unsupported naming or colocation is a compatibility blocker, not permission for a Git-only fallback. Adopt the result through the harness's session-move capability; shell `cd` alone does not move a session.
3. **Native JJ creation when ownership permits.** Use the source workspace's absolute root, a verified base and an absolute run-owned destination under its ignored local `.tmp/` layout. Never silently continue in the original workspace after an isolation or permission failure. Report the blocker and use the existing authorized decision path.

## Stable new-workspace identity

Capture the local creation date once. Derive a meaningful kebab-case slug from the task, PR or revision. Normalize caller-supplied names without double-prefixing. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`.

Use that single `YYYYMMDD-<slug>` identity for both the JJ workspace name and destination directory basename. Preserve the local `.tmp/` parent layout. Check registered names **and** filesystem destinations; append `-2`, `-3`, etc. on collisions without overwriting. Do not use timestamps, PIDs or random names. Persist the selected date, identity, verified base, absolute path and ownership before creation and reuse them across retries, resumes and midnight. A matching prior attempt is resumed only after ownership/path/revision verification. Existing isolation names and PR/source bookmarks are not renamed.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify registration, exact path, name = basename, base revision and colocation before execution. Run subsequent JJ commands with the absolute target workspace as their working directory; `jj -R` does not change relative output paths. Repository-scoped GitHub CLI calls require `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)` with the verified repository/host.

## Chain position

Callers derive a meaningful task/PR/revision slug, not a separate random workspace name. The same persisted dated identity is used throughout.

```text
/ce-work         -> /ce-worktree (optional isolation)
/ce-code-review  -> /ce-worktree (concurrent isolated review)
```

## Listing, switching and authorized removal

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_absolute_workspace_root"
```

Completion alone does not authorize deletion. Respect existing cleanup authorization and harness-owned lifecycle authority. Before retiring a disposable run-owned workspace:

- Stop workers; leave the target and move any active harness session to a surviving workspace.
- Verify the exact registered name, absolute path and run ownership. Never remove unrelated, ambiguous, still-referenced or non-disposable content.
- Prove integration when required. Preserve best/archive/recovery references and copy required evidence outside the target, then read it back.
- Inspect tracked changes, conflicts and ignored/untracked content. Removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot.

From the surviving workspace's absolute root:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify **both** deregistration and directory disappearance; directory-deletion failures can be warnings even on successful exit. On failure retain remaining state and report the blocker; never force-delete or fall back to Git removal. JJ owns colocated metadata cleanup. Keep bookmark deletion separate, retaining references still needed. Use `jj workspace forget` only to unregister while intentionally preserving files, never before directory deletion.

## References

- [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace)
- [Git command translation](https://docs.jj-vcs.dev/latest/git-command-table/)
- [`/ce-work`](./ce-work.md)
- [`/ce-code-review`](./ce-code-review.md)
- [`/ce-commit`](./ce-commit.md)

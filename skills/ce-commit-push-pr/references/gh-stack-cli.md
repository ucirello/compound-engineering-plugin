# `gh stack` semantics this skill relies on

Verified against `gh stack version 0.1.0`. `gh stack <command> --help` is authoritative — if it
disagrees with anything here, follow `--help` and say so in your report. (`gh stack help <command>`
does not work; it prints top-level help.)

Only the behavior that changes a decision in stack mode is listed. This file is self-contained on
purpose: do not depend on the user having a separate `gh-stack` skill installed.

## Backing-Git adapter gate

`gh stack` mutates Git provider branches and the checked-out Git head. This workflow supports those mutations only through a verified colocated Jujutsu/Git checkout. Before any `gh stack checkout`, `gh stack init`, or `gh stack add`, verify all of these conditions:

- `jj config get --repository <workspace-root> git.colocate` is `true`, `jj workspace root` identifies `<workspace-root>`, and `jj git root` identifies its directly contained `.git` directory. Reject a bare, linked, external, or otherwise non-colocated backing repository.
- Run `jj git import` and `jj git export`, then import once more. Each command must succeed without a bookmark conflict, unexpected movement, or unexportable ref. Use `jj status`, `jj sparse list`, and separate `jj log` queries for `git_head()` and `@-` to verify a clean, conflict-free, full working copy whose parent is exactly the backing checkout head. If either revision is absent or ambiguous, the adapter is not proven.
- After that synchronization, inspect each affected name with `jj bookmark list` and `jj log`. Every existing provider branch the command will adopt must be represented by one unconflicted local bookmark at the expected commit. A name absent after import may be created only when the command's documented behavior requires it and its exact expected target is already known; a collision, unexpected target, or bookmark conflict blocks the workflow.

If any condition is false or cannot be verified using Jujutsu, stop with a residual. Do not run a provider mutation in a non-colocated repository, use raw Git commands or an improvised synchronization bridge, or claim stack support for that checkout. After each allowed provider mutation, run `jj git import`, update a stale workspace with `jj workspace update-stale` if required, and repeat the head, working-copy, bookmark, export, and final-import checks before continuing. The imported state must match the provider mutation's documented effect exactly; otherwise stop before another provider action.

## Classifying a parent

```bash
gh stack checkout "<parent-pr-number>"
```

Resolve a parent by **PR number** whenever one exists — that is what pulls a stack down from
GitHub. A bare bookmark exported for Git interop resolves against **local** stacks only, so a bookmark-only parent can be
classified locally and no further.

Branch on the exit code; status text goes to stderr and must not be parsed.

| Exit | Meaning | What it means here |
|---|---|---|
| 0 | Success | Parent is in a stack, and `HEAD` has moved to it |
| 2 | Not in a stack | Parent is standalone; nothing was checked out or fetched |
| 5 | Invalid arguments | Fix the invocation; see `--help` |
| 6 | Disambiguation required | Branch is in several stacks — check out a non-shared branch |
| 9 | Stacked PRs unavailable | Not enabled on this repository; tell the user and stop |

```bash
gh stack view --json    # JSON on stdout: trunk, currentBranch,
                        # branches[] { name, head, base, isCurrent, isMerged, needsRebase,
                        #              pr { number, url, state } }
```

`base` is the parent SHA the provider branch was last known to contain, not the parent's current tip;
`needsRebase` is true when that tip is no longer an ancestor. There is no field naming the top of
the stack and no documented branch ordering, so do not derive position from this payload — use
`add`'s exit 5 instead.

## Resolving a PR head

`gh pr view "<n>" --json headRefName,headRefOid,author` identifies the head; `headRefName` alone
does not, because a same-repo name can be absent or stale locally and can collide with an unrelated
bookmark. Fetch the head bookmark's remote with `jj git fetch`, verify `headRefOid` is reachable,
and create a local bookmark at that revision only when no bookmark of that name exists.

## Building

```bash
gh stack init [--base "<trunk>"] "<branch>"...
```

Processes provider branches bottom to top and checks out the **last** one. The command can create
missing provider branches, but this workflow permits that only under the adapter gate's synchronized-absence,
known-target condition.
There is no separate adopt mode: existence decides. `--base` selects a non-default trunk, so a
parent branch can serve as the trunk without joining the stack.

```bash
gh stack add "<branch>"
```

Must run from the **top** branch of the stack (or the trunk while it is still empty); anywhere else
exits **5**. Exit 5 here means "you are not on the top", and moving there with `gh stack top` is a
decision, not a fix: it changes which layer the new branch is parented to. Whether that is correct
belongs to the caller — when a specific parent was named, it is not. Without `-Am`, `add` does not
alter file content. After it moves the provider checkout, synchronize the Jujutsu workspace and
verify the intended change and excluded paths before continuing.

```bash
gh stack submit --auto [--open]
```

`--auto` avoids a title prompt per new PR. `--open` creates PRs ready for review instead of drafts,
and also marks pre-existing drafts ready.

## Never

- **`gh stack link`** — GitHub-only by design, creates no local stack tracking, so a later
  `gh stack submit`, `gh stack view`, or `gh stack merge` will not see the layer.
- **`gh pr merge`** on a stack member — it cannot merge a stack. Landing uses `gh stack merge`.
- **Bare `view` / `submit` / `init` / `add` / `checkout`** — each prompts or opens a TUI that
  blocks under a PTY. Always pass the arguments and flags shown above.

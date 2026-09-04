# `gh stack` semantics this skill relies on

Verified against `GIT_DIR="$(jj git root)" gh stack version 0.1.0`. `GIT_DIR="$(jj git root)" gh stack <command> --help` is authoritative — if it
disagrees with anything here, follow `--help` and say so in your report. (`GIT_DIR="$(jj git root)" gh stack help <command>`
does not work; it prints top-level help.)

Only the behavior that changes a decision in stack mode is listed. This file is self-contained on
purpose: do not depend on the user having a separate `gh-stack` skill installed.

## Classifying a parent

```bash
GIT_DIR="$(jj git root)" gh stack checkout "<parent-pr-number>"
```

Resolve a parent by **PR number** whenever one exists; that is what pulls a stack down from
GitHub. A bare bookmark name resolves against **local** stacks only, so a bookmark-only parent can be
classified locally and no further.

Route on the exit code; status text goes to stderr and must not be parsed.

| Exit | Meaning | What it means here |
|---|---|---|
| 0 | Success | Parent is in a stack, and the current stack layer changed to it |
| 2 | Not in a stack | Parent is standalone; nothing was checked out or fetched |
| 5 | Invalid arguments | Fix the invocation; see `--help` |
| 6 | Disambiguation required | Bookmark is in several stacks; select a non-shared stack layer |
| 9 | Stacked PRs unavailable | Not enabled on this repository; tell the user and stop |

```bash
GIT_DIR="$(jj git root)" gh stack view --json    # JSON on stdout: trunk, currentBranch,
                        # branches[] { name, head, base, isCurrent, isMerged, needsRebase,
                        #              pr { number, url, state } }
```

`base` is the parent commit ID the bookmark was last known to contain, not the parent's current tip;
`needsRebase` is true when that tip is no longer an ancestor. There is no field naming the top of
the stack and no documented layer ordering, so do not derive position from this payload; use
`add`'s exit 5 instead.

## Resolving a PR head bookmark

`GIT_DIR="$(jj git root)" gh pr view "<n>" --json headRefName,headRefOid,author` identifies the head; the API field
`headRefName` alone does not, because a same-repository bookmark can be absent or stale locally and
can collide with an unrelated bookmark. After `jj git fetch`, create a local bookmark at the
revision corresponding to `headRefOid` only when it can be resolved and does not collide.

## Building

```bash
GIT_DIR="$(jj git root)" gh stack init [--base "<trunk>"] "<bookmark>"...
```

Processes bookmarks bottom to top and selects the **last** one. **Existing bookmarks are adopted;
missing ones are created**; the first starts from the trunk and each later one from the bookmark before it.
There is no separate adopt mode: existence decides. `--base` selects a non-default trunk, so a
parent bookmark can serve as the trunk without joining the stack.

```bash
GIT_DIR="$(jj git root)" gh stack add "<bookmark>"
```

Must run from the **top** bookmark of the stack (or the trunk while it is still empty); anywhere else
exits **5**. Exit 5 here means "you are not on the top", and moving there with `GIT_DIR="$(jj git root)" gh stack top` is a
decision, not a fix: it changes which layer the new bookmark is parented to. Whether that is correct
belongs to the caller — when a specific parent was named, it is not. Without `-Am`, `add` does not
does not alter working-copy content, so the current JJ change remains present.

```bash
GIT_DIR="$(jj git root)" gh stack submit --auto [--open]
```

`--auto` avoids a title prompt per new PR. `--open` creates PRs ready for review instead of drafts,
and also marks pre-existing drafts ready.

## Never

- **`GIT_DIR="$(jj git root)" gh stack link`** — GitHub-only by design, creates no local tracking, so a later
  `GIT_DIR="$(jj git root)" gh stack submit`, `GIT_DIR="$(jj git root)" gh stack view`, or `GIT_DIR="$(jj git root)" gh stack merge` will not see the layer. It exists for
  bookmarks managed by external tools.
- **`GIT_DIR="$(jj git root)" gh pr merge`** on a stack member — it cannot merge a stack. Landing uses `GIT_DIR="$(jj git root)" gh stack merge`.
- **Bare `view` / `submit` / `init` / `add` / `checkout`** — each prompts or opens a TUI that
  blocks under a PTY. Always pass the arguments and flags shown above.

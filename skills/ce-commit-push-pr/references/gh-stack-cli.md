# `gh stack` semantics this skill relies on

Verified against `gh stack version 0.1.0`. `gh stack <command> --help` is authoritative — if it
disagrees with anything here, follow `--help` and say so in your report. (`gh stack help <command>`
does not work; it prints top-level help.)

Pair every `gh stack` invocation with `GIT_DIR` set to the path from `jj git root`. `gh stack`
talks to the git store; without that env it fails in a non-colocated workspace.

Only the behavior that changes a decision in stack mode is listed. This file is self-contained on
purpose: do not depend on the user having a separate `gh-stack` skill installed.

## Classifying a parent

```bash
GIT_DIR=<git-dir> gh stack checkout "<parent-pr-number>"
```

Resolve a parent by **PR number** whenever one exists — that is what pulls a stack down from
GitHub. A bare bookmark name resolves against **local** stacks only, so a bookmark-only parent can be
classified locally and no further.

Branch on the exit code; status text goes to stderr and must not be parsed.

| Exit | Meaning | What it means here |
|---|---|---|
| 0 | Success | Parent is in a stack, and the working copy has moved to it |
| 2 | Not in a stack | Parent is standalone; the working copy was not moved or fetched |
| 5 | Invalid arguments | Fix the invocation; see `--help` |
| 6 | Disambiguation required | Bookmark is in several stacks — check out a non-shared bookmark |
| 9 | Stacked PRs unavailable | Not enabled on this repository; tell the user and stop |

```bash
GIT_DIR=<git-dir> gh stack view --json    # JSON on stdout: trunk, currentBranch,
                        # branches[] { name, head, base, isCurrent, isMerged, needsRebase,
                        #              pr { number, url, state } }
```

`base` is the parent SHA the layer was last known to contain, not the parent's current tip;
`needsRebase` is true when that tip is no longer an ancestor. There is no field naming the top of
the stack and no documented branch ordering, so do not derive position from this payload — use
`add`'s exit 5 instead. `currentBranch` / `branches[].name` are GitHub head names; they match the
local bookmark of the same name after push.

## Resolving a PR head

`GIT_DIR=<git-dir> gh pr view "<n>" --json headRefName,headRefOid,author` identifies the head; `headRefName` alone
does not, because a same-repo name can be absent or stale locally and can collide with an unrelated
bookmark. Create a local bookmark at `headRefOid` (`jj bookmark create <name> -r <headRefOid>`),
fetching with `jj git fetch` when that commit is not reachable — reachability leaves the commit with
no bookmark to name. If the commit is still unreachable after fetch, stop with a residual; do not
parse `.git/` or `.jj/` files for the SHA.

## Building

```bash
GIT_DIR=<git-dir> gh stack init [--base "<trunk>"] "<bookmark>"...
```

Processes layers bottom to top and checks out the **last** one. **Existing bookmarks are adopted;
missing ones are created** — the first from the trunk, each later one from the layer before it.
There is no separate adopt mode: existence decides. `--base` selects a non-default trunk, so a
parent bookmark can serve as the trunk without joining the stack.

```bash
GIT_DIR=<git-dir> gh stack add "<bookmark>"
```

Must run from the **top** layer of the stack (or the trunk while it is still empty); anywhere else
exits **5**. Exit 5 here means "you are not on the top", and moving there with `gh stack top` is a
decision, not a fix: it changes which layer the new bookmark is parented to. Whether that is correct
belongs to the caller — when a specific parent was named, it is not. `add` does not finish the
working-copy change, so working-copy files follow onto the new layer. There is no index.

```bash
GIT_DIR=<git-dir> gh stack submit --auto [--open]
```

`--auto` avoids a title prompt per new PR. `--open` creates PRs ready for review instead of drafts,
and also marks pre-existing drafts ready.

## Never

- **`gh stack link`** — GitHub-only by design, creates no local tracking, so a later
  `gh stack submit`, `gh stack view`, or `gh stack merge` will not see the layer. It exists for
  branches managed by external tools (jj, Sapling, git-town).
- **`gh pr merge`** on a stack member — it cannot merge a stack. Landing uses `gh stack merge`.
- **Bare `view` / `submit` / `init` / `add` / `checkout`** — each prompts or opens a TUI that
  blocks under a PTY. Always pass the arguments and flags shown above.

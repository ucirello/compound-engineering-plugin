# `gh stack` semantics this skill relies on

Verified against `gh stack version 0.1.0`. `gh stack <command> --help` is authoritative — if it
disagrees with anything here, follow `--help` and say so in your report. (`gh stack help <command>`
does not work; it prints top-level help.)

Only behavior that changes a decision in stack mode is listed. `gh stack` operates on exported Git branches, so run `jj git export` before each manager operation and `jj git import` after any operation that can move or create branches or change the checkout. Git terms below describe that provider boundary, not the repository workflow.

## Classifying a parent

```bash
gh stack checkout "<parent-pr-number>"
```

Resolve a parent by **PR number** whenever one exists — that is what pulls a stack down from
GitHub. A bare branch name resolves against **local** stacks only, so a branch-only parent can be
classified locally and no further.

Branch on the exit code; status text goes to stderr and must not be parsed.

| Exit | Meaning | What it means here |
|---|---|---|
| 0 | Success | Parent is in a stack; import the resulting checkout and branch state into Jujutsu |
| 2 | Not in a stack | Parent is standalone; nothing was checked out or fetched |
| 5 | Invalid arguments | Fix the invocation; see `--help` |
| 6 | Disambiguation required | Branch is in several stacks — check out a non-shared branch |
| 9 | Stacked PRs unavailable | Not enabled on this repository; tell the user and stop |

```bash
gh stack view --json    # JSON on stdout: trunk, currentBranch,
                        # branches[] { name, head, base, isCurrent, isMerged, needsRebase,
                        #              pr { number, url, state } }
```

`base` is the parent Git commit ID the branch was last known to contain, not the parent's current tip;
`needsRebase` is true when that tip is no longer an ancestor. There is no field naming the top of
the stack and no documented branch ordering, so do not derive position from this payload — use
`add`'s exit 5 instead.

## Resolving a PR head

`gh pr view "<n>" --json headRefName,headRefOid,author` identifies the head. Import the commit into Jujutsu, then create or verify a bookmark at `headRefOid`; fetch the PR ref through GitHub interoperability when the commit is unavailable locally.

## Building

```bash
gh stack init [--base "<trunk>"] "<branch>"...
```

Processes exported branches bottom to top and checks out the **last** one. Existing exported branches are adopted; missing ones are created. Import the result before further Jujutsu operations.
There is no separate adopt mode: existence decides. `--base` selects a non-default trunk, so a
parent branch can serve as the trunk without joining the stack.

```bash
gh stack add "<branch>"
```

Must run from the **top** exported branch of the stack (or the trunk while it is still empty); anywhere else exits **5**. Exit 5 means "you are not on the top", and moving there with `gh stack top` is a decision because it changes the parent. Without `-Am`, `add` does not alter file content. Import its branch topology before continuing.

```bash
gh stack submit --auto [--open]
```

`--auto` avoids a title prompt per new PR. `--open` creates PRs ready for review instead of drafts,
and also marks pre-existing drafts ready.

## Never

- **`gh stack link`** — creates no manager-local tracking, so later stack operations will not see the layer.
- **`gh pr merge`** on a stack member — it cannot merge a stack. Landing uses `gh stack merge`.
- **Bare `view` / `submit` / `init` / `add` / `checkout`** — each prompts or opens a TUI that
  blocks under a PTY. Always pass the arguments and flags shown above.

# Repository context, bookmark, and PR state

Gather this before Step 1. Run each command as its own argv-style shell call. Do not join probes with shell operators, substitutions, pipes, or redirects; separate calls work in POSIX shells, Git Bash, and PowerShell, and expose each exit status.

| Command | Purpose | Non-zero or empty result |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not in a JJ workspace; use description-only API fallback or report and stop |
| `jj status` | Working-copy change and conflicts | Repository unavailable |
| `jj diff` | Current change content | Empty means no current diff |
| `jj log -r ::@ -n 10` | Recent local history | No useful history |
| `jj bookmark list --all-remotes` | Local and remote bookmark state | Bookmark state unknown |
| `jj git remote list` | Named Git remotes and URLs | Remote state unknown |
| `gh repo view --json nameWithOwner,defaultBranchRef` | Base repository and provider default branch | Resolve from known remote bookmarks or ask; do not guess before mutation |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for the publish bookmark | Exit 0 with `[]` means none; non-zero means unknown |

Use `jj bookmark list -r <revision>` to determine which local bookmark points to a change. Do not infer a current branch from Git `HEAD`: JJ workspaces edit changes, and bookmarks do not automatically follow the working-copy change.

For a fork, run the PR query against the base repository with `-R <base-owner>/<repo>` and pass only `<bookmark>` to `--head`. Match `headRepositoryOwner` and `headRefName` to the selected push remote. Multiple or unconfirmed matches block mutation.

## Route the working state

- A feature bookmark already identifies the intended publish line: continue.
- Work based directly on the default bookmark without a feature bookmark: derive a feature bookmark name from the outcome and let Step 3 place it on the final intended change.
- No current diff and no unpublished changes beyond the default remote bookmark: report no feature work and stop.
- Divergent changes, conflicted bookmarks, conflicted working-copy changes, or an unresolved remote base: surface the state and stop rather than selecting a head or rewriting history.

Everything here is a snapshot. Immediately before push, re-run `jj status`, `jj bookmark list --all-remotes`, and `jj git remote list`. Immediately before PR creation, repeat the exact `gh pr list` query.

## Message and title conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Project instructions already in runtime context win, followed by recent repository history. Apply compatible Go quality guidance only: a concise summary line and an explanatory body when motivation or behavior is not obvious. Derive any prefix, type, scope, capitalization, mood, and body shape dynamically; do not default to a fixed convention.

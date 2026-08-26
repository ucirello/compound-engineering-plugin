# Repository context, bookmark, and PR state

Gather this before Step 1, then re-verify bookmark, remote, and PR state immediately before the push in Step 3 and `gh pr create` in Step 5.

Run each command as its own argv-style shell call. Do not join calls with shell operators, pipes, substitutions, or redirects. Read each exit status directly; non-zero is state to interpret.

| Command | Purpose | Non-zero or empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ workspace; stop |
| `jj status` | Working-copy state | Not a JJ workspace; stop |
| `jj diff` | Current working-copy change | Empty change |
| `jj log -r '@ | @-' --no-graph` | Current and parent change identity | Repository state unavailable |
| `jj bookmark list -r @` | Local bookmarks at the working-copy change | No bookmark targets `@` |
| `jj bookmark list --all-remotes` | Local and remote bookmark state | Remote state unavailable |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent change-description style | No local JJ history available |
| `jj git remote list` | Remote names and GitHub repository URLs | No usable GitHub remote; stop |
| `gh repo view <repository-url> --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Unavailable; inspect tracked remote bookmarks and ask rather than guessing |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark, once known | Exit 0 with `[]` means none. Non-zero means unknown and blocks creation until resolved |

Pass the bookmark name only to `--head`. On a fork workspace, target the base repository with `-R <base-owner>/<repo>`; do not use `<owner>:<bookmark>`, which can silently return `[]`. When multiple results share a bookmark name, match `headRepositoryOwner` and the exact API `headRefName`; stop if ownership cannot be resolved unambiguously.

## Step 1: resolve bookmark and PR state

JJ's working copy is a change, not a checkout of a bookmark. Determine whether a local bookmark already targets the work or one of its ancestors and whether it corresponds to the intended PR. If no feature bookmark exists and work is present, derive a non-conflicting name from the change content but create it only after the completed change target is known. If the work is empty and only the default bookmark is relevant, report no feature work and stop.

Resolve the default bookmark from `gh repo view`; if unavailable, use an unambiguous tracked remote default. Ask rather than inventing a default. A feature bookmark may not overwrite or move an unrelated existing bookmark.

Run the existing-PR check only after `<bookmark>` is known. Record the matching URL and body. Step 5 routes on the URL and Step 4 uses the body as rewrite context.

## Step 2: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Project instructions and runtime `git log` syntax win. PR titles follow the project's observed title conventions independently of the JJ change description.

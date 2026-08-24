# Repository context, change, bookmark, and PR state

Gather this before Step 1, and re-verify change, bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call: one program and its arguments. Do not join probes with shell operators, pipes, substitutions, or redirects. Read each exit status directly; a non-zero exit is state to interpret, not a failure to suppress.

Run them in order. The existing-PR check needs the publication bookmark chosen from the bookmark list and change topology:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj root` | Workspace root | Not a Jujutsu repository: use the current directory only as the local `.tmp` root; full change/push mode reports and stops |
| `jj status` | Working-copy change and conflicts | Outside a repository or unreadable state |
| `jj diff` | Current change content | Empty output means the current change has no content |
| `jj log -r @ -T builtin_log_compact` | Current change identity and description | Current change cannot be resolved |
| `jj log -r 'latest(::@, 10)'` | Recent description style and topology | No non-root history yet |
| `jj bookmark list --all-remotes` | Local and remote bookmark targets | No bookmarks or unavailable remote state |
| `jj git remote list` | Fetch and push remotes | No Git remote configured |
| `gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this branch (run only once `<branch>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<branch>` with the publication bookmark's same-named Git branch, and pass the **name only**. Two traps:

- **No publication bookmark:** skip the PR check entirely. `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates the bookmark.
- **Fork checkout:** do **not** pass `<owner>:<branch>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot. Re-verify the change, bookmark target, remote bookmark, and existing PR immediately before push and PR creation.

## Step 1 detail: resolve publication state

Resolve the base from `trunk()` when it names one unambiguous remote-backed change. Use `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` only to identify GitHub's base branch when needed. If the two disagree, repository instructions and explicit user intent decide; otherwise stop rather than guessing. An exit-0 empty PR array means no open PR for the bookmark. A non-zero result means unknown and must be resolved before creation.

Change and bookmark routing:

- **Working change has content or an unpublished described ancestor:** continue and ensure one feature bookmark points to the intended head before push.
- **Current change is an empty child of completed unpublished work:** publish the completed parent change, not the empty working-copy change.
- **Only trunk is present and there is no work:** report no feature work and stop.
- **A candidate bookmark is conflicted, ambiguous, or points to a different change:** stop or ask; never move it by inference.

If the PR check returned results, do **not** blindly take index 0. Select the entry whose head owner and branch match the push remote and publication bookmark. Stop on ambiguity. Note the URL and body from that entry. Step 5 routes by URL, and Step 4 uses the existing body as preservation context.

## Step 2 detail: description conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository instructions and the syntax established by `git log` always win. Where compatible, apply Go's quality guidance: describe the effect clearly, make the first line useful in history, and use a body when rationale or consequences are not evident. Do not impose a fixed type, scope, prefix, capitalization, punctuation, subject form, or body layout that the repository does not use. Apply the repository's title convention separately to PR titles.

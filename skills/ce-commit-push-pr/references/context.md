# Repository context, bookmark, and PR state

Gather this before Step 1, and re-verify bookmark, remote, and PR state immediately before each consequential step: the push in Step 3 and `gh pr create` in Step 5.

Run every command below as its own shell tool call. Do not join probes with shell operators, substitutions, pipes, or redirects. Read each exit status directly; a non-zero exit is a state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace; report and stop for VCS-changing modes |
| `jj status` | Working-copy change, parent, conflicts, and bookmark conflicts | Outside a workspace |
| `jj diff` | Current working-copy diff | Empty output means no content in `@` |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent description style and ancestry | No usable history |
| `jj log -r 'heads(::@ & bookmarks())' --no-graph -T 'json(local_bookmarks) ++ "\n"'` | Closest local bookmarks behind `@` | No local bookmark identifies the current line |
| `jj log -r 'heads(::@ & remote_bookmarks())' --no-graph -T 'json(remote_bookmarks) ++ "\n"'` | Closest remote bookmarks behind `@` | No remote bookmark identifies the current line |
| `jj git remote list` | Git remotes available to Jujutsu | No Git remote is configured |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | GitHub default branch name (`<base>`) | Provider/auth/connectivity unavailable; resolve from tracked remote bookmarks or ask |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for the feature bookmark | Exit 0 with `[]` = no open PR. Non-zero = unknown; re-check before creating |

Run the PR query only after `<bookmark>` is known, and pass the bookmark name only. An unnamed working-copy change skips the PR query until Step 3 creates its feature bookmark. On a fork, target the base repository with `-R <base-owner>/<repo>` because `gh pr list --head` does not accept `<owner>:<bookmark>`.

Everything gathered here is a snapshot. Immediately before an action they guard, separately re-run `jj bookmark list <bookmark>` for the local target, `jj log -r 'remote_bookmarks(exact:"<bookmark>")' --no-graph -T 'json(remote_bookmarks) ++ "\n"'` for remote targets, `jj git remote list`, and the existing-PR query.

## Step 1 detail: resolve bookmark and PR state

Treat the provider's default branch as the default bookmark name. Resolve its tracked remote targets with `jj log -r 'tracked_remote_bookmarks(exact:"<base>")' --no-graph -T 'json(remote_bookmarks.filter(|b| b.tracked())) ++ "\n"'`; accept the default only when exactly one matching remote bookmark identifies `<base>@<remote>`. If provider resolution fails, use a uniquely identifiable tracked remote bookmark that the project's active conventions designate as default; otherwise ask rather than guessing.

Bookmark routing:

- **Unnamed work based on the default bookmark**: derive a feature bookmark name from the change and continue. Step 3 creates it at the completed top commit. Do not ask whether to create it because the requested full workflow already authorizes a pushable PR head.
- **Default bookmark with work**: do not push the default bookmark. Continue through `references/bookmark-creation.md`, then create the feature bookmark in Step 3.
- **Default bookmark with no work and no unpublished descendants**: report no feature work and stop.
- **Feature bookmark in the ancestry of `@`**: continue with that bookmark.
- **Ambiguous or conflicting bookmarks**: stop and ask rather than selecting or moving one.

Only an exit-0 `[]` from the base-repository PR query means no open PR. With results, match both `headRepositoryOwner` and `headRefName` to the head this workflow can push. If exactly one entry matches, retain its URL and body. If ownership cannot disambiguate multiple matches, stop instead of acting on the wrong PR.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime conventions and recent repository history win over generic guidance for commit descriptions and PR titles. Apply only compatible Go quality guidance, and do not impose a fixed message prefix, type, scope, or template.

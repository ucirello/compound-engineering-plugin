# Workspace context, bookmark, and PR state

Gather this before Step 1 and re-verify before each push or `gh pr create`. Run each command as its own argv-style shell call and interpret non-zero status as state.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj root` | Workspace root | Not a JJ workspace; stop |
| `jj status` | Working-copy state | Not a JJ workspace; stop |
| `jj diff` | Current changes | No file changes |
| `jj bookmark list -r @ -T 'name ++ "\n"'` | Bookmarks on `@` | No attached bookmark |
| `jj bookmark list -r 'heads(::@ & bookmarks())' -T 'name ++ "\n"'` | Nearest ancestor bookmarks | No unique ancestor bookmark |
| `jj log -r ::@ -n 10` | Local description style | No meaningful history |
| `jj git remote list` | Configured remote names and URLs | No configured remote |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Lookup unavailable; inspect remote bookmarks |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR | Exit 0 with `[]` means none; non-zero means unknown |

Pass the uniquely selected bookmark name only. With no bookmark, skip the PR query because an empty `--head` lists unrelated PRs. On a fork, target the base repository with `-R` rather than passing `<owner>:<bookmark>`, which `gh pr list --head` does not support.

## Step 1 Detail

Use the default bookmark from `gh repo view`. If unavailable, inspect `jj bookmark list --all-remotes` and use only a uniquely identifiable default. Resolve the remote whose URL owns the base repository; stop if no unique configured remote matches.

- **No attached bookmark** - if the unique nearest ancestor is the default, derive a feature bookmark and let Step 3 root it safely. Otherwise create the derived bookmark at `@`. Stop on ambiguous ancestry.
- **Default bookmark with work** - derive a feature bookmark and let Step 3 root it safely.
- **Default bookmark without work** - report no feature work and stop.
- **Feature bookmark** - continue.

For a non-empty PR result, match `headRepositoryOwner` and `headRefName` to the remote and bookmark being pushed. Never select index 0 blindly. Stop when ownership cannot disambiguate matches. Preserve the selected URL and body for Steps 4-5.

## Step 2 Detail

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe any fixed syntax or example. Derive PR titles independently from project PR conventions and the change outcome.

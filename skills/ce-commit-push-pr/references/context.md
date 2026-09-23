# Repository context, bookmark, and PR state

Run each probe as its own argv-form call and interpret its exit status. Resolve the absolute workspace root with `jj workspace root` from the known checkout; set that absolute root as cwd for every subsequent JJ subprocess, never substituting `-R`. Use only public JJ commands, never repository internals or filesystem identity. If workspace membership matters, use `jj workspace list` and `jj workspace root --name <name>`.

Before every `gh` call, obtain `jj git root` in this workspace and set the returned value as the call's `GIT_DIR` environment variable. This is the portable equivalent of `GIT_DIR=$(jj git root)`; use the host's environment facility, not POSIX substitution on a non-POSIX host. Pass the base repository explicitly with `-R <base-owner>/<repo>` on fork operations. Description-only and update modes must also perform this setup.

| Command | Purpose | Failure meaning |
| --- | --- | --- |
| `jj workspace root` | Absolute workspace root | Outside JJ: report and stop |
| `jj status` | Working-copy and conflict state | Unknown state: stop |
| `jj diff` | Current change's content | Unknown content: stop |
| `jj log -r '@ \| @-'` | Current change and parent | Do not infer a head if unresolved |
| `jj bookmark list --all-remotes` | Feature bookmarks and tracking state | Unknown destination: stop |
| `jj log -r 'ancestors(@, 10)'` | Recent commit and title conventions | Report if history unavailable |
| `jj git remote list` | Head and base repository mapping | Resolve missing remote before publishing |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Default branch | Resolve from verified project context or ask; pipeline stops rather than guesses |
| `gh pr list -R <base-owner>/<repo> --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Existing PR for resolved bookmark | Only exit-0 `[]` means none; non-zero is unknown |

## Step 1: Resolve the intended head and PR

JJ has no current Git branch or staging index. Choose the intended feature bookmark from invocation, verified local/remote bookmarks, and work ancestry. Inspect both `@` and `@-`: after a commit, `@` may be an empty child while the publishable head and bookmark are at `@-`. If `@` holds excluded or unrelated work, the publishable head is the selected committed ancestor, never that remainder. Do not create a duplicate bookmark merely because `@` is empty. If multiple candidates remain, stop and ask; pipeline reports the ambiguity.

- **No feature bookmark with publishable work:** derive a non-conflicting feature name from the change and create it at the verified intended revision. No branch-confirmation question is needed.
- **Default bookmark with work:** use `references/branch-creation.md`; do not move or publish the default bookmark.
- **Default bookmark with no work:** report no feature work and stop.
- **Existing feature bookmark:** retain it, verifying ownership and destination before moving it.

Never query with an empty head. Pass the branch name only: `--head <owner>:<branch>` silently returns `[]`. The PR lives in the base repository, not necessarily the head remote. Match results by both `headRepositoryOwner` and `headRefName`; never take index 0 without matching. Stop on ambiguity and show candidates. Keep the matching URL and body for Steps 4 and 5.

Probe output is a snapshot. Re-check the intended revision, bookmark, remote, and PR immediately before push and creation. Resolve non-zero PR checks through authentication/connectivity evidence; they never authorize creation.

## Step 2: Conventions

Read https://go.dev/wiki/CommitMessage before composing or validating messages.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Here `git log` refers to history inspected with `jj log` for this JJ workflow; never execute Git. Runtime project instructions and visible history override Go-specific syntax. Match PR titles to those project conventions too; do not impose a fixed prefix or template.

# Committing the refresh

Skip if no files changed. Use `jj status`, `jj diff`, the current bookmarks, the remote default bookmark, and recent history to distinguish this refresh from unrelated working-copy changes. JJ snapshots the working copy and has no staging area; commit only the refresh files by passing their dynamically resolved filesets to `jj commit`, leaving every other change in the new working-copy commit.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Compose the change description from the actual actions and local conventions. Go guidance supplies only compatible quality criteria; the local runtime syntax and observed repository style win. Do not impose a fixed syntax, example, or template, and preserve dynamic names and values as placeholders until the repository state resolves them.

Non-interactive defaults: when the refresh starts directly from the provider's remote default bookmark, create a dynamically named local bookmark at the committed revision, push that bookmark with `jj git push --bookmark <bookmark> --remote <remote>`, and attempt a pull request with `gh`; if PR creation fails, report the bookmark. When the refresh belongs to existing feature work, keep it as a separate JJ change in that stack, advance the applicable bookmark to the committed revision when needed, and push that bookmark. A failed JJ, provider, or GitHub operation becomes a recommendation containing the state and dynamically resolved recovery command, and the run continues.

Interactive mode asks, with the recommendation first, whether to use the applicable bookmark-and-PR path, keep the change on the current stack, create a separate bookmark, or leave it uncommitted. The choices depend on the current JJ graph and bookmark state rather than Git branch or dirty-tree categories.

Use `jj git fetch` and `jj git push` for Git remote synchronization. In a colocated repository, JJ and Git synchronize automatically, so provider tooling and a necessary Git command may run side-by-side; after an exceptional direct Git mutation, let the next JJ command import it or run `jj git import`. In a non-colocated repository, resolve the backing Git directory with `jj git root` for `gh` when required and use `jj git export` before a Git-only consumer needs updated refs. On Windows, use the active shell's native environment-assignment syntax; Git Bash is supported, but do not emit Git Bash syntax into another shell.

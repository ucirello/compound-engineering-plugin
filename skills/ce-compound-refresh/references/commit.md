# Committing the refresh

Skip if no files changed. Check the current bookmark (`jj status` / `jj bookmark list`), whether `@` has unrelated edits, and recent change-description style (`jj log`). JJ has no index: working-copy files are already in `@`. Finish **only** the files this refresh modified with `jj commit -- <paths>` (or `jj describe` when the change is already isolated to those paths). Never invent a staging step.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repo-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing local syntax.

Preserve these constraints on the composed message: it summarizes the refresh — what was updated, consolidated, replaced, or deleted — in the repo's convention.

```bash
(cd "$workspace_root" && jj commit -- <refresh-paths> -m "<message composed from the standards above>")
```

Or, when the working-copy change is already only those files:

```bash
(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")
```

`$workspace_root` is `jj workspace root`. Run every `jj` command with cwd at that root.

Non-interactive defaults: on the repo's default bookmark (`main`, `master`, `trunk`, or whatever the remote designates as `main@origin` / `trunk@origin`) → `jj bookmark create <name>` named for what was refreshed (e.g., `docs/refresh-auth-learnings`), `jj commit -- <refresh-paths> -m "<message composed from the standards above>"`, `jj git push --bookmark <name>`, attempt a PR with `GIT_DIR=$(jj git root) gh pr create` (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark (`jj commit -- <refresh-paths> -m "<message composed from the standards above>"`); jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / finish the change on the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: `jj commit -- <refresh-paths>` only refresh files / don't commit. "Don't commit" leaves the edits in `@` without `jj commit` and without creating a shipping bookmark.

# Committing the refresh

Skip if no files changed. Check the current bookmark (`jj bookmark list -r @`), whether the working copy has unrelated changes (`jj status` / `jj diff`), and recent change-description style (`jj log`). Include **only** the files this refresh modified in the change — leave unrelated working-copy edits out of it. Jujutsu auto-snapshots tracked files; untracked paths may need `jj file track`.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from the Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax.

The description must summarize the refresh: which docs were updated, consolidated, replaced, or deleted. Those are constraints on the dynamically composed message — do not use a fixed subject, prefix, type, scope, or template.

Describe the current change with:

```bash
jj describe -m "<message composed from the standards above>"
```

When the workflow should finish this change and start a new one:

```bash
jj commit -m "<message composed from the standards above>"
```

Non-interactive defaults: on the repo's default bookmark (`trunk()`, typically main, master, or whatever the remote designates) → `jj new` from that base, then `jj bookmark create <name> -r @` named for what was refreshed (e.g., `docs/refresh-auth-learnings`), describe/commit, attempt a PR with `GIT_DIR="$(jj git root)" GIT_WORK_TREE="$(jj workspace root)" gh` (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark; jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / describe the current change / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature working copy: include only refresh changes in this change / don't commit.

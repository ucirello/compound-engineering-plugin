# Committing the refresh

Skip if no files changed. Check the current bookmark, whether the working copy has unrelated changes, and recent change-description style. Include **only** the files this refresh modified in the change (the working copy is the change; when unrelated changes are present, `jj commit` with those filesets keeps the refresh paths in the current change and moves the rest to a new working-copy change on top).

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in git log, compose commit messages adherent to the present standards.

Then: repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax.

The description covers the refresh (what was updated, consolidated, replaced, or deleted) under those standards — not a fixed prefix, type, scope, or subject template. Apply with:

```
jj describe -m "<message composed from the standards above>"
```

When unrelated working-copy changes must stay out of this change, use `jj commit -m "<message composed from the standards above>"` with the refresh filesets instead.

Non-interactive defaults: on the repo's default bookmark (main, master, or whatever the remote designates) → `jj new` plus `jj bookmark set` named for what was refreshed (e.g., `docs/refresh-auth-learnings`), describe the change, attempt a PR (pair `gh` with `GIT_DIR=$(jj git root)`; if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark; jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+describe+PR (recommended; specific bookmark name) / describe the current change in place / don't describe. On a clean feature bookmark: describe it (recommended) / separate bookmark / don't describe. On a dirty feature bookmark: `jj commit` with only refresh filesets / don't describe.

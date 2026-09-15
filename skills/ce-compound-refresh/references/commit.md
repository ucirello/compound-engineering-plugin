# Describing the refresh change

Skip if no files changed. Check the bookmarks on `@`, whether the working copy has unrelated changes, and recent change-description style. The working copy is the change — do not stage. Isolate the refresh so the described change contains only the files this run modified.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repo-local syntax.

The description must summarize the refresh: which learnings were updated, consolidated, replaced, or deleted. Do not use a fixed subject, prefix, type, scope, or template. Set it with `jj describe -m "<message composed from the standards above>"` (or `jj commit -m "<message composed from the standards above>"` when the workflow needs a new empty change on top).

Non-interactive defaults: on the repo's default bookmark (main, master, or whatever the remote designates) → if `@` carries that bookmark, create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`) on `@` and move the default bookmark back to `@-`, describe the change, `jj git push --bookmark <name>`, attempt a PR with `GIT_DIR=$(cd "$(jj workspace root)" && jj git root)` on `gh` (if PR creation fails, report the bookmark name); on a feature bookmark → describe a separate change on that bookmark; jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: new bookmark + describe + PR (recommended; specific bookmark name) / describe on the current bookmark / don't describe. On a clean feature bookmark: describe on it (recommended) / separate bookmark / don't describe. On a working copy that also has unrelated changes: isolate and describe only refresh changes / don't describe.

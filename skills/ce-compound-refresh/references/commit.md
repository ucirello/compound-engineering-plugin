# Committing the refresh

Skip if no files changed. Check the current bookmark (`jj bookmark list -r @` or `jj log -r @ -T 'bookmarks ++ "\n"' --no-graph`), whether the working copy has unrelated changes (`jj status`), and past commit messages.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing local syntax.

Include **only** the files this refresh modified in the change. The message should summarize what was refreshed (how many docs were updated, consolidated, or deleted) as constraints, not as a fixed template. The working copy is already the change. When the working copy also holds unrelated edits, pass only the refresh paths to `jj commit`; otherwise describe or commit the current change:

```
jj commit -m "<message composed from the standards above>"
```

```
jj commit path1 path2 -m "<message composed from the standards above>"
```

Non-interactive defaults: on the repo's default bookmark (main, master, or whatever the remote designates) → create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`) with `jj bookmark create NAME` on the refresh change (if the default bookmark also points here, move it to the parent so the work lives only on the new bookmark), describe/commit, attempt a PR with `GIT_DIR=$(jj git root)` so `gh` sees the colocated git store (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark; jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / commit directly to the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: include only refresh files in the change / don't commit.

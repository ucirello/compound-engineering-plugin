# Committing the refresh

Skip if no files changed. Check the current bookmark, whether the working copy has unrelated changes, and recent description style. There is no staging area: name **only** the files this refresh modified on `jj commit`.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing repo-local syntax. Determine the syntax at runtime from those sources. Keep the semantic constraint that the description summarizes the refresh (how many docs were updated, consolidated, or deleted). Do not impose a fixed type, scope, prefix, footer, or body template.

Example:

```bash
jj commit -m "<message composed from the standards above>" file1 file2
```

Non-interactive defaults: on the repo's default bookmark (main, master, or whatever the remote designates) → create a bookmark named for what was refreshed, commit, attempt a PR (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark; jj failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / commit on the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: named-fileset commit of only refresh changes / don't commit.

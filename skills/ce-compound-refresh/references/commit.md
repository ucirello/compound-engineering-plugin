# Committing the refresh

Skip if no files changed. Inspect `jj status`, bookmarks, and recent history with `jj log`, using the absolute workspace root as cwd. Isolate only the refresh changes in a revision; JJ has no staging area. Preserve unrelated changes, including unrelated hunks in the same file, using a selective split when needed.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Here `git log` refers to history inspected using `jj log` in this JJ workflow. Read the linked guidance before composing the message. Runtime project instructions and observed history syntax override Go guidance. The message summarizes the refresh and its reasons.

Non-interactive defaults: on the default line of development -> create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), commit, publish with `jj git push`, and attempt a PR (if PR creation fails, report the bookmark name); on a feature bookmark -> separate revision on that line and advance its bookmark. If `@` is empty, inspect `@-` for the completed revision and bookmark/PR target. Run `gh` with `GIT_DIR` set to the result of `jj git root` in the correct workspace. JJ failures -> put recommended commands in the report and continue; any message argument is `<message composed from the standards above>`.

Interactive: ask (per Blocking questions), with the recommended option first. On the default line: bookmark+commit+PR (recommended; specific bookmark name) / commit directly to the current line / don't commit. On a feature line without unrelated changes: commit to it (recommended) / separate bookmark / don't commit. With unrelated working-copy changes: selectively isolate and commit only refresh changes / don't commit.

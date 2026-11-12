# Committing the refresh

Skip if no files changed. From the verified absolute target workspace root, inspect `jj status`, conflicts, bookmarks, and the task's actual history head (including `@-` when `@` is empty). Never use `-R` as a cwd substitute or run the Git executable. Preserve unrelated tracked, ignored, and untracked work.

Before composing any commit message, read the full https://go.dev/wiki/CommitMessage guide and several recent full subjects **and bodies** with `jj log --no-graph -r 'ancestors(<verified-task-history-head>)' -n 10 -T 'description ++ "\n---\n"'`. Compare repository prefixes, casing, tense, body layout, wrapping, and issue references. Project instructions and actual history syntax always win; use only compatible Go quality guidance and invent no precedent.

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Describe only the owned refresh changes with `jj describe -m "<message composed from the standards above>"`. Its body, and the PR body when present, lists each worth-based cut/Delete and standards change with quoted evidence. No fixed message template, Conventional type/scope, creator/model/harness byline, Co-authored-by, or Assisted-by trailer. Include an owned changed `CODING_STANDARDS.md`.

JJ has no staging area: if unrelated changes share `@`, use path-limited `jj split` after checking its current help to isolate only the refresh-owned paths, preserving all other work. If ownership cannot be separated safely, stop the commit operation and report the blocker. Never describe or publish unrelated changes as part of the refresh. Capture and verify the resulting commit ID and exact bookmark target before push/PR actions.

Non-interactive defaults: on the verified default bookmark, create a meaningful refresh bookmark and a separate owned change, then attempt the authorized push and PR; on a feature bookmark, make a separate owned commit there. Preserve the semantic scope and use `jj bookmark create/set` and `jj git push --bookmark <verified-name>` as appropriate after verifying authority. If PR creation fails, report the bookmark name. JJ failures put recommended JJ-native commands in the report and continue, never a Git fallback. Repository-scoped `gh` runs from the target root with `GIT_DIR=$(jj git root)`.

Interactive: ask per Blocking questions, recommended option first. On the default bookmark: bookmark+commit+PR / commit directly / don't commit. On a clean feature bookmark: commit there / separate bookmark / don't commit. With unrelated changes: isolate only owned refresh changes / don't commit. No approval implies authority for unrelated rewrites or publishing.

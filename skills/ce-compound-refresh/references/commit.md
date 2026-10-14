# Commit

Skip if no files changed. From the target workspace's absolute root, inspect `jj status`, `jj diff`, and bookmarks to identify the current change, unrelated work, and verified default remote bookmark. Isolate only refresh-owned paths with `jj split <refresh-paths>` when mixed with unrelated changes; if a file contains both, select only owned hunks interactively where allowed, otherwise report the blocker without capturing unrelated work. Never discard unrelated changes or conflicts.

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.** Before composing, read the full Go guide and compare several recent subjects AND bodies using `(cd "$workspace_root" && git --git-dir="$(jj git root)" log -10 --format=%B)`. This is a read-only backend inspection. Establish actual prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and history always win over differing Go syntax; apply compatible guidance for clarity and structure. If history is absent, use explicit project/user instructions and Go guidance without inventing precedent. Describe the refresh actions and counts, affected documents, and relevant issue references without imposing a fixed subject format.

Source guidance from https://go.dev/wiki/CommitMessage, not a mandatory repository template:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

Describe the isolated revision with `(cd "$workspace_root" && jj describe -r <verified-refresh-change> -m "<message composed from the standards above>")`; create a fresh working-copy child with `jj new <verified-refresh-change>` when appropriate. Run every JJ command from that absolute root. Use local `.tmp/` for any message or report temporary files.

Non-interactive defaults: on the verified default bookmark → create a unique bookmark named for what was refreshed, record the refresh, push that bookmark and attempt a PR; on a feature bookmark → a separate refresh change on that bookmark. Keep existing source bookmarks unchanged when creating a separate bookmark. Use `jj bookmark create <name> -r <refresh-change>` or deliberately advance the verified feature bookmark with `jj bookmark set <name> -r <refresh-change>`, then `jj git push --bookmark <name>` within authorized push scope. Repository-scoped PR calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr create ...)`. If PR creation fails, report the bookmark; JJ or permission failures → include recommended commands in the report and continue without retrying denied operations.

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: separate bookmark+change+PR / record directly on the current bookmark / don't commit. On a clean feature bookmark: record there / separate bookmark / don't commit. With unrelated work: isolate only refresh changes / don't commit. Preserve existing consent boundaries.

JJ command reference: https://docs.jj-vcs.dev/latest/cli-reference/ ; Git-to-JJ mapping: https://docs.jj-vcs.dev/latest/git-command-table/ .

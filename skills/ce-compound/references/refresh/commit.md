# Committing the refresh

Skip if no files changed. From the absolute target workspace root inspect bookmarks, `jj status` and `jj diff` for unrelated changes. Commit **only** the refresh-owned paths, including a `CODING_STANDARDS.md` this refresh changed; use JJ's path-scoped commit operation and preserve all unrelated work. Compose a descriptive message summarizing the refresh under the standards below, never a fixed template. Its body, and the PR body when present, lists each worth-based cut or Delete and each standards change with quoted evidence.

Non-interactive defaults: resolve the repository's actual default bookmark and exact head; do not guess. On that bookmark create a distinct refresh bookmark, make a separate path-scoped JJ commit and attempt the authorized push/PR; if PR creation fails report the bookmark. On a feature bookmark make a separate refresh commit and move only that verified bookmark. JJ failures put recommended native JJ commands in the report and continue. Before repository-scoped `gh`, export `GIT_DIR=$(jj git root)` from the absolute workspace root. Use `jj git push` for transport, never direct Git. See https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: new bookmark+commit+PR / commit to current bookmark / don't commit. On a clean feature bookmark: commit to it / separate bookmark / don't commit. With unrelated work: path-scoped commit of only refresh changes / don't commit. Preserve unrelated changes and stop safely on conflicts or uncertain ownership.

## Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and inspect several recent subjects AND bodies from the target workspace's absolute root: `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Resolve that history head from the actual task/repository; do not hardcode a default remote or replace any reviewed base/head range with this style sample. Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository-local instructions and observed syntax always win over Go guidance; apply compatible guidance to clarity and structure within that syntax. Without history use explicit project/user instructions and Go guidance, not invented precedent. Neutral command placeholder: `jj describe -m "<message composed from the standards above>"`; preserve the intended commit operation and owned-path scope. Do not add branded/model/harness bylines.

The following verbatim source excerpts are illustrative guidance, NOT a mandatory repository template:

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

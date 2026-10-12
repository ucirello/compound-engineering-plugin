# Committing the refresh

Skip if no files changed. Resolve the target's absolute `workspace_root`; run every JJ command from it, for example `(cd "$workspace_root" && jj status)`. Inspect conflicts and unrelated work first. Commit only this refresh's changes using `jj commit <refresh-owned-paths> -m "<message composed from the standards below>"`; stop if a path contains inseparable unrelated edits rather than including or discarding them. Describe the supported maintenance actions and their counts without imposing message syntax.

Non-interactive defaults: resolve the remote's verified default bookmark and current feature bookmark. On the default line, create a refresh bookmark, commit, advance only that owned bookmark to the refresh revision, push using `jj git push --bookmark <verified-refresh-bookmark>`, and attempt a PR. On a feature line, make a separate refresh change and advance that feature bookmark only when authorized. If PR creation fails, report the bookmark. For repository-scoped `gh`, use `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`. JJ failures → put recommended commands in the report and continue, preserving all state.

Interactive: ask (per Blocking questions), with the recommended option first. On the default line: bookmark+commit+PR (recommended; specific bookmark name) / commit directly on the current line / don't commit. On a clean feature line: commit to it (recommended) / separate bookmark / don't commit. With unrelated dirty changes: commit only separable refresh-owned paths / don't commit.

## Message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and inspect several recent subjects AND bodies from the read-only JJ Git backend: `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue placement. Repository-local instructions and actual history always win over Go syntax; apply compatible Go guidance to clarity and structure. With no history, use explicit project/user instructions and Go guidance without inventing precedent. Never add model/harness attribution or coauthor footers.

The following verbatim Go source guidance is illustrative, not a mandatory repository template:

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

JJ command references: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/ .

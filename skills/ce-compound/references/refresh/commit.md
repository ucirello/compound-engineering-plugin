# Committing the refresh

## Source guidance, not a mandatory repository template

Repository-local instructions and the observed runtime history pattern take precedence over this illustrative Go example. Apply compatible quality guidance without imposing its package-prefix syntax.

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

Skip if no files changed. Check the verified bookmark and unrelated/conflicted changes from the absolute target workspace root. Commit **only** refresh-owned paths with JJ's explicit path selection, including any changed `CODING_STANDARDS.md`; do not absorb unrelated work. Read the full https://go.dev/wiki/CommitMessage guide, then compare several recent full subjects AND bodies from the actual relevant verified history head with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Analyze package/prefix, case/tense, separation, wrapping and issue placement. Project instructions/history syntax wins; apply compatible Go quality guidance. Without history use project/user instructions and Go, never invent precedent. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. The body and any PR body list worth-based cuts, Deletes and standards changes with quoted evidence. Use `jj describe -m "<message composed from the standards above>"` only for the verified owned revision.

Non-interactive defaults: on the verified remote default bookmark create a task-named bookmark for the owned revision, commit and attempt an authorized PR; on a feature bookmark create a separate owned commit. JJ failures produce recommended commands in the report. Never guess push authority or reset unrelated work. For repository-scoped `gh`, obtain `GIT_DIR=$(cd "$workspace_root" && jj git root)` and supply it to `gh`.

Interactive: ask (per Blocking questions), with the recommended option first. On the default branch: branch+commit+PR (recommended; specific branch name) / commit directly to the current branch / don't commit. On a clean feature branch: commit to it (recommended) / separate branch / don't commit. On a dirty feature branch: selective-stage and commit only refresh changes / don't commit.

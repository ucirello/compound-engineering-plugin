# Commit

Skip if no files changed. Resolve the absolute workspace root with `jj workspace root`; run every JJ command from that root, for example `(cd "$workspace_root" && jj status)`. Inspect the current change, bookmarks, conflicts, and unrelated working-copy changes. Record only refresh-owned files with `jj commit <refresh-owned-paths> -m "<message composed from the standards below>"`; paths must be workspace-relative, such as `docs/solutions/example.md`, not prefixed with a workspace directory. If unrelated edits share a file, isolate the refresh hunks safely before recording it, or leave the work intact and report the blocker. Never discard unrelated work.

Non-interactive defaults: on the verified remote default bookmark, create a separate refresh change and a meaningfully named bookmark, then attempt a PR; on a feature bookmark, add a separate change and advance only that verified bookmark. Verify the remote and push authority before `jj git push --bookmark <verified-bookmark>`. For repository-scoped GitHub CLI calls, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. If PR creation fails, report the bookmark name. JJ failures → put recommended commands in the report and continue without destructive recovery.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: separate bookmark+change+PR (recommended; specific bookmark name) / record directly on the current bookmark / don't commit. On a clean feature bookmark: record on it (recommended) / separate bookmark / don't commit. With unrelated dirty work: record only refresh changes / don't commit. Do not infer a bookmark from an empty `@`; inspect its parent and bookmark targets.

Use workspace-root `/.tmp/` for temporary material, ensure `.tmp` is ignored in `.gitignore`, and never fall back to OS-global temporary storage. JJ command guidance: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/git-command-table/ .

## Message composition

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing any message, read the full Go guide and examine several recent subjects AND bodies from the read-only Git backend: `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Compare prefixes or package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and history syntax always win over differing Go guidance; apply compatible guidance to clarity and structure, not to replacing local syntax. Without history, use explicit project/user instructions and Go guidance without inventing precedent. Describe the actual refresh actions and their scope; do not use a fixed subject template.

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

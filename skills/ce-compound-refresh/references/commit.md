# Committing the refresh

Skip if no files changed. Check the current bookmarks, whether the working-copy change has unrelated changes, and recent commit style. Record **only** the files this refresh modified: use `jj split` with explicit refresh paths if unrelated changes share `@`, preserving those changes. Describe the refresh's actions and counts without prescribing message syntax.

Non-interactive defaults: on the repo's default bookmark (main, master, or whatever the remote designates) → create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), describe the isolated refresh change, push that bookmark with `jj git push --bookmark <bookmark>`, and attempt a PR (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark and move the bookmark to it; JJ failures → put the recommended commands in the report and continue.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+change+PR (recommended; specific bookmark name) / record directly on the current bookmark / don't commit. On a clean feature bookmark: record on it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: isolate and record only refresh changes / don't commit.

Run every JJ command from the target workspace's absolute root, e.g. `(cd "$workspace_root" && jj status)`. For repository-scoped GitHub calls, use `(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh pr create ...)`. Temporary files, including error/fallback paths, belong under that workspace's `.tmp/` (local `.tmp/` outside JJ); ensure `.tmp/` is ignored. Native command references: https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ . Use `jj describe -m "<message composed from the standards below>"` on the isolated refresh change, not a fixed message template.

## Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing any description, read the full Go guide and compare several recent subjects **and bodies** using `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Establish the repository's actual prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and observed syntax always win; apply compatible Go guidance to clarity and structure without replacing that syntax. With no history, follow explicit project/user instructions and compatible Go guidance without inventing precedent.

The following are verbatim Go source guidance, not a mandatory repository template:

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

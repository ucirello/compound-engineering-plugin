# Describing the refresh

Skip if no files changed. From the absolute target JJ workspace root, inspect bookmarks, conflicts, unrelated changes, and the task's verified history head. Read the full https://go.dev/wiki/CommitMessage and multiple recent subjects **and bodies** using `jj log` anchored to that head, not hardcoded main.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

**Go source guidance — illustrative excerpts, not a repository template.** These verbatim SOURCE excerpts are subordinate to observed repository syntax and explicit project/user instructions. Read the full guide and compare history as required above; apply only compatible guidance.

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

Repository-local syntax wins. Compare package/prefix, casing, tense, subject/body structure, wrapping and issue references. Without history, use explicit project/user requirements plus compatible Go guidance; never invent precedent. The body and any PR body list each worth-based cut or Delete and standards change with its quoted evidence. Do not add authorship attribution.

Read complete descriptions, not the default log template or `description.first_line()`: from the absolute target root run `jj log --no-graph -r "ancestors($history_head)" -n 8 -T 'commit_id ++ "\n" ++ description ++ "\n---\n"'`, where `history_head` is the task's verified exact commit ID captured before describing the refresh. This includes subjects and bodies on that task's ancestry, not unrelated default-bookmark history.

Isolate only this refresh's files using native JJ split/commit selection when unrelated work exists; preserve all other work. Use `jj describe -m "<message composed from the standards above>"` on the verified refresh change. Run every JJ command with cwd set to the absolute workspace root. No staging or direct Git executable.

Non-interactive defaults: at the verified default bookmark, create a task-named bookmark for the refresh, describe the isolated change and attempt a PR only with established push authority; on a feature bookmark use a separate refresh change. On failure, report recovery commands and continue, without force or inferred authorization. Scope repository `gh` calls from the root with `GIT_DIR=$(jj git root)`.

Interactive: ask with the recommended option first: new bookmark + refresh change + PR, refresh change on the existing feature bookmark, or do not commit/publish. With unrelated work, offer selective JJ isolation or no commit. Do not create or retire workspaces here; retain existing isolation and session ownership.

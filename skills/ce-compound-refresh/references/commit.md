# Committing the refresh

Skip if no files changed. Inspect `jj status`, bookmarks and unrelated changes from the target workspace's absolute root. Commit **only** refresh-owned paths using `jj commit <owned-paths> -m "<message composed from the standards below>"`; inspect the resulting change and preserve all unrelated work. Do not stage, reset, or discard unrelated files. Resolve the actual default bookmark and task history head rather than assuming a branch name.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and compare several recent subjects AND bodies from the verified task history head, using `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Observe prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement. Repository-local syntax and project/user instructions always win; apply compatible Go advice for clarity and structure without inventing a fixed template. With no history, follow explicit instructions and compatible Go guidance without inventing precedent. Describe the actual refresh actions, affected docs, and relevant issues.

The following are verbatim Go source guidance, **not a mandatory repository template**:

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

Non-interactive defaults: on the verified default bookmark → create a bookmark named for the refresh, commit the owned paths, move that bookmark to the verified refresh commit, push with `jj git push --bookmark <verified-bookmark>`, and attempt a PR. Run repository-scoped GitHub commands as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr create ...)`. If PR creation fails, report the bookmark name. On a feature bookmark → create a separate refresh commit and advance that bookmark without including unrelated work. JJ/push failures → put recommended native JJ recovery commands in the report and continue; never use direct Git. See https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/.

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: separate bookmark+commit+PR / commit on the current bookmark / don't commit. On a clean feature bookmark: commit to it / separate bookmark / don't commit. With unrelated changes: commit only refresh-owned paths / don't commit. If owned and unrelated edits overlap and cannot be safely separated, stop for a decision rather than including or discarding user work.

# Commit

Skip if no files changed. Run every JJ command from the target workspace's verified absolute root, for example `(cd "$workspace_root" && jj status)`. Inspect current bookmarks, conflicts and unrelated work. Commit only this refresh's paths with `jj commit <owned-paths> -m "<message composed from the standards above>"`; do not absorb unrelated edits, including edits sharing a path. If those cannot be separated safely, report the blocker rather than discard them.

## Message standards

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards."

Before composing or editing a description, read the full https://go.dev/wiki/CommitMessage at runtime. Resolve the actual history head relevant to this task, then examine several recent full subjects AND bodies from the absolute target root, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement. Repository-local syntax from project instructions and history always wins; apply only compatible Go quality guidance. With no history, use explicit project/user instructions and Go guidance without inventing precedent. Describe the refresh's actual actions and scope, including relevant issue references, without a fixed syntax.

Verbatim excerpts from https://go.dev/wiki/CommitMessage (the Go example is source guidance, not a mandatory repository template):

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

## Mode decisions

Non-interactive defaults: on the verified default bookmark (main, master, or the remote-designated default), create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), commit, push that bookmark with `jj git push --bookmark <verified-bookmark>`, and attempt a PR. For repository-scoped `gh`, from the absolute target root first `export GIT_DIR=$(jj git root)`. If PR creation fails, report the bookmark name. On a feature bookmark, create a separate change on that bookmark and advance it to the verified refresh commit. JJ failures put recommended commands in the report and continue; never use a Git fallback.

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: new bookmark+commit+PR (recommended; specific bookmark name) / commit directly on the current bookmark / don't commit. On a clean feature bookmark: commit on it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: commit only safely separated refresh changes / don't commit. Preserve existing authorization and never guess an ambiguous bookmark or remote.

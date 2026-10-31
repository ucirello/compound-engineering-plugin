# Committing the refresh

Skip if no files changed. Resolve the absolute workspace root with `jj workspace root`, then run every JJ command from that root. Check `jj status`, conflicts, current bookmarks, the verified remote default bookmark, and unrelated changes. Commit **only** this refresh's paths using `jj commit <owned-paths> -m "<message composed from the standards above>"`; never include unrelated edits or whole mixed-ownership files. If file-level isolation is insufficient, stop and report rather than incorporating unrelated content.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide and several recent complete subjects AND bodies at the actual verified relevant history head: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Compare prefixes/package names, case, tense, subject/body separation, wrapping, and issue placement. Project/user instructions and observed repository syntax ALWAYS win; apply compatible Go guidance within that pattern. With no history, use explicit instructions and Go guidance without inventing precedent. Describe the refresh's actual actions and scope, not a fixed message template. To edit a description use `(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")` on the verified owned change.

The following verbatim Go excerpts are source guidance, not a mandatory repository template:

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

Non-interactive defaults: on the verified default bookmark → create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), commit, move only that owned bookmark to the resulting commit, push with `jj git push --bookmark <verified-bookmark>`, and attempt a PR; report its bookmark if PR creation fails. On a feature bookmark → a separate refresh commit on that bookmark, preserving unrelated work. JJ failures → put recommended commands in the report and continue, never fall back to Git. Repository-scoped `gh` runs from the absolute root with `GIT_DIR=$(jj git root)`, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr create ...)`. Store any temporary report/error files under the workspace's ignored `.tmp/`.

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: bookmark+commit+PR / commit directly to the current bookmark / don't commit. On a clean feature bookmark: commit to it / separate bookmark / don't commit. On a dirty feature bookmark: commit only safely isolated refresh paths / don't commit. Never reset, discard, or rewrite unrelated changes.

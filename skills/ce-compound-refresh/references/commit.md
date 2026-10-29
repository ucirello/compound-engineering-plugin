# Committing the refresh

Skip if no files changed. Check current bookmarks, conflicts, and unrelated changes with JJ from the target workspace's absolute root. Commit **only** files this refresh modified with `jj commit <owned-paths> -m "<message composed from the standards below>"`; preserve unrelated changes. Summarize the actual refresh actions and counts without prescribing message syntax.

Non-interactive defaults: on the verified repository default bookmark → create a bookmark named for what was refreshed, commit, advance that bookmark to the committed revision, and attempt a PR (if creation fails, report the bookmark); on a feature bookmark → separate change on that bookmark and advance it to the committed revision. JJ failures → put recommended commands in the report and continue. Run commands as `(cd "$workspace_root" && jj ...)`, with an absolute root; use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)` for repository-scoped GitHub operations. Scratch and fallback artifacts belong under that workspace's `.tmp/`. Never invoke Git directly. See https://docs.jj-vcs.dev/latest/git-command-table/ .

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / commit directly to the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: commit only owned refresh paths / don't commit.

## Runtime message standards

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards."

Before composing or editing any message, read the full Go guide and compare several recent subjects AND bodies from the actual task's verified history head: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. This style sample does not replace any reviewed revision range. Determine prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue placement at runtime. Repository-local instructions and observed syntax ALWAYS win over Go syntax; apply compatible Go guidance to clarity and structure. If history is absent, use explicit project/user instructions plus Go guidance without inventing precedent.

Verbatim source guidance from https://go.dev/wiki/CommitMessage (the example illustrates Go, not a mandatory repository template):

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

# Committing the refresh

Skip if no files changed. From the absolute workspace root inspect `jj status`, `jj diff`, conflicts and bookmarks; preserve all unrelated work. JJ snapshots automatically: never stage files or describe unrelated changes as part of this refresh. Read this full composition contract and execute the runtime guide/history reads below before composing any description, including a split description. Separate owned paths into a dedicated change with `jj split` only after inspecting the exact selection; otherwise stop and report the ambiguity.

Before composing any message, read the full https://go.dev/wiki/CommitMessage at runtime and read recent full subjects and bodies from the actual verified history head:

```sh
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Set `workspace_root` to the verified absolute target workspace root. Replace the placeholder with the verified actual history revision; do not assume a default bookmark. Compare several examples. Actual repository syntax takes precedence over Go examples. Preserve semantic constraints: a concise outcome-focused subject (imperative where compatible with repository syntax), a body explaining what and why, accurate issue references, no attribution trailers. Use `jj describe -m '<message derived from repository history and verified change>'`, never a fixed conventional template.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Verbatim source guidance, subordinate to actual repository syntax and not a mandatory template:

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

Additional Go source guidance:

> The CL description is a public document that explains to the future what has been done and why.

> the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”

> the verb after the colon is lowercase

> there is no trailing period

> there is no Markdown in the commit message.

> similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

The body and any PR body list each worth-based cut or Delete and each standards change with its quoted evidence. On the verified default bookmark, create a meaningful refresh bookmark; on a feature bookmark, keep the refresh in a separate change. Publish only when authorized using JJ transport. Before repository-scoped `gh`, export `GIT_DIR=$(jj git root)` from the target absolute root. Report publication failures and recovery commands without Git fallback.

Interactive: ask whether to create the separate change and PR, keep a local separate change, or not commit. Non-interactive: follow the caller's publication authorization and report any blocked operation; never include unrelated dirty work.

# Repository context, bookmarks, and PR state

Resolve the absolute root with `jj workspace root`. Every subsequent JJ and repository-scoped gh command must run with that absolute root as its working directory: shell `(cd "$workspace_root" && ...)`, subprocess `cwd=workspace_root`. Obtain and export `GIT_DIR=$(jj git root)` there before gh; this applies to every gh example throughout this skill and its references. It does not permit direct Git execution. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/git-command-table/ . Read each probe's actual exit status.

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list`. Resolve the feature bookmark and push remote from task context and verified revisions; JJ has no checked-out branch. An empty `@` directly above a pushed head is normal: inspect `@-` and its bookmarks before concluding there is no PR. Multiple plausible heads require a decision. The full workflow authorizes creating a meaningful collision-free feature bookmark when missing, without another branching approval. Default bookmark with work uses `branch-creation.md`; no feature work means report and stop.

Resolve base from project/task instructions and `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`; verify its remote bookmark. Do not guess main when resolution fails. Query `gh pr list --head <nonempty-bookmark-name> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` against the base repository (`-R <base-owner>/<repo>` for forks). Pass name only, never owner:name or an empty head. Only exit-0 `[]` means no open PR. Nonzero/auth/network failures mean unknown and block creation until resolved. Match head owner, repository and bookmark, not index 0; stop on ambiguity. Preserve URL/body for composition.

Snapshots are hints: re-verify repository, bookmark, remote, exact head and PR presence before push and create.

## Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing any message, read the full Go guide and local project instructions. Resolve the history head from the actual task/repository, verify it, and inspect several recent subjects AND complete bodies from the absolute target root: `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement. This style sample never replaces a reviewed base/head range. Repository-local syntax established by instructions and history ALWAYS wins over Go guidance. Apply compatible guidance to clarity and structure within that observed pattern; impose no fixed prefix or template. If history is absent, use explicit project/user instructions and Go guidance without inventing precedent. Match PR-title conventions from the same evidence when applicable.

Verbatim source guidance follows. The Go example is illustrative, NOT a mandatory repository template:

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

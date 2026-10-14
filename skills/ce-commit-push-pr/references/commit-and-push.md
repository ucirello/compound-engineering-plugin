# Committing and pushing

If stack construction committed layers, skip to composition; Step 5 publishes the verified layer bookmarks. Default-bookmark work follows `branch-creation.md`. Group naturally distinct concerns at whole-file level (two or three max); do not force hunk splits. Honor `exclude:<paths>`, preserving and reporting unrelated work. JJ has no staging index: inspect status, diff and conflicts, then explicitly commit only the group's paths.

## Message standards (every ordinary, layer and archival commit)

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."

Before composing, read the full Go guide and compare several recent subjects AND bodies with `(cd "$workspace_root" && git --git-dir="$(jj git root)" log -10 --format=%B)` against the read-only backend. Establish prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository-local instructions and history ALWAYS win over differing Go syntax; apply compatible Go guidance to clarity and structure inside the observed pattern. Without history use explicit project/user instructions and Go guidance without inventing precedent. Describe actual outcomes and required issue/PR references. Include a known unambiguous plan U-ID compatibly with the observed style; do not hunt for plans.

### Verbatim Go source guidance, not a mandatory repository template

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

```bash
(cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- file1 file2 file3)
```

Verify committed paths and remaining `@`. Resolve the exact committed revision, not the new empty `@`; create or move only the authorized feature bookmark using `jj bookmark create` or `jj bookmark set`. Apply the Project publishing gate to that exact state, re-verify bookmark, remote, head repository/commit and push authority, then:

```bash
(cd "$workspace_root" && jj git push --remote "<verified-remote>" --bookmark "<verified-feature-bookmark>")
```

Never move default, unrelated or recovery bookmarks. Clean and already pushed means no-op. References: https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

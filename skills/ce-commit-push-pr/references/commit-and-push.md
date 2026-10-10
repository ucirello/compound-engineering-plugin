# Committing and pushing

If stack mode already committed its layers, continue to Step 4; Step 5 publishes the stack. On the default bookmark, first follow `references/branch-creation.md`.

## Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and repository instructions, then compare several recent subjects AND bodies:

```bash
(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)
```

Determine actual prefixes/package names, casing, tense, subject/body separation, wrapping, and issue-reference placement at execution time. Repository instructions and observed history ALWAYS win differing syntax; apply compatible Go guidance for clarity and quality. Without history, use explicit project/user instructions plus Go guidance, never invented precedent. Apply this rule to every layer, explainer commit, title recommendation, and message validation in this workflow.

### Go source guidance (subordinate to runtime repository pattern, not a mandatory template)

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

## Selective changes and publication

Scan for distinct logical concerns (2–3 groups maximum); split whole files, not hunks. Honor `exclude:<paths>` and preserve all unrelated tracked, ignored, and untracked work. JJ has no Git staging-index contract: explicitly select the group's paths with `jj split` when `@` also contains unrelated work, inspect both resulting changes, and describe only the intended revision. Do not include generated files or `.env`. Stop on conflicts or ambiguous ownership rather than discard work.

When an Implementation Unit ID is already in hand, include it in the dynamically composed message in repository-compatible form; do not hunt for a plan or invent a unit. Omit for unclear or multi-unit changes.

```bash
(cd "$workspace_root" && jj status)
(cd "$workspace_root" && jj diff)
(cd "$workspace_root" && jj describe -r "<verified-group-revision>" -m "<message composed from the standards above>")
(cd "$workspace_root" && jj bookmark set "<feature-bookmark>" -r "<verified-publishable-tip>")
```

Apply the Project publishing gate to the exact resulting tip. Re-verify repository, remote, bookmark, and intended commit before publication; do not publish a stale bookmark or unrelated change. Push only this bookmark; explicit `--bookmark` also establishes tracking for a new remote bookmark. Track an existing fetched remote bookmark explicitly only when needed:

```bash
(cd "$workspace_root" && jj git push --remote origin --bookmark "<feature-bookmark>")
```

Already-published work is a no-op. An empty `@` directly above the published tip is normal; inspect `@-` and its bookmarks rather than concluding there is no PR.

Native command semantics: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/ .

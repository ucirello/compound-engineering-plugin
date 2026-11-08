# Committing and pushing

If stack mode already committed its layers, continue to Step 4; Step 5 publishes them. On the default bookmark, first read `references/branch-creation.md`.

## Message standards — required at every composition site

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide. Resolve the actual task's verified history head, then examine several recent full subjects AND bodies from the target workspace's absolute root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository instructions and observed repository-local syntax always win; apply compatible Go guidance to clarity and structure without replacing that syntax. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

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

## Scoped changes and publication

Inspect `jj status` and `jj diff`. Group naturally distinct concerns by whole files into at most 2–3 changes; when ambiguous one is fine. JJ has no staging index. Explicitly name owned paths with `jj commit <owned-paths> -m "<message composed from the standards above>"`, leaving unrelated work in the working copy. Honor and report `exclude:<paths>`. Inspect new files before explicitly tracking owned paths with `jj file track`; never automatically track ignored files.

For an already isolated change use `(cd "$workspace_root" && jj describe -r <owned-change> -m "<message composed from the standards above>")`. Preserve other authors' changes and existing human credit, never squash their work into yours. When shipping someone else's work, retain exact known human identities in repository-compatible credit, using prose when trailers conflict with local conventions; never invent emails. When a known plan Implementation Unit applies, include its U-ID according to project conventions, but do not hunt for a plan or force fixed subject syntax.

Apply the Project publishing gate to the exact state being sent. Re-verify the feature bookmark, head repository, remote, and exact commit; move only the authorized bookmark to the completed change. Publish with `(cd "$workspace_root" && jj git push --remote <verified-head-remote> --bookmark <verified-feature-bookmark>)`. Never push the default or unrelated bookmarks. Conflicts, ambiguous targets, or unknown push authority block publication. With no owned changes and everything published, this step is a no-op.

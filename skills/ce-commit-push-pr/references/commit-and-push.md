# Committing and pushing

Run from the absolute target workspace root; use `context.md` for repository and scoped `gh` context. If stack construction already committed layers, skip ordinary commit/push; Step 5 submits them. Default-bookmark work first follows `branch-creation.md`.

## Runtime message standards — apply at every composition site

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide at that URL and inspect several recent complete subjects **and bodies** at the actual verified history head relevant to this task:

```bash
cd "$workspace_root"
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Compare package/prefix syntax, casing, tense, subject/body separation, wrapping and issue-reference placement. Project-local instructions and observed repository syntax **always win** over Go guidance. Apply compatible Go advice for clarity and structure, not a forced template. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

The following verbatim Go excerpts are source guidance, **not a mandatory repository template**:

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

## Owned-path commits

Scan for clearly separate concerns (2–3 commits maximum); group whole files only. Honor `exclude:<paths>`: leave them and unrelated user work unchanged and report exclusions. JJ has no staging index. Track only intended new paths with `jj file track <owned-files>` if needed; never force ignored files. Explicit path-scoped commits leave unrelated changes in the next working-copy change:

```bash
jj commit -m "<message composed from the standards above>" <owned-files>
```

For an already isolated complete change, `jj describe -m "<message composed from the standards above>"` retains its identity. Include a known plan Implementation Unit ID in the dynamically composed message in the repository's observed style; omit when unknown or spanning units. Do not hunt for a plan or force a suffix format.

Add work above others' commits; never squash away human authorship or existing trailers. Preserve human credit according to explicit project instructions and established local conventions; never invent identities or add model/harness attribution.

## Push

Apply the Project publishing gate to the exact revision being sent. Re-verify feature bookmark, head repository, remote, commit, authority and PR. Move only the owned feature bookmark forward with `jj bookmark set <branch> -r <verified-completed-head>`, then `jj git push --remote <verified-remote> --bookmark <branch>`. This also creates and tracks an authorized new remote bookmark. Never push unrelated bookmarks. An empty `@` above the completed head is normal; do not push it. If clean and already pushed, this step is a no-op.

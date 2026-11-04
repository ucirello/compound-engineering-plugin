# Committing and pushing

If stack mode already built layers, skip ordinary commit/push; Step 5 submits them. On the default bookmark first follow `branch-creation.md`.

Group naturally distinct concerns by whole files, 2–3 changes maximum, or one when ambiguous. Honor `exclude:<paths>` and report excluded paths. JJ snapshots automatically: inspect the diff and commit only named owned paths with `jj commit <owned-files> -m "<message composed from the standards above>"`, leaving unrelated work in the working copy. Verify the resulting revision and remaining work. Never sweep unrelated or ignored files into a change.

## Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and compare several recent subjects AND bodies from the task's verified history head, from the target workspace's absolute root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefixes/package names, casing, tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax established by project instructions and JJ history ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to clarity and structure, not as a replacement syntax. With no history use explicit project/user instructions and Go guidance without inventing precedent. Preserve known plan unit U-IDs as semantic content when one unit applies; do not hunt for plans or impose fixed placement.

The following verbatim Go source guidance is illustrative, not a mandatory repository template:

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

Preserve other people's authorship and existing human trailers; never squash their work into yours in a way that loses credit. When repository-local requirements require human contributor credit, copy exact recorded identities, never invent emails or add model/harness attribution.

Apply the **Project publishing gate** to the exact state being sent. Immediately before push verify head repository, remote, feature bookmark, push authority, and exact committed head. Set only the intended bookmark with `jj bookmark set <bookmark> -r <verified-head>`, then `(cd "$workspace_root" && jj git push --remote <verified-remote> --bookmark <bookmark>)`. Latest JJ pushes and automatically tracks an explicitly selected new bookmark. Do not publish an empty working-copy tip instead of its intended parent. Clean work whose intended commits are already pushed is a no-op.

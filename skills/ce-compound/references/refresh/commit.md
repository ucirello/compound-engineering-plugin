# Committing the refresh

Skip if no files changed. From the absolute JJ workspace root identify the verified base, current bookmark and default remote bookmark, accounting for an empty `@` above `@-`, and inspect for unrelated work or conflicts. Use JJ from that workspace (see [the JJ CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-commit)); include **only** the exact paths this refresh changed, including any `CODING_STANDARDS.md` it changed. A path-scoped `jj commit` can leave unrelated paths in the working-copy change; if there is an unrelated edit within an owned path or exact separation cannot be proven, stop instead of committing it.

Non-interactive defaults: on the verified default line, make the refresh change on a separate bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), then attempt to publish and open a PR; if PR creation fails, report the bookmark. On a feature line, make a separate change on that line. On JJ failure, report the blocker and recommended commands and continue reporting. Verify the selected local bookmark points to the exact new refresh change: create the separate bookmark there without moving the default, or advance the selected existing bookmark only along its verified line. Push only the identified authorized bookmark and remote via `jj git push`, and scope any PR command with `(cd "$workspace_root" && GIT_DIR="$(jj git root)" && export GIT_DIR && gh …)`.

Interactive: ask (per Blocking questions), with the recommended option first. On the default line: separate bookmark + commit + PR (recommended; specific bookmark name) / commit directly to that line / don't commit, subject to repository policy. On a clean feature line: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature line: commit only verified refresh paths / don't commit.

## Compose the change description

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing a message, read the full Go guide and inspect full subjects **and** bodies at the history head verified for this refresh, e.g. `(cd "$workspace_root" && jj log --no-graph -r "::$history_head" -n 10 -T 'description ++ "\n"')`. Compare several changes for prefix or package name, casing, verb tense, subject/body separation, wrapping and issue references. Project instructions and repository-local syntax take precedence; apply compatible Go guidance to clarity, structure and issue references. If there is no history, use explicit project/user instructions and Go guidance without inventing a precedent.

Summarize what was refreshed; the message body and PR body list each worth-based cut or Delete and each standards change with its quoted evidence. Use the composed message in the path-scoped operation, e.g. `(cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- <exact refresh paths>)`.

Go source guidance (illustrative, not a repository template):

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

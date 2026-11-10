# Fix commit composition

Before composing any fix commit, read the full https://go.dev/wiki/CommitMessage at runtime, not only this link or an excerpt. Also inspect recent full subjects and bodies from the actual verified history head, running from the absolute target workspace root:

```sh
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Replace the placeholder with the verified immutable history head; do not assume a default remote bookmark. Compare several examples for the repository's actual syntax. Repository syntax wins over Go guidance; never impose a fixed conventional-commit prefix or template. User constraints remain authoritative. Explain the change and its reason, include accurate issue references only, and never add attribution, generated-by text, or Signed-off-by trailers.

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

Use `jj describe -m '<repository-conformant description>'` only for the isolated fix change. If user work overlaps, stop rather than describe or commit it accidentally. Use JJ bookmark and `jj git push --bookmark <verified-task-bookmark>` transport, never direct Git; verify the resulting immutable commit ID for return fields. This composition requirement applies to both pipeline and return-to-caller commits.

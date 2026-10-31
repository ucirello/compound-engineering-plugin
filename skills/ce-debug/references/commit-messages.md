# Fix change descriptions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composition, read the full guide and several recent complete subjects and bodies from the actual verified relevant history head: from the absolute target workspace root run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare package/prefix syntax, case, tense, subject/body separation, wrapping and issue placement. Repository instructions and observed history syntax always win over Go examples; apply compatible guidance for clarity. With no history, use explicit instructions and Go guidance without inventing precedent. Describe the verified bug, causal correction, evidence and applicable issue; never force a fixed prefix or Conventional Commits.

Source guidance, subordinate to the runtime repository pattern:

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

Commit only the recorded fix-owned paths with `jj commit <fix-owned-paths> -m "<message composed from the standards above>"`; unrelated working-copy edits must remain outside the resulting commit. Verify the resulting commit and bookmark before any authorized push.

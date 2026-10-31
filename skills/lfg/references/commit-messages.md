# Runtime commit-message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing each message, read the full linked guide and several recent complete subjects **and bodies** at the actual verified relevant history head. From the absolute target workspace root run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Resolve that head from the task and repository, not an assumed default branch. Compare package/prefix syntax, case, tense, subject/body separation, wrapping, and issue placement. Repository-local instructions and observed history syntax always win; apply compatible Go guidance within that pattern. Without history, follow explicit instructions and Go guidance without inventing precedent. No fixed message, prefix, or Conventional Commit type is required.

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

Use `jj describe -m "<message composed from the standards above>"` when describing an already isolated owned change; when a caller prescribes a path-scoped `jj commit`, retain that operation and exact owned paths instead. Preserve semantic requirements from the caller, not fixed syntax.

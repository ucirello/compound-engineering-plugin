# Change-description composition

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before every composition (candidate, integration, result-marker or report change), read the full guide and several recent complete subjects AND bodies at the verified relevant task history head, from the absolute target workspace root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare package/prefix syntax, casing, tense, body separation, wrapping and issue placement. Repository-local instructions and observed history syntax ALWAYS win. Apply compatible Go clarity/structure guidance; with no history do not invent precedent. Describe the actual hypothesis, experiment and scoped changes, or the report/result evidence being recorded, without forcing any fixed prefix or Conventional Commit syntax. Use `jj describe -m "<message composed from the standards above>"` from the absolute target root; include only the intended owned paths, leaving unrelated files out through an inspected path-scoped JJ change/split. Advance the optimization bookmark only to verified integrated results.

The following verbatim Go excerpts are source guidance, subordinate to the runtime repository pattern, not a mandatory template:

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

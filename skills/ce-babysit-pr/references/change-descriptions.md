# Change descriptions for authorized repairs

Before describing a repair or recommending its message, read the full guide at https://go.dev/wiki/CommitMessage and inspect several recent subjects AND bodies from the read-only JJ Git backend: `(cd "$workspace_root" && git --git-dir="$(jj git root)" log -10 --format=%B)`. Compare prefixes/package names, casing, tense, separation, wrapping and issue placement. Repository-local instructions and observed history always override differing Go syntax; apply compatible guidance to clarity and structure. With no history use explicit project/user instructions and Go guidance, never invent precedent.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The following is quoted source guidance, not a mandatory repository template:

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

Compose dynamically from those standards, describing the actual repair, validation and applicable issue/PR without fixed prefixes or templates. Use `(cd "$workspace_root" && jj describe -r <owned-repair> -m "<message composed from the standards above>")` only for the verified owned change; do not rewrite unrelated history.

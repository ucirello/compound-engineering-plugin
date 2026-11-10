# Change descriptions

Apply this whenever babysitting composes or edits a change description, including a mechanical base-merge repair, takeover fix, or squash description. Existing authorship remains intact.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composition, read the full Go guide and inspect several recent subjects AND bodies from the target workspace's absolute root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Resolve the history head from the actual PR/task; do not assume a default branch or replace the reviewed base/head range with this style sample. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement across several messages. Repository-local instructions and observed syntax always win over Go guidance; apply compatible guidance to clarity and structure, not a new mandatory prefix/template. With no history, use explicit project/user instructions and Go guidance without inventing precedent. Describe the actual fix, its scope and relevant PR/issue accurately. Use `jj describe -m "<message composed from the standards above>"` only on the intended owned change.

Verbatim source guidance from https://go.dev/wiki/CommitMessage (the Go example is illustrative, not a mandatory repository template):

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

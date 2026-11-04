# Local message composition

Before composing, editing, validating, or recommending any setup or polish commit message, read the full https://go.dev/wiki/CommitMessage guide. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Verify the actual relevant runtime history head without substituting a default bookmark or changing any reviewed range. From the target absolute workspace root, inspect several recent full subjects and bodies:

```bash
(cd "$WORKSPACE_ROOT" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefix/package conventions, case and tense, subject/body separation, wrapping, and issue placement. Project instructions and actual history syntax always win; apply compatible Go quality guidance. If history is unavailable, use project/user instructions plus the guide without inventing precedent. Keep the intended operation, changed dependency version when relevant, and owned-path scope, without imposing a fixed message syntax. Invoke `ce-commit` with that evidence; a direct description example is `(cd "$WORKSPACE_ROOT" && jj describe -m "<message composed from the standards above>")`.

## SOURCE GUIDANCE — not a mandatory repository template

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

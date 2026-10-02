# Runtime message standards

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."

Before composing, editing, validating, or recommending any change description, read the full Go guide at runtime and compare several recent commit subjects AND bodies:

```bash
(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)
```

`workspace_root` must be the target workspace's absolute root. This is read-only backend history access, not Git-based working-copy management. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax established by project instructions and history ALWAYS wins over differing Go guidance. Apply compatible Go advice to clarity, quality, and structure within that pattern. If history is absent, use explicit project/user instructions and Go guidance without inventing precedent. Never infer syntax from the example below. PR titles follow the observed repository title conventions rather than a fixed Conventional Commit template.

## Verbatim Go source guidance (illustrative, not a mandatory repository template)

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

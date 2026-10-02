# Runtime change-description standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing a message, read the full Go guide and compare several recent subjects AND bodies using `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)` from the target workspace's absolute root. This is read-only history access. Establish actual prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue-reference placement. Repository-local instructions and syntax always win; apply compatible Go guidance to quality and clarity without replacing that syntax. With no history, use explicit project/user instructions and Go guidance without inventing precedent. Preserve bug, hypothesis, CI and issue-reference requirements, but choose no fixed message syntax beforehand.

Verbatim Go excerpts below are source guidance, not a mandatory repository template:

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

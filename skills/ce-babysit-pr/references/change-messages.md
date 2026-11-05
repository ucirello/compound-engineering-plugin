# Change-description standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing or editing, read the full Go guide and project/user instructions. Resolve the relevant history head from this actual PR/task; from the target workspace's absolute root run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare several full subjects AND bodies: package/prefix syntax, casing, verb tense, separation, wrapping and issue placement. Repository-local syntax always wins; apply compatible Go guidance for clarity and structure, not as a replacement syntax. With no history use explicit project/user instructions and Go guidance without inventing precedent. Describe the actual repair and relevant PR/issue without fixed wording. Use `jj describe -m "<message composed from the standards above>"` only on the owned change; preserve human authorship.

The following verbatim Go source guidance is illustrative, not a mandatory repository template:

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

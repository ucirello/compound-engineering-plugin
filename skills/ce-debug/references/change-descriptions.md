# Change descriptions

Before composing any fix change description, read the full https://go.dev/wiki/CommitMessage guide and examine several recent subjects **and bodies** from the target workspace's absolute root, for example `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Resolve that history head from the actual task/repository, not a hardcoded default branch, and do not replace a reviewed base/head range with this style sample.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

**Go source guidance — illustrative excerpts, not a repository template.** These verbatim SOURCE excerpts are subordinate to observed repository syntax and explicit project/user instructions. Read the full guide and compare history as required above; apply only compatible guidance.

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

Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue-reference placement across several messages. Repository-local syntax and explicit project/user instructions always win; apply compatible Go guidance to clarity and structure within that pattern. If there is no history, use explicit instructions and compatible Go guidance without inventing precedent. Describe the confirmed cause and fix and required issue references, without a fixed type, scope, subject or body template. Use `jj describe -m "<message composed from the standards above>"` only on the fix-owned change; use the owned-file commit workflow to keep unrelated edits out. Do not add model/harness authorship or coauthor/assistance attribution.

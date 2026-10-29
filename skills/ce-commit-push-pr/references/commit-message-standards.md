# Runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, editing, validating or recommending a description, read the **full** https://go.dev/wiki/CommitMessage at runtime. Resolve the actual task's verified history head (feature head or selected layer parent, not a hardcoded default). Inspect several recent complete subjects AND bodies from the target workspace's absolute root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement across multiple commits. Repository-local project/user instructions and observed syntax **always win** over conflicting Go guidance. Apply compatible Go advice for clarity, concise subjects, explanatory bodies and issue placement within that pattern. With no history, use explicit instructions and compatible Go guidance without inventing precedent. Style samples never replace the exact base/head review range.

These verbatim excerpts are source guidance, including an illustrative Go example, **not a mandatory repository template** or a message to emit:

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

Preserve semantic requirements (behavior, issue/PR, hypothesis, known implementation unit, owned paths) but determine syntax at runtime. Use neutral message placeholders in commands. This applies to ordinary commits, stack layers, explainer archival and message/title recommendations.

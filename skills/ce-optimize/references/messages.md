# Runtime change descriptions

Apply this procedure at every composition site: experiment candidates, remote result-only changes, integrated winners, archive descriptions and exported reports. Use JJ for describing, committing, integrating and publishing changes; never invoke Git. Commands run from the target workspace's absolute root. Preserve owned mutable-path scope; inspect the exact candidate and integrate it with native JJ rebase/merge operations without including result-only commits or unrelated work. Move the optimization bookmark only after successful integration and verification. Never discard unrelated working-copy state.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide and resolve the actual task's relevant history head. From the target workspace's absolute root inspect several recent subjects AND bodies, for example `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement. Repository-local instructions and observed syntax always win; use compatible Go guidance for clarity and structure. With no history, use explicit project/user instructions and the guide without inventing precedent. Never replace the exact reviewed base/head range with this style sample. Use `jj describe -m "<message composed from the standards above>"` for descriptions; preserve each site's required hypothesis, experiment, report or result content rather than fixing syntax in advance.

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

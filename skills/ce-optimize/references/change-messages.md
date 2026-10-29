# Change descriptions

Apply this procedure before composing every experiment, result-marker, integration or report description, including remote-worker messages. Pass this reference's full instructions in the worker brief.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the full Go guide at runtime. Resolve the relevant history head from the actual optimization task and repository, then inspect several recent subjects AND bodies from the target workspace's absolute root:

```sh
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue placement. Project/user instructions and the observed repository syntax always win over incompatible Go syntax. Apply compatible Go guidance for clarity and structure, not a fixed experiment prefix or Conventional Commit template. With no history use explicit instructions and Go guidance without inventing precedent. The history sample never replaces the actual reviewed base/head range. Preserve required hypothesis, experiment identity, scope and issue references as content. Use `jj describe -m "<message composed from the standards above>"` for the owned candidate; record only mutable-scope paths. Create a separate child for a result-marker-only commit and move only the authorized result bookmark before `jj git push` to the verified remote.

## Verbatim Go source guidance (illustrative, not a repository template)

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

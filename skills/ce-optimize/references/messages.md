# Change-description standards

This applies to every description composed during optimization: initial scaffolding, candidate experiments, integrated winners/runners-up, result-only remote children, report exports and wrap-up. Runtime-read the full guide at https://go.dev/wiki/CommitMessage and inspect several recent full subjects AND bodies from a history anchor verified from the task's optimization base/bookmark, not a hardcoded default branch:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue placement. Repository/user syntax always wins; Go supplies only compatible quality/structure guidance. Without history use explicit instructions plus Go, never invent precedent. Keep the exact experiment base/reviewed range distinct from this style sample.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Use `jj describe -m "<message composed from the standards above>"` from the absolute target workspace root, preserving intended operation and scope. Do not impose a Conventional Commit type/scope or a fixed subject/body template. Retain semantic experiment identity, hypothesis, measured rationale and required issue references. Do not add generator/model/harness attribution.

## Go SOURCE GUIDANCE — subordinate to observed repository pattern

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

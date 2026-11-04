# Committing and pushing

Use `context.md`'s absolute cwd and repository-scoped `gh` rules. Stack construction replaces ordinary single-bookmark commits.

## Message standards for every composition site

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards."

Before composing at runtime, read the full Go guide. Resolve the relevant history head from the actual task and repository; from the target workspace's absolute root inspect:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Compare several subjects AND bodies for prefixes/package names, casing, verb tense, separation, wrapping and issue placement. Repository-local instructions and observed syntax always win over Go syntax. Apply compatible Go guidance to clarity, intent and structure within that pattern. With no history use explicit project/user instructions and Go guidance without inventing precedent. A style sample never replaces the exact reviewed base/head range.

Verbatim Go source guidance, not a mandatory repository template:

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

## Owned-path mechanics

Follow `branch-creation.md` on the default bookmark. Group naturally distinct concerns at whole-file level (2–3 commits maximum); one commit is fine when ambiguous. No forced hunk splitting. Honor `exclude:<paths>`: never move or commit them and report exclusions. Inspect `jj status` and `jj diff`; explicitly track intended untracked paths with `jj file track <owned-paths>` when necessary. Commit only the group:

```bash
jj commit -m "<message composed from the standards above>" -- <owned-paths>
```

Verify committed paths and leave unrelated work in the working copy. When a plan Implementation Unit is already known, record its U-ID in repository-compatible syntax; omit if unclear or spanning units and do not hunt for a plan. Preserve other people's commits, human authorship and existing trailers; never squash their work into yours. Any credit for incorporated human work must use exact recorded identities, follow repository policy and the message standards above, and never invent an email or add model/harness attribution.

Apply the Project publishing gate to the exact state being sent. Immediately reverify intended commit, feature bookmark, head repository, remote and push authority. Move only the owned feature bookmark and push it:

```bash
jj bookmark set <feature-bookmark> -r <verified-commit>
jj git push --remote <verified-head-remote> --bookmark <feature-bookmark>
```

Use `--allow-new` only for the intended new remote bookmark. Never publish a guessed head or move the default bookmark. Clean and already pushed is a no-op.

# Committing and pushing

Use the absolute target workspace cwd for every JJ command and context.md's wrapper for every gh call. Stack layers already committed skip ordinary creation, not the publishing gate.

## Every commit composition

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the FULL linked Go guide at runtime before composing. Resolve the actual task/repository history anchor, never hardcode main, then compare several recent full subjects AND bodies:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

The history sample does not replace the exact review range. Infer prefixes/package/case/tense/body separation/wrapping/issues from several messages. Project/user instructions and repository history syntax win; use compatible Go quality guidance only. Without history use project/user plus Go guidance, never invented precedent. Preserve semantic scope and known unit identifiers in the repository idiom, not a fixed suffix.

Verbatim illustrative Go source excerpts — NOT a mandatory repository template:

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

Preserve existing human authorship/source credit; repository-required human credit wins over incompatible illustrative conventions. Never add model/harness attribution.

## Selection and publication

JJ snapshots automatically. Inspect complete changes including untracked paths; honor exclude:<paths> and unrelated user work. Group distinct concerns into at most 2–3 whole-file commits, otherwise one. Use `jj split <explicit-paths>` only for selected groups and verify each resulting revision contains exactly its intended files. Never assume all of @ belongs to the task. Preserve other people's commits/authors/trailers without squashing them into yours.

```bash
jj describe -r <verified-selected-revision> -m "<message composed from the standards above>"
```

Read branch-creation.md for default-bookmark work. Apply the Project publishing gate to the exact head sent. Re-verify repository, feature bookmark, remote and revision; move only the authorized bookmark with `jj bookmark set <feature> -r <verified-head>`, then `jj git push --remote <remote> --bookmark <feature>`; allow-new is only for an authorized new remote bookmark. Never push all bookmarks. Already-pushed work is a no-op. An empty @ directly above the exact verified pushed head is aligned. Dirty/conflicted/uncertain alignment forbids destructive adjustment, not otherwise authorized monitoring.

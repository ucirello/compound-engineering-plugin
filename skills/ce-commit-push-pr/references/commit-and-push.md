# Committing and pushing

If stack construction already committed layers, continue to composition; Step 5 owns publication. For default-base handling read `branch-creation.md`. All JJ commands run with cwd the absolute `workspace_root`, not merely `-R`; use the gh environment in `context.md`.

Inspect the complete tracked and untracked change set and exclusions. Group naturally distinct concerns at whole-file level (usually one, at most 2–3 commits). Never include unrelated or `exclude:<paths>` work. JJ has no staging step: commit only explicit owned repo-relative paths using `jj commit -m "<message composed from the standards above>" -- <owned-paths>`. Inspect the resulting commit and remaining working change to verify exclusions and ignored content stayed untouched. Preserve other people's authorship and existing human trailers; do not squash their work into yours. Credit actual human work with exact recorded identities when necessary, never invent email addresses or add model/harness credits.

## Message composition and validation

Read the full https://go.dev/wiki/CommitMessage guide, then compare several recent full subjects AND bodies at the actual relevant verified runtime history head using `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Analyze prefix/package, case/tense, separation, wrap and issue placement. Project instructions/history syntax always wins; use compatible Go quality guidance. No history means project/user instructions plus Go guidance, not invented precedent. Preserve semantic scope and any already-known implementation-unit identity only in syntax compatible with these runtime standards.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

### SOURCE GUIDANCE — not a mandatory repository template

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

## Publish

Apply the Project publishing gate against the exact commit being sent. Immediately re-verify repository, publishing bookmark, remote, exact commit and PR, including push authority. Advance only the intended owned bookmark with `jj bookmark set <bookmark> -r <verified-commit>`; track the confirmed remote bookmark when required using `jj bookmark track <bookmark>@<remote>`. Publish only that bookmark using `jj git push --remote <remote> --bookmark <bookmark>` (use `--allow-new` only for an authorized new remote bookmark). No broad push, force overwrite, or stale-ref substitution. Unknown authority, conflicts, dirty unrelated work requiring movement, or ambiguous alignment stops safely. Verified clean-head alignment, including an empty `@` above the exact head, and authorized push/monitor/rearm need no additional approval. Already-published exact commits are a no-op.

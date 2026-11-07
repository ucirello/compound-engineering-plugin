# Committing and pushing with JJ

If stack layers were already described, continue to composition; Step 5 owns submission. Read `branch-creation.md` before publishing work derived from the default base.

## Required runtime message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

At runtime read the **entire** https://go.dev/wiki/CommitMessage, not just these excerpts. Resolve `<verified-history-head>` from this task's actual verified head/base, then inspect several recent complete subjects **and bodies**:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Explicitly compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue placement. User/project requirements and observed repository syntax always win; Go supplies compatible quality/structure, not mandatory syntax. With no history use explicit instructions plus Go and state that no precedent exists. This sample never replaces the exact reviewed revision/range.

### Verbatim Go SOURCE GUIDANCE — subordinate to observed repository pattern

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

## Scope and publication

Inspect the exact change and group naturally distinct whole-file concerns into at most 2–3 changes; ambiguity favors one. JJ snapshots automatically: there is no staging-area recipe. Honor `exclude:<paths>` and unrelated user work, including ignored content. If `@` includes only the intended group, describe it; otherwise use explicit whole-file `jj split <owned-paths>` only after verifying resulting revisions and preserving excluded work in the working copy. Never sweep unrelated paths into a commit. Hunk splitting, conflicts or uncertain ownership stop for a decision.

```bash
jj describe -m "<message composed from the standards above>"
```

Preserve human authorship and existing human/source credit; never squash others' work into yours or invent identities. Plan unit IDs already in hand may be included where compatible with repository syntax; do not mandate a suffix or hunt for plans. No generated-by/model/harness trailers.

Apply the Project publishing gate to the exact intended commit state. Reconfirm feature bookmark, commit, head repository and push authority; set/move only the authorized feature bookmark to the verified commit, preserving recovery refs. Push using `jj git push --remote <verified-head-remote> --bookmark <feature-bookmark>`; `--allow-new` only for an authorized new remote bookmark. Clean already-pushed work is a no-op. A clean empty `@` above that head already aligns; no extra alignment approval. Dirty/conflicted/unknown states stop without discarding work.

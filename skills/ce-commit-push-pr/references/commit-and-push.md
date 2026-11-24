# Committing and pushing

Stack mode constructs layers per `references/stack-submit.md` instead of the ordinary Step 3 below; Step 5 submits them. When starting on the default bookmark, apply `references/branch-creation.md` first.

## Compose each JJ change description

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing any message (including a stack layer or explainer archive), read the full Go guide and compare several recent full descriptions — subjects **and** bodies — from the actual task's verified history head. Run from the target workspace's absolute root, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Resolve the anchor from the intended branch/bookmark and task, not from a hard-coded default or drafts created in this run. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. This sample is for style, not a substitute for the actual publish or review range.

Project instructions and observed repository-local syntax **always win** where they differ. Apply compatible Go guidance to clarity, quality and structure without imposing Go syntax. When no history exists, use explicit project/user instructions and compatible Go guidance without inventing precedent.

Go source guidance (not a required template):

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

Include the plan Implementation Unit ID when one is already in hand and applies to this commit only, using the repository's placement and format. Do not hunt for a plan or guess a unit. Add commits above others' work without rewriting or dropping their authorship. If someone's work will not otherwise land under their name, preserve human credit using local conventions. Copy known author and contributor identities exactly from the source commits or patch; when email is unavailable, use the known name in prose rather than guessing.

## Commit only intended paths

Start by recording exact parent/change IDs and validating scope. Group distinct concerns at file level (2–3 commits max; use one when ambiguous). Reject overlaps with `exclude:<paths>` or unrelated work; leave those changes and report them. If unwanted work is already in commits in the publish range, stop rather than pushing it. Do not separate competing edits to the same file without a separate decision.

```bash
jj commit -m "<message composed from the standards above>" -- "<owned-path-1>" "<owned-path-2>"
```

Pass literal verified workspace-relative filesets (use `file:"..."` filesets for exact path matching and quote unexpected characters as arguments). `jj commit` with explicit paths keeps those changes in the resulting commit and carries the remainder into the new `@`. Verify the exact resulting commit ID and path diff for each group; never commit all by omission. Do not publish `@` just because it is the current working-copy change.

## Publish one verified bookmark

Record the intended feature tip after all groups. Create a new bookmark there (`jj bookmark create "<feature>" -r "<tip-id>"`), or advance a verified existing feature bookmark only over the authorized range (`jj bookmark set "<feature>" -r "<tip-id>"`). Verify the bookmark still selects that exact commit, not the working-copy remainder. Never move the default or another user's bookmark.

Apply the **Project publishing gate**. Recheck the PR, remote identity, push authority, exact local bookmark and published head immediately before push. Fetch the exact remote branch, distinguish a missing remote bookmark from an unknown fetch, and prove an existing remote head is identical to or an ancestor of the local tip. For GitHub, use verified evidence such as the authenticated actor's write permission on the exact head repo and any applicable branch restrictions; base-repo permissions alone do not establish that for a fork. Unexpected divergence, conflicts, unknown push authority or denial stop safely. A successful `jj git push … --dry-run` can preview the ref update but is not proof of push permission.

```bash
jj git push --remote "<verified-head-remote>" --bookmark "exact:<feature>"
```

No push is needed if the exact intended tip is already published. After push, verify the exact remote OID via a fresh fetch or authoritative GitHub query. Never force a rewrite to align or monitor, and never publish unrelated remaining changes.

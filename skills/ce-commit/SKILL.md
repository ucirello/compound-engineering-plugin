---
name: ce-commit
description: Commit local Jujutsu changes with a clear, repository-appropriate description. Use when the user asks to commit or save working-copy changes without pushing or opening a pull request.
---

# Commit with Jujutsu

Create well-crafted local commits from the current JJ working-copy change (`@`). No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a description that states the outcome, and `jj status` shows those changes are no longer pending in `@`. Unrelated or excluded changes stay in `@`. **Stop when:** there are no eligible changes to commit.

## Context

Run `jj workspace root`; stop if no JJ workspace is found. From its absolute root, run each command separately with program and arguments: `jj status` for state and conflicts, `jj diff -r @` for the full working-copy diff, and `jj log -r @`, `jj log -r @-`, and `jj log -r 'trunk()'` for bookmark context. `root()` alone does not establish a default bookmark. Interpret failures rather than suppressing them.

Determine the default bookmark name from project instructions and the configured trunk ref. If it is still unknown and the repository is on GitHub, use `GIT_DIR=$(jj git root)` for `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`: make two tool calls from the same workspace root, passing the verified output of `jj git root` as the environment value for the `gh` call. If `jj git root` fails, skip the GitHub lookup. Use the bare name, not a remote-qualified ref, to recognize the default bookmark; also protect `main` and `master`.

Treat the context as a snapshot. Recheck `@`, the selected paths, and the intended bookmark just before each commit if anything may have changed. Check remote bookmark targets with `jj bookmark list --all-remotes` when local output doesn't establish whether `@` is published.

## Description standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing, read the full Go guide and compare several recent **subjects and bodies** from the workspace's absolute root: `jj log --no-graph -r '::<verified-history-head> ~ root()' -n 10 -T 'description ++ "\n"'`. Use the verified parent of `@` or a more relevant verified task revision, not an assumed default branch. Compare prefixes or package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Without history, follow explicit project/user instructions and Go guidance; don't invent precedent.

Repository-local syntax from active project instructions and observed history always wins over Go guidance. Apply compatible guidance: describe the outcome, not the files, and explain non-obvious motivation or trade-offs. Include a plan Implementation Unit ID only if already in hand and the commit clearly belongs to that one unit. Credit human authors and co-authors whose work would otherwise land without their names; use the repository's convention and exact recorded identities. If an email isn't recorded, give credit by name in the body instead.

**Verbatim Go source guidance (the example illustrates Go's conventions; it is not a repository template):**

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

## Workflow

0. **Gather** — inspect the Context above, including the full working-copy diff.

1. **Nothing to commit** — if `jj status` reports no changes, report that and stop. JJ snapshots eligible new files into `@`; don't call the workspace clean if JJ warns that relevant files were left unsnapshotted. Honor `exclude:<paths>` throughout and report those paths as left out. If no eligible paths remain, stop before creating a bookmark.

2. **Feature bookmark first** — reuse a verified local feature bookmark for the task. If there is none or only a default bookmark at the parent, create a unique task bookmark on `@` with `jj bookmark create --revision @ <feature-bookmark>` and verify its target. If the name is taken, choose a non-conflicting suffix. Do not ask for this routine local step. Before creating or moving a bookmark, stop and report a blocker if committing `@` would rewrite a published change, default or unrelated bookmark, or existing descendant, or if the changes are conflicted.

3. **Logical commits** — if files clearly split into distinct concerns, use separate commits (whole files only, 2–3 max, no interactive hunk selection). If the grouping is ambiguous, use one commit. Do not take unrelated edits just because they are in `@`; if an intended file also contains unrelated edits, resolve scope with the user before committing that file. Treat both sides of a rename as one scope decision.

4. **Compose and commit each group** — apply the Description standards to the group's reviewed diff. Pass the whole message as one literal argument, including any newlines, to the scoped command below. Use one [exact fileset](https://docs.jj-vcs.dev/latest/filesets/) per workspace-relative file, with the path quoted as a JJ string literal when needed. Never omit the paths or use a directory or glob selector. JJ commits the selected paths and moves all remaining edits onto the new working-copy change above it; there is no separate staging step.

```sh
jj commit --message "<message composed from the standards above>" -- 'root-file:src/example.py' 'root-file:src/example_test.py'
```

Use an argument-vector call so message characters are not evaluated by a shell. If a file is needed for handoff, write it under the workspace's local `.tmp/` and read it into the message argument from an argv-capable runner (for example, `subprocess.run` with `cwd` set to the absolute workspace root); never interpolate its contents into shell source.

5. **Confirm and advance** — after each commit, inspect the new `@-` with `jj log -r @-` and `jj diff -r @- --summary`, and check `jj status` for untouched remaining work. Confirm the commit contains exactly the intended files before moving the verified task bookmark forward. `jj commit` leaves bookmarks on the change they already pointed to; if the feature bookmark has not reached the new commit, advance only that named bookmark using `jj bookmark move --to <verified-commit-id> <feature-bookmark>` after verifying its current target is still the expected ancestor. Never force it or move a default or unrelated bookmark. Stop and report a mismatch rather than continuing.

6. **Report** — list the resulting commit hash(es) and subject(s), and note any files left uncommitted. Do not push.

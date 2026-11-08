---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` shows those changes no longer in the working copy. **Stop when:** there are no requested changes to commit.

## Context

Resolve the absolute target workspace root with `jj workspace root`. Run every subsequent JJ command with the shell tool's working directory set to that absolute root, not merely with `-R`. Use each command as its own shell call; interpret non-zero exits rather than suppressing them. See the [JJ command table](https://docs.jj-vcs.dev/latest/git-command-table/) and [CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/).

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy changes and conflicts | Not a JJ workspace — stop |
| `jj diff --summary` | Changed paths | No tracked changes; also inspect untracked/ignored state |
| `jj log --no-graph -r '@ | @-'` | Working-copy change and parent identities | Resolve repository state before proceeding |
| `jj bookmark list` | Local and remote bookmark positions | No bookmarks is valid; JJ has no detached-HEAD failure mode |

Treat this as a snapshot. Re-read status, selected paths, conflicts, and bookmark positions immediately before committing if anything may have changed. Inspect new files as well: ignored or intentionally untracked files are not automatically part of a JJ change. Do not add unrelated files or alter ignore rules to sweep them in.

## Message standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing, read the **full** Go guide. Resolve the relevant actual history head from this task and repository, verifying its commit identity: use the current change when it is an existing described task commit, or its verified parent when `@` is a fresh working-copy change; use the verified task/source head when the workflow identifies a different history. Do not blindly select a default remote bookmark. From the absolute target workspace root, examine several recent **full subjects and bodies**, for example:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement across several commits. Repository-local syntax established by project/user instructions and that history **always wins** over differing Go guidance. Apply compatible Go guidance to clarity, quality, and structure within that pattern. With no history, use explicit project/user instructions and compatible Go guidance without inventing precedent. Do not impose a fallback Conventional Commit format, package prefix, or fixed subject.

The following verbatim Go excerpts are **source guidance, not a mandatory repository template**; the runtime repository pattern takes precedence:

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

0. **Gather** — collect the context above and inspect the actual requested changes. Stop for unresolved conflicts or uncertain ownership; never discard unrelated work.

1. **Nothing to commit** — if there are no requested changes, report that and stop. An empty `@` is normal. Do not create an empty commit merely to satisfy the workflow.

2. **Bookmark first** — preserve existing task/source bookmarks. If no suitable task bookmark exists, or the only relevant bookmark is the verified default branch, create a non-conflicting feature bookmark derived from the change content with `jj bookmark create <name> -r @`. Do not move the default bookmark. JJ does not require a checked-out branch; verify the task bookmark points at the intended change. If its name exists elsewhere, choose a non-conflicting suffix rather than moving unrelated state.

3. **Convention** — read the full guide and compare full recent descriptions as required above before drafting any message. User/project requirements and repository-local syntax win; do not select syntax in advance.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk splitting). If ambiguous, one commit. Keep an explicit owned-path list for each group.

5. **Message** — communicate the outcome, not just the file list, using the runtime standards above. Include motivation or trade-offs when needed. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or files belonging to one unit), record that unit ID in a form compatible with local message syntax. Do not hunt for a plan. Omit it when the commit spans units, the unit is unclear, or no plan is in hand. When carrying someone else's work that will not otherwise land under their name, preserve human credit from the source commits or patch. Follow explicit local attribution requirements; otherwise name those people in the body rather than adding trailers forbidden by compatible Go guidance. Copy recorded identities exactly; never guess an email. Do not add assistant/model/harness attribution.

6. **Commit named files** — JJ has no staging index. Honor `exclude:<paths>`: those files remain in the working copy and must not enter a selected group; report their exclusion. Use explicit literal filesets for the named files (escape paths according to JJ fileset syntax rather than allowing wildcard expansion). Recheck the exact group with `jj diff` before committing. Never use an unscoped commit that would include unrelated work.

   Write the full dynamically composed message with the file-write tool under the target workspace's local `.tmp/` directory; ensure `.tmp/` is ignored, preserving existing ignore entries. Do not use OS-global temporary storage. To avoid shell interpolation of message contents, the shell tool may run a small local Python invocation that reads this UTF-8 file and passes it as a single argument to `subprocess.run(["jj", "commit", "-m", message, *selected_filesets], cwd=workspace_root, check=True)`. Set `workspace_root` to the verified absolute root and `selected_filesets` to the explicit owned group, never all paths. No direct Git executable or harness dispatcher is involved.

   Equivalent command shape (the message is dynamically composed, not prescribed):

```bash
jj commit -m "<message composed from the standards above>" <explicit-owned-filesets>
```

   With path selection, `jj commit` keeps the selected changes in the completed commit and moves remaining changes into a new working-copy change on top. It does not move bookmarks to that new working copy. Before the next logical group, create a distinct task bookmark there if needed; do not move the bookmark protecting a completed group. Verify completed commit contents and excluded paths after each group. If safely separating the existing change would rewrite work outside the authorized scope, stop and explain rather than rewriting it.

7. **Confirm** — run `jj status`, inspect each completed commit's paths and full description, and report commit/change IDs and subjects. Confirm task bookmarks protect the intended commits, the requested groups are no longer in the working copy, and excluded/unrelated changes remain untouched. A nonempty working copy containing those exclusions is expected, not a reason to commit them.

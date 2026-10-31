---
name: ce-commit
description: Save logical JJ changes with clear, repository-appropriate messages. Use when the user asks to commit or save changes.
---

# Commit Changes

Create local changes only. No push or PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each selected logical change has an explicit file list, verified description and immutable commit ID, and unrelated/excluded work remains intact. Stop if there is no selected work to save.

## Context and safety

Discover the absolute target workspace root. Run every JJ command with that root as actual cwd, e.g. `(cd "$workspace_root" && jj status)`, never relying on `-R`. Do not execute Git. Read applicable repository instructions.

Gather `jj root`, `jj status`, `jj diff --summary`, `jj diff`, `jj bookmarks list`, and `jj log -r '@ | @-'` in that cwd. Inspect conflicts, tracked changes and ignored/untracked files separately; ignored data is not protected by snapshots. Stop on conflicts or ambiguous ownership. Capture change/commit IDs and parent IDs. Verify the intended history head from the task and graph, normally the parent of a fresh working change, not an assumed default bookmark. Re-read identities and status before mutation if anything may have changed.

JJ has no staging step. Preserve descriptions, bookmarks, recovery references and existing isolation. An empty working change above saved work is normal. Do not create/move default or source bookmarks automatically. Create a non-conflicting feature bookmark on the verified saved change only if required by the task; otherwise report its change ID without inventing a branch requirement. This skill does not create or remove workspaces.

## Mandatory runtime message standard

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the FULL linked guide at runtime before composing. Compare SEVERAL recent subjects AND bodies using the task-verified history head:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Replace the placeholder with the verified immutable history head. Examine prefixes/packages, casing, tense, subject/body separation, wrapping and issue references. Repository-local syntax ALWAYS wins. With no history, explicitly report that and follow explicit instructions plus compatible Go guidance; never invent precedent or default to fixed conventional-commit syntax.

Communicate outcome and useful motivation/trade-offs. Preserve relevant known unit traceability and human/source provenance in compatible prose, without mandated subject suffixes or invented identities. Do not add Markdown, `Co-authored-by`, `Assisted-by`, or creator/model/harness attribution to resulting messages. Compatible local rules win.

### Verbatim Go source excerpts

The following source illustrations from https://go.dev/wiki/CommitMessage are subordinate to repository patterns. Go package syntax and examples are NOT templates to impose on other repositories.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.
>
> Please *don’t* use alternate GitHub-supported aliases like `Close` or `Resolves` instead of `Fixes`.
>
> To link a commit to an issue without marking it fixed—for example, if the commit is working toward a fix but not yet a complete fix—GitHub requires only that the issue is mentioned by number in the commit message. By convention, Go commits mention this at the bottom of the message using `For`, where `Fixes` might be expected, even if the number is also mentioned in the body of the commit message.
>
> For example:

```text
Refactor func Foo.
This will make the handling of <corner case>
shorter and easier to test.

For #12345
```

> It is common in other Git projects to use `Updates` instead of `For`, and that is acceptable too, even though it makes little sense (the commit does not update the issue). More precise phrasings are fine too. Don’t be too pedantic in code reviews: it’s not worth asking people to change from `Updates` or something else to `For`, or vice versa.
>
> ## Reverts
>
> You can roll back a change using the Gerrit `Revert` button. Gerrit will generate a description for you. Edit the description to add the Gerrit CL number being rolled back next to or instead of the Git revision number.
>
> Do not use the Gerrit UI to create a revert of a revert, as that notifies people right away. Instead, mail it as a new change, and in the description explain that it is a roll forward of CL NNNNNN which was rolled back by CL NNNNNN.
>
> ## Other repos
>
> For non-“go” repos (“crypto”, “tools”, “net”, etc), the subject is still the name of the package, but you need to fully-qualify the issue number with the GitHub org/repo syntax:

```text
cipher/rot13: add new super secure cipher

Fixes golang/go#1234
```

> Notably, the first line subject should **not** contain the `x/crypto/` prefix. We only do that for the issue tracker.
>
> ## Non-normative references
>
> - [Please heed my plea and write good CL descriptions for Go—and for any other project you work on.](https://groups.google.com/d/msg/golang-dev/6M4dmZWpFaI/SyU5Sl4zZLYJ)
> - [The CL description is a public document that explains to the future what has been done and why.](https://groups.google.com/d/msg/golang-dev/s07ZUR8ZDHo/i-rIsknbAwAJ)
>
> ## GitHub Pull Requests
>
> If you’re using GitHub Pull Requests, your commit message is constructed by GerritBot based on your PR’s title & description. See [How does GerritBot determine the final commit message?](https://go.dev/wiki/GerritBot#how-does-gerritbot-determine-the-final-commit-message)
>
> If somebody asks you to modify your commit message, you’ll need to modify your PR.

Quoted Gerrit/PR procedures describe the source project only; this local skill does not execute them.

## Workflow

1. **Select.** Enumerate named files only. Honor `exclude:<paths>`: excluded and unrelated work stays untouched. If no selected work exists, report that and stop; an empty tracked diff alone does not establish absence of untracked files.

2. **Group.** Use one change unless selected files clearly divide into distinct concerns (2–3 groups maximum), at file granularity without interactive hunk selection. Capture baseline identities and explicit paths. Do not rewrite shared or unrelated described changes without authority; stop if that would be required.

3. **Compose and validate.** Perform the full guide/history comparison above for each message. Validate subject AND body against the actual repository pattern, semantic outcome and compatible guidance, never a fixed template. Write the message with the file-write tool under absolute workspace-local `.tmp/`, never global temporary storage. Verify it is ignored and not selected.

4. **Save exactly the group.** If the current working change contains only this group and is safe to describe, run `jj describe --file <absolute-workspace-local-message-file>` in the absolute workspace root, then `jj new` to leave a fresh working change. Neutral inline equivalent: `jj describe -m "<message composed from the standards above>"`; prefer the file for multiline/literal shell-sensitive text. If other groups or excluded/unrelated files coexist, use noninteractive `jj split -m "<message composed from the standards above>" -- <explicit-paths...>` in that cwd. Pass the complete message as one literal argument using the shell tool's argument interface, or read the workspace-local message file and call `subprocess.run(["jj", "split", "-m", message, "--", *explicit_paths], cwd=absolute_workspace_root, check=True)` from Python; do not interpolate message text as shell code. JJ 0.46 split has no description-file option. Trailing paths select the group. Immediately inspect the selected change and remaining working change; never apply the selected description to the remainder. Never select `.`, all files, broad globs, excluded paths or incidental temporary state. Stop rather than rewrite unrelated shared history. On mutation failure inspect identities and graph before retrying.

5. **Confirm.** Re-read `jj status`, graph and full descriptions in the same absolute cwd. Verify saved immutable IDs, exact file diffs and messages, and that excluded/unrelated work remains intact. Report IDs, subjects, selected paths and remaining work/blockers. An empty working change is expected. No push, PR, destructive cleanup or optional history rewrite is implied.

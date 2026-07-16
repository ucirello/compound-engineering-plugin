---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# JJ Workspace Isolation

Ensure the current work happens in an isolated workspace without disturbing the user's main workspace. Create or select a Jujutsu workspace backed by the current JJ repository.

Order of operations: **detect existing isolation -> use a harness-native JJ workspace primitive when available -> use `jj workspace add`.** Never create a workspace the harness cannot see.

## Choose The Mode

- **New work**: create a new working-copy change whose parent is the chosen base revision, then create a local feature bookmark on that change.
- **Continue from a target**: create a new working-copy change whose parent is an existing bookmark, remote bookmark, PR source revision, JJ tag, change ID, or revision ID. This is the safe default for review fixes and follow-up work.
- **Edit an existing change**: create the workspace, then explicitly `jj edit` the mutable target only when the caller intends to amend that exact change.

`jj workspace add -r <target>` creates a new working-copy change with `<target>` as its parent, as if `jj new <target>` had been run. It does not edit `<target>`. Do not describe it as attaching directly to that revision.

## 1. Inspect Existing Workspaces

Use read-only inspection without snapshotting the current working copy:

```bash
jj --ignore-working-copy workspace root
jj --ignore-working-copy workspace list
jj --ignore-working-copy bookmark list --all-remotes
jj --ignore-working-copy log -r '@ | @-'
```

Match the current root and target revision against `jj workspace list`. If a suitable workspace already exists, locate it with `jj workspace list -T 'if(self.name() == "<workspace-name>", self.root() ++ "\n")'` and require exactly one nonempty absolute-path result before reporting and using that path. Stop on zero or multiple results. Do not create a workspace inside another workspace.

If that existing isolated workspace must be repositioned, use `jj new <target>` to preserve its current working-copy change and start a child on the target. Use `jj edit <target>` only for intentional direct amendment after applying the direct-edit checks below.

A generic alternate-workspace primitive may have incompatible semantics. Use a native harness primitive only when it explicitly creates a JJ workspace in this same JJ repository; otherwise use `jj workspace add` below.

If the current workspace already provides the requested isolation and target, work in place. Do not create a redundant or nested workspace.

## 2. Resolve The Revision

Resolve names before creating files. Accept JJ revsets and unambiguous bookmark, tag, change-ID, or revision-ID prefixes. Use `jj --ignore-working-copy log -r '<rev>'` and require exactly one revision. If a bookmark is conflicted or a prefix is ambiguous, stop and ask the user which target to use.

Map provider or caller naming at the boundary, then use only JJ names:

| Input identity | JJ form |
| --- | --- |
| local line of work | local bookmark `<name>` |
| provider source bookmark with a known remote | remote bookmark `<name>@<remote>` |
| named release | JJ tag `<name>` |
| full or abbreviated revision ID | revision ID, after exact cardinality validation |
| JJ change ID | change ID, after exact cardinality validation |

Do not preserve provider namespace wrappers or remote-name prefixes in newly created bookmark names. Preserve slashes that are part of the source bookmark's own name. Never guess whether an ambiguous slash-separated name is local or remote; inspect `jj bookmark list --all-remotes`.

For new work, prefer the project's configured or documented trunk bookmark. Otherwise inspect local and remote bookmarks instead of assuming fixed names:

```bash
jj --ignore-working-copy bookmark list --all-remotes
jj git remote list
```

Remote bookmarks are addressed as `<bookmark>@<remote>`. Fetch only when fresh remote state is useful and network access is allowed:

```bash
jj git fetch --remote <remote>
```

A failed fetch is non-fatal only when the user accepts the already-resolved local revision. Never substitute a different base silently.

Use JJ for every local repository operation, including workspace, revision, bookmark, description, synchronization, and publication operations. At the description-composition site below, follow its mandated message-history bridge; `jj git ...` remains JJ syntax.

### Pull Requests

Keep GitHub access through `gh`, but use it only to read PR metadata or interact with the PR. Supply the JJ backing store with `GIT_DIR="$(jj git root)"` on every `gh` invocation so this also works in non-colocated JJ repositories. Do not let `gh` create, switch, or mutate the local workspace.

1. Read the PR's source repository URL, source bookmark, and source revision ID with `GIT_DIR="$(jj git root)" gh pr view` or `GIT_DIR="$(jj git root)" gh api`; then inspect `jj git remote list`.
2. Normalize the GitHub repository URL and every configured JJ remote URL only for comparison (equate HTTPS and SSH/scp forms for the same host/path, and ignore a trailing `.git`). Require exactly one URL match and use that configured JJ remote name. Never assume `origin` or choose the first remote.
3. With the matched JJ remote, validate the source bookmark, fetch it directly with `jj git fetch --remote "<remote>" --branch "<validated-source-bookmark>"`, and resolve the authoritative source revision ID from GitHub metadata. Treat `<source-bookmark>@<remote>` as naming context, not content identity.
4. For a fork with no matching remote, ask before adding one with `jj git remote add <remote> <url>`, then fetch its source bookmark. Adding a remote changes shared repository configuration.
5. If the PR revision ID is already present locally, use it directly without creating or tracking a bookmark.
6. If URL matching is ambiguous or no JJ-visible revision can be obtained, stop rather than selecting an arbitrary remote or switching repository models.

Use `jj bookmark track <bookmark>@<remote>` only when the user wants a same-named local bookmark that follows future fetches. Merely reviewing or basing a child change on a remote bookmark does not require tracking it.

When the caller intends to update the PR, use the validated source bookmark name for the local bookmark, track the corresponding remote bookmark, move the local bookmark to the publishable change, and publish with `jj git push --bookmark <bookmark> --remote <remote>`. Confirm the destination repository and bookmark from GitHub metadata before pushing. Never invent a replacement bookmark for a PR source or use a local-workspace mutation command from `gh`.

## 3. Compose Names And Descriptions

Choose a unique ASCII workspace name and, for new work, a bookmark name derived from the work description. Follow the repository's active naming conventions and inspect existing workspace and bookmark names. Do not use a fixed namespace, prefix, or example name. Generated names, descriptions, and other visible artifacts must not contain product branding, tool or model names, badges, attribution, generation metadata, co-author attribution, or decorative footers. When validating a description against these constraints, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not validate against fixed message syntax or examples.

Compose the new change description from the requested work. At this composition site, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples. Resolve the JJ base to the underlying ID required by the message-history bridge, then inspect nearby messages with the mandated read-only `git log` command:

```bash
base_id=$(jj --ignore-working-copy log -r '<base-rev>' --no-graph -T 'commit_id ++ "\n"')
git log -n 10 --format='%s' "$base_id"
```

At every description composition, edit, validation, or recommendation site, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples.

Before passing a description to `jj workspace add -m`, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples.

If the description must be revised with `jj describe -m`, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples.

Before any later `jj commit -m` use, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples. Pass descriptions directly as arguments. Do not create an intermediate message file unless the content cannot be passed safely as an argument.

## 4. Choose A Workspace Path

Choose an absolute destination outside every existing workspace root. A sibling directory grouped under the current repository's parent is a good default. Do not put a JJ workspace inside a working copy: JJ snapshots working-copy files automatically, and nesting mixes workspace contents with tracked project content.

Create only the destination's parent directory, then let JJ create the destination. Refuse to reuse a non-empty path or a workspace name already shown by `jj workspace list`.

If an operation requires transient storage inside a JJ workspace, use exactly `$(jj workspace root)/.tmp`. Before creating or writing it, inspect the repository's root ignore rules and, if `.tmp/` is not covered, add `.tmp/` to the root `.gitignore` while preserving every existing entry. Outside a JJ repository, use only a local `.tmp` directory under the current working directory and ensure it is excluded from that directory's deliverable content before writing. If the applicable `.tmp` cannot be made safe, keep the content in memory or ask for an allowed local path. Never use OS-global scratch storage, environment-selected temp roots, home-directory caches, or global temporary-file APIs. A `.tmp` directory is scratch only; it is never the workspace destination.

## 5. Create The Workspace

Run the command against the current workspace root so repository discovery is unambiguous:

```bash
# The destination and description are derived above.
jj -R <current-workspace-root> workspace add --name <workspace-name> -r <base-rev> -m <change-description> <absolute-destination>
```

At this creation site, apply this guidance before replacing the neutral `<change-description>` placeholder: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not impose fixed message syntax or examples.

This preserves the current workspace's working-copy change and files. By default the new workspace copies the current workspace's sparse patterns; use `--sparse-patterns full` only when a full working copy is required.

For new work, create a local bookmark at the new working-copy change:

```bash
jj -R <absolute-destination> bookmark create <feature-bookmark> -r @
```

JJ has no current or selected bookmark. A bookmark follows rewrites of its target change, but it does not automatically advance when `jj new` or `jj commit` creates a child. Move it deliberately when the publishable tip changes:

```bash
jj -R <absolute-destination> bookmark move <feature-bookmark> --to <tip-rev>
```

For an existing target, `workspace add` already creates the recommended child change on that target. Do not create a duplicate local bookmark unless the workflow needs one.

### Directly Editing The Target

Use direct editing only when the caller explicitly wants to amend the target rather than add a child change:

1. Confirm the target is mutable and is not conflicted.
2. Compare it with every working-copy revision shown by `jj workspace list`. A revision cannot safely be the working-copy change of two workspaces; if another workspace already edits it, use that workspace or choose child-change mode.
3. Create the workspace as above, then switch its working-copy revision explicitly with `jj -R <absolute-destination> edit <target-rev>`.

Prefer child-change mode followed by `jj squash --into <target-rev>` because it keeps the new edits inspectable before amending the target.

After creation, verify and report the workspace name, absolute path, `@`, parent revision, mode, description, and bookmark if any. When validating or recommending a description, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not validate against or recommend fixed message syntax or examples.

```bash
jj -R <absolute-destination> workspace root
jj -R <absolute-destination> log -r '@ | @-'
jj -R <absolute-destination> bookmark list -r '@ | @-'
```

Then perform all requested work with the tool working directory set to `<absolute-destination>`. A shell `cd` in one tool call does not move later calls.

If creation fails because of permissions or sandboxing, stop and ask whether to work in the current workspace or resolve access. Use the host's concrete blocking question interface: `AskUserQuestion` in Claude Code (discover it with `ToolSearch select:AskUserQuestion` if needed), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi through the `pi-ask-user` extension. Fall back to numbered options only when the host has no blocking interface or the call errors. Never silently sacrifice isolation or retry inside the current working copy.

## Lifecycle

List and locate workspaces:

```bash
jj workspace list -T 'self.name() ++ "\t" ++ self.root() ++ "\n"'
```

For a selected name, filter with `jj workspace list -T 'if(self.name() == "<workspace-name>", self.root() ++ "\n")'` and require exactly one nonempty absolute-path result. Retain that validated path before any cleanup operation.

If JJ reports that the selected workspace is stale, run `jj -R <workspace-root> workspace update-stale` from that workspace after checking that its files do not contain work that must be recovered. `update-stale` reconciles a workspace whose working-copy state was changed by another operation; it is not a fetch or general refresh command.

Cleanup is two separate operations. `forget` removes the workspace's working-copy record from the JJ repository but does not delete files:

```bash
jj -R <another-workspace-root> workspace forget <workspace-name>
```

Delete the workspace directory separately, before or after `forget`, only after confirming the retained validated path is the intended workspace and its working-copy change and files are no longer needed. Never forget or delete the workspace currently being used, and never delete a bookmark as an implicit part of workspace cleanup.

## When To Create A Workspace

Create a workspace only when the current workspace does not already provide the requested isolation and a separate working directory is useful, such as reviewing a PR while keeping the current workspace free or running multiple features in parallel. For single-task work already isolated in the current JJ workspace, proceed in place.

## Integration

When another workflow requests workspace isolation, inspect existing JJ workspaces first. If the work is already isolated at the intended target, proceed there; otherwise create a workspace with names and a description derived from the work and repository conventions. When recommending that description, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply the project's active instructions first, then the syntax established by `git log`, and use Go guidance only when compatible. Do not recommend fixed message syntax or examples.

## Failure Rules

- **Name or destination exists**: locate it with the cardinality-checked `jj workspace list -T` name/path lookup above; reuse it only if exactly one result identifies the intended workspace. Otherwise stop or choose a new name/path.
- **Stale workspace**: inspect its files, then run `jj workspace update-stale` in that workspace. Do not recreate it over the stale path.
- **Target is already a working copy**: use the existing workspace or create a child change; do not `jj edit` it in a second workspace.
- **Missing remote revision**: use `jj git fetch` against a configured JJ remote. For a fork, request permission before `jj git remote add`.
- **Bookmark conflict or ambiguous revision**: stop for an explicit revision choice. Do not resolve by moving a bookmark arbitrarily.
- **Remote synchronization needed**: prefer `jj git fetch`, JJ remote bookmarks, and `jj git push`. In colocated repositories synchronization is automatic; in non-colocated repositories `jj git import` and `jj git export` are explicit synchronization tools, not workspace-selection mechanisms.

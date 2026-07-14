---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# JJ Workspace Isolation

Create or select a Jujutsu workspace backed by the current JJ repository. The public skill name remains `ce-worktree`, but the implementation is JJ-native: use revisions, bookmarks, workspaces, and working-copy changes throughout.

## Choose The Mode

- **New work**: create a new working-copy change whose parent is the chosen base revision, then create a local feature bookmark on that change.
- **Continue from a target**: create a new working-copy change whose parent is an existing bookmark, remote bookmark, PR head, tag, change ID, or revision ID. This is the safe default for review fixes and follow-up work.
- **Edit an existing change**: create the workspace, then explicitly `jj edit` the mutable target only when the caller intends to amend that exact change.

`jj workspace add -r <target>` has the semantics of `jj new <target>`: the new workspace's `@` is a new child of `<target>`. It does not check out or edit `<target>`. Do not describe it as attaching directly to that revision.

## 1. Inspect Existing Workspaces

Use read-only inspection without snapshotting the current working copy:

```bash
jj --ignore-working-copy workspace root
jj --ignore-working-copy workspace list
jj --ignore-working-copy bookmark list --all-remotes
jj --ignore-working-copy log -r '@ | @-'
```

Match the current root and target revision against `jj workspace list`. If a suitable workspace already exists, report its path from `jj workspace root --name <workspace-name>` and use it. Do not create a workspace inside another workspace.

If that existing isolated workspace must be repositioned, use `jj new <target>` to preserve its current working-copy change and start a child on the target. Use `jj edit <target>` only for intentional direct amendment after applying the direct-edit checks below.

A generic harness alternate-workspace primitive may use incompatible semantics. Use a native harness primitive only when it explicitly creates a JJ workspace in this same JJ repository; otherwise use `jj workspace add` below.

## 2. Resolve The Revision

Resolve names before creating files. Accept JJ revsets and unambiguous bookmark, tag, change-ID, or revision-ID prefixes. Use `jj --ignore-working-copy log -r '<rev>'` and require exactly one revision. If a bookmark is conflicted or a prefix is ambiguous, stop and ask the user which target to use.

For new work, prefer the project's configured or documented trunk bookmark. Otherwise inspect likely local and remote bookmarks rather than assuming `main` or `origin`:

```bash
jj --ignore-working-copy bookmark list --all-remotes
jj git remote list
```

Remote bookmarks are addressed as `<bookmark>@<remote>`. Fetch only when fresh remote state is useful and network access is allowed:

```bash
jj git fetch --remote <remote>
```

A failed fetch is non-fatal only when the user accepts the already-resolved local revision. Never substitute a different base silently.

### Pull Requests

Use the forge interface only to read PR metadata such as the source repository, source bookmark name, and source revision ID. Resolve the revision and create a JJ workspace rather than asking the forge interface to mutate the workspace.

1. Inspect the PR source metadata and `jj git remote list`.
2. If its repository already has a JJ remote, validate the source bookmark, fetch it with `jj git fetch --remote "<remote>" --branch 'exact:"<validated-source-bookmark>"'`, and resolve the authoritative PR revision ID from forge metadata. Treat `<source-bookmark>@<remote>` as naming context, not content identity.
3. For a fork with no matching remote, ask before adding one with `jj git remote add <remote> <url>`, then fetch its source bookmark. Adding a remote changes shared repository configuration.
4. If the PR revision ID is already present locally, it can be used directly without creating or tracking a bookmark.
5. If no JJ-visible revision can be obtained, stop rather than switching repository models.

Use `jj bookmark track <bookmark>@<remote>` only when the user wants a same-named local bookmark that follows future fetches. Merely reviewing or basing a child change on a remote bookmark does not require tracking it.

## 3. Choose A Workspace Path

Choose a unique ASCII workspace name and an absolute destination outside every existing workspace root. A sibling directory such as `<parent>/<repo-name>-workspaces/<workspace-name>` is a good default. Do not put workspaces inside a working copy: JJ snapshots working-copy files automatically, and nesting mixes workspace contents with tracked project content.

Create only the destination's parent directory, then let JJ create the destination. Refuse to reuse a non-empty path or a workspace name already shown by `jj workspace list`.

## 4. Create The Workspace

Run the command against the current workspace root so repository discovery is unambiguous:

```bash
# jj workspace add creates DEST and a new working-copy change on BASE.
jj -R <current-workspace-root> workspace add --name <workspace-name> -r <base-rev> <absolute-destination>
```

This preserves the current workspace's working-copy change and files. By default the new workspace copies the current workspace's sparse patterns; use `--sparse-patterns full` only when a full working copy is required.

For new work, create a local bookmark at the new working-copy change:

```bash
jj -R <absolute-destination> bookmark create <feature-bookmark> -r @
```

JJ has no current or selected bookmark. A bookmark follows rewrites of its target change, but it does not automatically advance when `jj new` or `jj commit` creates a child. Move it deliberately when the publishable tip changes:

```bash
jj bookmark move <feature-bookmark> --to <tip-rev>
```

For an existing target, the `workspace add` command above already creates the recommended child change on that target. Do not create a duplicate local bookmark unless the workflow needs one.

### Directly Editing The Target

Use direct editing only when the caller explicitly wants to amend the target rather than add a child change:

1. Confirm the target is mutable and is not conflicted.
2. Compare it with every working-copy revision shown by `jj workspace list`. A revision cannot safely be the working-copy change of two workspaces; if another workspace already edits it, use that workspace or choose child-change mode.
3. Create the workspace as above, then switch its working-copy revision explicitly:

```bash
jj -R <absolute-destination> edit <target-rev>
```

Prefer child-change mode followed by `jj squash --into <target-rev>` because it keeps the new edits inspectable before amending the target.

After creation, verify and report the workspace name, absolute path, `@`, parent revision, mode, and bookmark if any:

```bash
jj -R <absolute-destination> workspace root
jj -R <absolute-destination> log -r '@ | @-'
jj -R <absolute-destination> bookmark list -r '@ | @-'
```

Then perform all requested work with the tool working directory set to `<absolute-destination>`. A shell `cd` in one tool call does not move later calls.

If creation fails because of permissions or sandboxing, stop and ask whether to work in the current workspace or resolve access. Never silently sacrifice isolation or retry inside the current working copy.

## Lifecycle

List and locate workspaces:

```bash
jj workspace list
jj workspace root --name <workspace-name>
```

If JJ reports that the selected workspace is stale, run this from that workspace, after checking that its files do not contain work that must be recovered:

```bash
jj -R <workspace-root> workspace update-stale
```

`update-stale` reconciles a workspace whose working-copy state was changed by another operation; it is not a fetch or a general refresh command.

Cleanup is two separate operations. `forget` removes the workspace's working-copy record from the JJ repository but does not delete files:

```bash
jj -R <another-workspace-root> workspace forget <workspace-name>
```

Delete the workspace directory separately, before or after `forget`, only after confirming it is the intended path and its working-copy change and files are no longer needed. Never forget or delete the workspace currently being used, and never delete a bookmark as an implicit part of workspace cleanup.

## Failure Rules

- **Name or destination exists**: locate it with `jj workspace list` and `jj workspace root --name`; reuse it only if it is the intended workspace. Otherwise choose a new name/path.
- **Stale workspace**: inspect its files, then run `jj workspace update-stale` in that workspace. Do not recreate it over the stale path.
- **Target is already a working copy**: use the existing workspace or create a child change; do not `jj edit` it in a second workspace.
- **Missing remote revision**: use `jj git fetch` against a configured JJ remote. For a fork, request permission before `jj git remote add`.
- **Bookmark conflict or ambiguous revision**: stop for an explicit revision choice. Do not resolve by moving a bookmark arbitrarily.
- **Remote synchronization needed**: prefer `jj git fetch`, JJ remote bookmarks, and `jj git push`. In colocated repositories synchronization is automatic; in non-colocated repositories `jj git import` and `jj git export` are explicit synchronization tools, not workspace-selection mechanisms.

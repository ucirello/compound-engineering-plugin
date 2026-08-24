---
name: ce-worktree
description: Set up isolated JJ workspaces with a dedicated change. Use when starting isolated work or isolating an existing bookmark, PR, change, or revision.
---

# Workspace Isolation

Put the requested work in a dedicated JJ workspace and working-copy change without moving or rewriting another workspace's change. Preserve the requested GitHub target when isolating a PR.

**Done when:** the caller can continue from a dedicated workspace whose `@` is a distinct change with the intended parent, and the report names the workspace path, workspace name, change ID, parent revision, and publication bookmark when one applies. A blocker is also a complete result when isolation cannot be proved.

Use JJ for repository state and mutation. Do not use Git branches, worktrees, the index, checkout, switch, or another VCS's workspace operations. Read-only `git log` is allowed only where the mandated message guidance below calls for it, and `jj git` is allowed for Git remote interoperability. Use `gh` for GitHub metadata, not for checkout.

## Choose The Target

- **New work (default):** use the repository's configured trunk revision as the parent. If trunk is absent or ambiguous, resolve the intended base from the caller and repository conventions before mutation. Choose a meaningful workspace name and a Git-interoperable bookmark name from the work description.
- **Existing target:** resolve the named bookmark, change, or revision to one exact revision. The new workspace gets a fresh child change; do not edit, duplicate, or move the target change.
- **GitHub PR:** ask GitHub for the head repository, head bookmark, and head object ID. Match that repository to a configured JJ remote, adding a uniquely named remote only when the caller's requested isolation requires it, then fetch the head with `jj git`. Require the fetched remote bookmark to resolve to the reported head object ID. A fork, missing remote, ambiguous target, or changed head is a reason to stop rather than guess. For a non-colocated repository, point each `gh` invocation at the backing Git repository reported by `jj git root`.

JJ bookmarks name revisions; they do not own workspaces and there is no active or checked-out bookmark. The same bookmark or revision may therefore be the parent of multiple workspace changes. Never reject isolation merely because another workspace is based on the same target.

## Preserve Existing Work

Resolve the current workspace root with `jj workspace root`, then inspect `jj status`, `jj log -r '@|@-'`, and `jj workspace list`. Ordinary JJ commands snapshot visible working-copy files, so re-check the current status immediately before mutation.

If the current environment already identifies its workspace as dedicated to this session, and its `@` is a distinct change with the intended parent and no unrelated content, work there instead of creating another workspace. Otherwise leave its change, description, parentage, bookmarks, and files untouched and create a sibling workspace. A JJ workspace by itself is not proof of session isolation.

## Create The Workspace

Place new workspace directories under `<current-workspace-root>/.tmp/ce-worktree/workspaces/<workspace-name>`. Outside a JJ workspace, the only permitted temporary root is `<current-directory>/.tmp`; because no shared JJ repository can be resolved there, report the blocker instead of creating an imitation workspace. Never use OS-global temporary storage.

Before creating anything under `.tmp`, prove that the applicable ignore rules exclude it from JJ's working-copy snapshot. If they do not, offer to add only the needed `.tmp/` ignore rule. If exclusion is declined or cannot be proved, stop before creating the directory.

Create the workspace with one explicit parent so its working-copy change is new and distinct:

```bash
jj workspace add --name <workspace-name> --revision <target-revision> <workspace-destination>
```

Run subsequent repository actions against the new workspace. Confirm that its root and name are the requested ones, `@` is a new change, its parent is the exact target revision, and no source-workspace content moved.

For new work, create the chosen local bookmark at the new `@`. For an existing bookmark or PR, leave that bookmark on the target until completed work is ready to publish; report it as the publication bookmark so the downstream commit or PR workflow can move it deliberately. For a raw change or revision, create no bookmark unless publication was requested.

Describe the new working-copy change at this message site. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the requirement that the description identify the isolated work while adapting its form to runtime conventions. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example.

If workspace creation or verification fails because of permissions, sandboxing, stale state, target drift, or an unexpected existing destination, the requested isolation does not exist. Do not continue in the invoking workspace and do not retry another path automatically. Report the attempted workspace name and destination, exact target, unchanged source workspace, and failure. Use an available blocking question capability to offer working in the current workspace or stopping to resolve the blocker; if no such capability is available, present numbered options and wait.

---
name: ce-worktree
description: Set up isolated JJ workspaces with a dedicated change. Use when starting isolated work or isolating an existing bookmark, PR, change, or revision.
---

# Workspace Isolation

Put the requested work in a dedicated JJ workspace and working-copy change without moving or rewriting another workspace's change. Preserve the requested provider and GitHub target when isolating existing work.

**Done when:** the caller can continue from a dedicated workspace whose `@` is a distinct change with the intended parent, and the report names the workspace path, workspace name, change ID, parent revision, and publication bookmark when one applies. A blocker is also a complete result when isolation cannot be proved.

Use JJ for repository state and mutation. Do not use Git branches, worktrees, the index, checkout, switch, or another VCS's workspace operations. Read-only `git log` is allowed only where the mandated description guidance below calls for it, and `jj git` is allowed for Git remote interoperability. Keep provider operations in their provider interface, and use `gh` for GitHub metadata rather than checkout. Commands must remain compatible with Git Bash when that is the available shell.

## Resolve The Target

- **New work (default):** resolve the intended base from the caller, the configured trunk revision, and the repository's runtime conventions. Stop if the base remains absent or ambiguous. Derive meaningful, filesystem-safe workspace and Git-interoperable bookmark names from the actual work.
- **Existing target:** resolve the named bookmark, change, or revision to one exact revision. The new workspace gets a fresh child change; do not edit, duplicate, or move the target change.
- **Provider review or GitHub PR:** obtain the head repository, head bookmark, and head object ID from the provider. Match that repository to a configured JJ Git remote, adding a uniquely named remote only when the requested isolation requires it, then fetch through `jj git`. Require the fetched remote bookmark to resolve to the provider-reported head object ID. Stop rather than guess when the repository, remote, target, or head identity cannot be proved. For a non-colocated repository, point `gh` at the backing Git repository reported by `jj git root` when repository discovery requires it.

JJ bookmarks name revisions; they do not own workspaces, and there is no active or checked-out bookmark. The same bookmark or revision may therefore parent multiple workspace changes. Never reject isolation merely because another workspace is based on the same target.

## Preserve Existing Work

Resolve the current workspace root with `jj workspace root`, then inspect `jj status`, `jj log -r '@|@-'`, and `jj workspace list`. Ordinary JJ commands snapshot visible working-copy files, so re-check the current status immediately before mutation.

If the current environment identifies its workspace as dedicated to this session, and its `@` is a distinct change with the intended parent and no unrelated content, work there instead of creating another workspace. Otherwise leave its change, description, parentage, bookmarks, and files untouched and create a sibling workspace. A JJ workspace by itself is not proof of session isolation.

If the harness offers a native primitive that creates a JJ workspace backed by the same repository and makes its path available to the session, prefer it and verify the same done condition. A native Git-worktree primitive is not a substitute. Never create a workspace the harness cannot enter or manage.

## Create The Workspace

Resolve `<workspace-root>` with `jj workspace root` and place new workspace directories under `<workspace-root>/.tmp/rocketclaw/ce-worktree/workspaces/<workspace-name>`. Outside a JJ workspace, use `<current-directory>/.tmp/rocketclaw/ce-worktree` for local scratch only; because no shared JJ repository can be resolved there, report the isolation blocker instead of creating an imitation workspace. Never use `/tmp`, `$TMPDIR`, bare `mktemp`, `tempfile`, or another OS-global temporary location.

Before creating anything under `.tmp/rocketclaw`, prove that the repository's applicable ignore rules exclude it from JJ's working-copy snapshot. If they do not, offer to add only the needed ignore rule. If exclusion is declined or cannot be proved, stop before creating the directory.

Refresh the required Git remote through `jj git fetch`. A fetch failure is non-fatal only when the selected target already resolves locally and the caller did not require fresh provider state. Resolve the target to exactly one revision, then create a new working-copy change with one explicit parent:

```bash
jj workspace add --name <workspace-name> --revision <target-revision> <workspace-destination>
```

The placeholders above come from runtime state; do not substitute fixed names or example values. Run subsequent repository actions against the new workspace. Confirm that its root and name are the requested ones, `@` is a new change, its parent is the exact target revision, the source workspace is unchanged, and the harness can continue from the new path.

For new work, create the derived local bookmark at the new `@`. For an existing bookmark or provider review, leave its bookmark on the target until completed work is ready to publish and report it as the publication bookmark. For a raw change or revision, create no bookmark unless publication was requested. Bookmarks do not advance with descendant changes; the downstream publication workflow must deliberately move the applicable bookmark to the intended revision and push it with `jj git push` using the runtime-resolved remote.

Before composing, editing, validating, or recommending any change description, apply this rule: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed at runtime always win. Apply compatible Go guidance only to message quality, clarity, and structure. Derive the description from the actual isolated work and preserve dynamic tracker or provider tokens required by the active integration; do not impose a fixed prefix, type, scope, subject, body, layout, syntax, template, or example. Set the description with JJ and verify the resulting description with `jj log` before reporting success.

Do not add creator attribution, badges, bylines, generated-by text, co-authorship, sign-off, or model/harness attribution to the change description. If a machine-readable provider protocol requires an actor, use `ai:assistant` with display name `AI Assistant` only in its protocol fields, never as visible artifact branding. Preserve operational model and provider details when they are required to execute or verify the workflow.

If workspace creation or verification fails because of permissions, sandboxing, stale state, target drift, or an unexpected existing destination, the requested isolation does not exist. Do not continue in the invoking workspace and do not retry another path automatically. Report the attempted workspace name and destination, exact target, unchanged source workspace, and failure. Use an available blocking question capability to offer working in the current workspace or stopping to resolve the blocker; if no such capability is available, present numbered options and wait.

If creation partially succeeds, inspect `jj workspace list` before any recovery. Never overwrite a destination, forget a workspace, delete files, move an existing bookmark backward or sideways, or replace a conflicting bookmark merely to make setup succeed. Report the partial state and let the caller choose cleanup or recovery.

---
name: ce-worktree
description: Set up isolated, colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision, preserving harness ownership and session lifecycle.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace without disturbing the user's main checkout. Harness-created isolation is common: detect it before creating anything.

**Done when:** the caller's harness session is working in the verified isolated workspace, with its absolute path, registered name, revision and relevant bookmarks reported; otherwise report a blocker. Creation alone is not success.

**Order:** detect existing isolation → establish native harness lifecycle support → verify source and identity → explicitly create a colocated JJ workspace → verify colocation and adopt the session. Never create invisible harness state or fall back to direct Git execution.

## Step 0: Detect existing isolation first

Resolve the current absolute workspace root with `jj root`, then run subsequent JJ commands with that root as the actual working directory (a shell `cd` subshell or process `cwd`, never `-R` as a substitute). Inspect `jj workspace list`, the current workspace identity and the harness's native workspace inventory/session metadata. Resolve registered paths before comparing them. A subdirectory, submodule, or unrelated nested repository is not evidence of isolation.

- **Already isolated:** preserve its existing name and path, even if undated. Report them and work in place. Never nest a workspace simply to satisfy the naming convention below.
- **Existing-ref request in an isolated workspace:** verify the requested exact revision and current state; use that workspace only if changing its working revision is authorized and does not disturb other work. Otherwise stop for a decision, not nested isolation.
- **Not isolated:** continue below. Unknown ownership or ambiguous inventory is a blocker, not permission to create.

## Step 1: Establish harness ownership and lifecycle

Use the host's native worktree/workspace capability for ownership, tracking, navigation and cleanup. In OpenCode, use the available native worktree lifecycle and `session_move` capability to adopt a verified destination. A native create tool is suitable only if its documented contract supports the exact requested name/destination and **explicit `jj workspace add --colocate`**, plus verification below. Do not assume a generic worktree tool does this.

If the native lifecycle supports registering/adopting a shell-created JJ workspace, use that documented flow. If it cannot meet the naming, colocation, ownership or session-adoption requirements, report a safe compatibility blocker. Do not bypass lifecycle with an untracked shell workspace, a bridge helper, a direct Git operation, or another harness. Moving the shell's directory alone does not move a harness session.

## Step 2: Verify source and stable identity

**Modes:**

- **New work (default):** verify the repository's intended trunk/base and capture its exact commit ID. A remote refresh via `jj git fetch` is non-fatal for local-only repositories, but disclose failure and use a local base only when it is verified and consistent with caller intent. Never silently substitute a different base.
- **Existing bookmark, PR, tag or revision:** resolve the exact requested source and capture its commit ID. Preserve source bookmark names and PR tracking identity; the dated workspace identity does not rename them. For a PR, verify repository, head repository/remote, head bookmark and exact head commit, including fork push destination. Use JJ fetch/bookmark operations, not a detached transport placeholder or `gh pr checkout`. If resolution or fetch cannot establish the exact source, stop rather than retrieving another ref. If another workspace already serves that source, report its path and offer reuse; do not force takeover or disturb it.

Repository-scoped `gh` commands must execute from the absolute target workspace root with `GIT_DIR=$(jj git root)` in that directory. Do not execute the Git program, even for read-only discovery.

Before any creation attempt, capture **one local `YYYYMMDD` date** and persist it with task identity, source root, exact base commit, normalized slug, selected name/destination and ownership/session metadata in a receipt under the source workspace's absolute `.tmp/rocketclaw/` directory. All scratch and error captures stay under local workspace `.tmp`, never OS temporary storage. Reuse this receipt across retries, resumes and midnight; never recapture the date for the same creation attempt.

Normalize both generated and caller-selected names:

1. Derive a meaningful task kebab slug, `pr-<number>-<topic>` slug, or revision/topic slug. Caller-selected names go through the same normalization: lowercase, turn separators/punctuation into hyphens, collapse runs, trim edges, reject empty/unsafe path components. Never use a PID, randomness or a clock timestamp as identity.
2. Strip existing leading `YYYYMMDD-` date prefixes before adding the captured local date exactly once. An existing receipt's captured date wins across retries/resumes; a caller-selected date prefix does not trigger a second prefix or a fresh date capture. Do not rename an already-existing isolated workspace.
3. Form `<captured-date>-<meaningful-slug>`, for example fresh work `20261008-fix-email-validation`, PR work `20261008-pr-214`, or revision work `20261008-review-efcb657`. A caller name `fix/email-validation` normalizes to the first identity; an already dated caller name gets one captured-date prefix, never two. The registered workspace name **must equal the destination basename**.
4. Place the destination under an absolute source-local `.tmp/rocketclaw/workspaces/` parent, verified ignored before creation using repository ignore configuration and JJ's ignored/untracked inspection. Do not silently edit ignore rules or create under an unverified parent; obtain authorization if configuration must change.
5. Check **both** all registered workspace names/paths and filesystem destinations (including files, symlinks and stale directories). On collision use `-2`, `-3`, and so on, checking both inventories for each candidate. Do not overwrite, reuse or delete a collision. Recheck immediately before creation. A receipt may resume an already-created workspace only after exact identity/path/base/ownership verification; otherwise stop on ambiguity. Persist the selected identity so retries remain stable.

## Step 3: Create, verify, and adopt

Within the supported native lifecycle, execute from the verified absolute **source** root:

```bash
jj workspace add --colocate --name "$workspace_name" --revision "$verified_base_commit" "$absolute_destination"
```

The destination is absolute and its basename equals `$workspace_name`. An implicit/default colocation setting is insufficient. From the created absolute destination as actual cwd, run:

```bash
jj git colocation status
jj root
jj workspace list
jj log -r @ --no-graph
```

Require successful colocation status and verify the exact root, registration name/path and expected base relationship (the new working-copy change may sit above the captured base). Confirm the shared repository and source/PR bookmarks are unchanged. Record results in the receipt. Failed or uncertain verification is not completed isolation and must not trigger an automatic alternate creation attempt.

Complete native harness registration/ownership and move/adopt the active session into the destination (`session_move` in OpenCode), then verify the session directory. Resume workers only after adoption. Report absolute path, registered name, captured base/current revision, relevant bookmark/PR identity, colocation result and adoption result.

If creation, permission, sandbox, colocation or adoption fails, retain evidence/state and report the precise incomplete stage. Do **not** proceed in the original checkout: isolation was requested. Ask whether to work in place or stop and resolve the issue using an available blocking-question capability; if none exists or its actual call fails, present numbered choices and wait. Never probe another harness's tool names or retry denied operations through alternative paths.

## Owned cleanup and preserve-only unregistering

Creation does not authorize destructive cleanup. Native harness cleanup must honor these safeguards too; if its remove primitive cannot, stop rather than call it blindly.

1. Obtain explicit authorization for the exact disposable workspace. Verify the registered name, resolved absolute path, repository, task receipt and harness ownership; reject ambiguous, unrelated, referenced or non-disposable data. Destination containment alone is not proof of ownership.
2. Stop all workers/processes using it, except the controlled inspection below. Identify a verified surviving absolute workspace root for recovery evidence and session adoption.
3. From the target root while it still exists, inspect tracked changes, conflicts, ignored and untracked files, working-copy revisions and bookmarks. A JJ snapshot does not protect ignored/untracked files. Establish integration of all intended work and durable recovery refs; preserve recovery/best/archive bookmarks. Uncertain integration, unresolved conflicts, unrelated changes or valuable ignored/untracked files block removal. Copy necessary evidence and authorized recovery material outside the target into the surviving workspace's local `.tmp/rocketclaw/` and read it back before proceeding. Do not declare a disposable workspace based only on a clean tracked diff. Then move the harness session to that surviving root and leave the target in all shells/process cwd contexts **before** removal. Verify adoption and no remaining active session/worker/process references.
4. From the **surviving absolute root as cwd**, reverify exact registration/name/path and authorization, then run `jj workspace remove <verified-name>`. This is the destructive owned-workspace operation. **Never** implement removal as `jj workspace forget` plus filesystem deletion; never add a force-delete or direct Git fallback.
5. Verify both deregistration and filesystem disappearance, then reconcile native lifecycle metadata and record the outcome outside the removed target. A warning, command failure, remaining directory or registration is incomplete cleanup: retain remaining state/evidence, report it, and stop. Do not force-delete leftovers.

`jj workspace forget <verified-name>` is **only** unregister-and-preserve-files, with explicit preserve-only intent; report that files remain. It is not destructive cleanup and must not be followed by deletion. Bookmark deletion is a separate authorized operation, never implied by workspace removal; preserve recovery, best and archive refs.

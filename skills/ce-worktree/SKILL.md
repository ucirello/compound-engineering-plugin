---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision, preserving harness ownership and safe cleanup.
---

# Workspace Isolation

Ensure work happens in an isolated JJ workspace without disturbing the user's primary checkout. Existing harness isolation is the common case: reuse it, never nest another workspace merely because its name differs from the naming policy below.

**Done when:** the caller is working in a verified isolated workspace and its absolute path, registered name, revision and relevant bookmark are reported, or a blocker is reported. Creation is not successful until colocation and session navigation are verified.

Use current JJ commands only; do not invoke Git directly or Git-based helpers, even for inspection or recovery. Run every repository command with its working directory set to the target **absolute workspace root**, not with `-R` as a substitute. Keep scratch, receipts and errors under repository-local `.tmp/`. For repository-scoped GitHub operations, first export `GIT_DIR=$(jj git root)` in that workspace; use `gh` for metadata, not `gh pr checkout` or another operation that launches Git.

## 1. Detect and reuse existing isolation

Resolve `jj root` to an absolute physical path and inspect `jj workspace list`, `jj status`, and the current revision/bookmarks. Check the harness's session/worktree metadata and the caller's isolation receipt, if available. A directory name alone is not evidence of ownership or isolation; a default JJ workspace alone is not proof that the harness did not isolate it. If JJ is not initialized or the workspace/harness relationship is ambiguous, stop and report the compatibility blocker; do not initialize, convert, or create a hidden alternative automatically.

If already isolated, report its existing name and path and work there. Preserve its name, destination, harness ownership, and native cleanup lifecycle even when they predate the naming policy. Never rename an existing workspace just to add a date. For an existing-ref request, first verify the target and the current clean/conflict state. Only move to the target with an authorized `jj new <verified-target>` when doing so preserves existing work; do not discard changes or move an unrelated bookmark. Otherwise report the mismatch and ask. JJ permits multiple workspaces based on the same revision; do not impose Git's one-branch-one-worktree rule.

## 2. Resolve the mode and verified base

- **New work (default):** derive a meaningful task slug and verify the intended trunk/default bookmark and its resolved revision. Inspect remotes and bookmarks rather than assuming `main@origin`. Refresh the relevant remote with `jj git fetch --remote <verified-remote>` when appropriate. A missing remote or failed fetch may use a verified local base, but disclose that it was not refreshed; never silently invent a base.
- **Existing bookmark, tag, or revision:** resolve and record the exact intended revision. Preserve source bookmark names. Creating a workspace does not itself move or publish a bookmark.
- **PR:** obtain its number, head repository, head ref and exact head SHA with `gh`, with `GIT_DIR` exported as above. Fetch using JJ's supported remote/bookmark operations and verify that the resolved target matches the PR head. For a fork, verify the source remote and subsequent push destination; do not infer write permission or substitute the base repository's similarly named bookmark. If the head cannot be fetched and verified with supported JJ operations, report a blocker. Keep PR/source bookmark identities unchanged.

Do not compose a commit or alter its description as part of isolation. Bookmark creation or movement, if needed by the caller's later workflow, is separate from the workspace identity and must preserve that workflow's authorization and tracking requirements.

## 3. Allocate a stable dated identity

For **new** isolation, capture the local calendar date **once**, for example `date +%Y%m%d`, and persist it with the operation's receipt before attempting creation. Choose a meaningful slug from the task, PR (`pr-123`), revision, or caller context. Normalize it to lowercase filesystem-safe hyphenated words, trim separators, collapse repeated separators, reject empty/`.`/`..`/path traversal, and avoid opaque PID/random names. A supplied identity already prefixed with a valid `YYYYMMDD-` must not receive a second date prefix: reuse that operation identity on retry/resume, or extract its meaningful slug for a genuinely new operation using the newly captured date.

Use **the same identity** for the JJ workspace name and destination basename: `YYYYMMDD-slug`, at an absolute owned destination such as `<repository-root>/.tmp/workspaces/YYYYMMDD-slug`. Ensure `.tmp/` is ignored before creation using JJ's supported ignored-file inspection; if not, request or make only the authorized narrowly scoped ignore change. Do not create a second legacy workspace directory or use a global temporary directory.

Check **both** registered workspace names (`jj workspace list`) and filesystem entries, including symlinks, at the destination. If either collides with unrelated state, try `YYYYMMDD-slug-2`, then `-3`, and so on; name and basename must still match. Persist the selected name, absolute destination, date, verified base, ownership and status in a receipt outside the destination under local `.tmp/`. Retries/resumes reuse this reservation and inspect whether the prior operation completed; do not roll the date, add another date prefix, allocate another workspace, adopt an unrelated existing directory, or overwrite an existing entry. Concurrent collision failures require rechecking both namespaces before selecting and recording the next suffix.

## 4. Create through a compatible lifecycle

Prefer a native harness workspace primitive **only if** it can honor the verified JJ base, explicit colocation, exact dated name/destination, registration and session lifecycle. Native OpenCode worktree tools must not be assumed to create JJ workspaces or accept these controls. If incompatible, use supported JJ creation only when the harness can explicitly register/navigate/manage it; otherwise report the compatibility blocker rather than creating invisible state.

From the surviving absolute source workspace root, the JJ creation operation is:

```bash
jj workspace add --colocate --name <dated-identity> --revision <verified-base> <absolute-destination>
```

Then, with cwd set to the new absolute root, run `jj root`, `jj workspace list`, `jj status`, and `jj git colocation status`. Verify the exact registered name/path, expected base relationship and successful colocation. Unsupported `--colocate`, unsupported status verification, permissions, sandbox failures, partial creation, or mismatched registration are blockers, not permission to fall back to Git or non-colocated creation.

Move the session using the available native session-navigation capability (for example OpenCode `session_move` with the absolute destination), and establish worker cwd there before starting work. If navigation is unavailable, report the limitation and obtain an explicit caller handoff instead of claiming the active session moved. Record creation and verification evidence in the receipt. Report path, name, base/current revision, relevant bookmark and lifecycle owner to the caller.

On failure, do not proceed in the original checkout or retry an unrelated location automatically. Preserve partial-state evidence and offer the explicit choices to resolve the blocker, authorize work in the current checkout, or stop. Use an available blocking question capability; otherwise ask in chat and wait. Cleanup of partial creation follows the same guards below.

## 5. Preserve lifecycle and delegation boundaries

Harness-created isolation remains harness-owned: use its supported lifecycle and do not manually remove it behind the harness. This skill does not dispatch agents or select models. If a caller needs delegation, use native subagent capabilities subject to host permission; skill-requested delegation does not imply permission to override the inherited model. Do not introduce shell-based harness dispatch or bridge scripts. Retain support assets unrelated to workspace dispatch.

Keep the receipt available to the caller for retries and eventual cleanup. Workspace creation is not evidence that work was integrated, published, or safe to delete. Do not change PR/source bookmark names to match the workspace's dated identity.

## 6. Guarded cleanup and recovery

Cleanup is a separate authorized action, not an automatic consequence of finishing isolation. Before removing an agent-owned workspace:

1. Stop and join all workers using it; move active sessions and shell cwd to a verified **surviving absolute workspace root**. Confirm the harness lifecycle permits removal. Never remove a workspace still in use or a user-owned/ambiguously owned checkout.
2. Read back the receipt and verify the exact registered name, resolved absolute path, ownership and removal authorization against current registration and disk state. Do not select a target by basename, glob, date prefix or stale receipt alone. Reject symlink/path mismatches and any target containing the surviving workspace or evidence directory.
3. Inspect tracked changes, conflicts, untracked files **and ignored files** with current JJ status/diff and supported file inspection plus a read-only filesystem inventory. Include ignored caches, generated artifacts and nested data in the safety decision. A JJ snapshot does **not** protect ignored or untracked files. Unknown or valuable data blocks removal until explicitly preserved or otherwise resolved with authorization.
4. Verify integration into the intended destination, or preserve recoverable revisions with authorized durable recovery bookmarks/references. Record exact revisions, integration checks, registration, status, file inventory and recovery instructions outside the target under the surviving workspace's local `.tmp/`. Copy any required files and evidence there and **read them back** before deletion. A receipt inside the target, an unverified copy or a snapshot alone is not sufficient recovery evidence. Preserve unrelated work and never equate a pushed PR with verified integration.
5. From the surviving absolute workspace root, use `jj workspace remove <verified-name>` only after all guards pass. For harness-owned workspaces, use the supported native lifecycle only if it meets these same JJ and verification requirements; otherwise stop for the owner. Never force-delete a directory, invoke Git cleanup, or use recursive deletion as a fallback.
6. Re-read workspace registrations and inspect the filesystem: success requires **both** the exact name to be gone **and** the destination directory to have disappeared. Warnings, retained directories, partial removal, registration ambiguity or failed checks mean incomplete cleanup and are blockers. Preserve evidence and report the remaining state; do not escalate to force deletion.

`jj workspace forget` is **unregister-only**, preserving files; it is not a substitute for removal and must never be reported as successful directory cleanup. Use it only when that distinct action is explicitly intended and authorized, and report that the directory remains. Retain recovery evidence outside removed targets for the caller's recovery and audit needs.

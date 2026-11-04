---
name: ce-worktree
description: Set up isolated JJ workspaces — start fresh work from a verified base, or isolate an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a worktree by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its absolute path, registered name, revision, and applicable bookmarks have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a compatible harness-native workspace tool -> use native JJ with harness-session adoption.** Never create a workspace the harness cannot see. Never invoke the Git executable. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [Git migration guide](https://docs.jj-vcs.dev/latest/git-experts/).

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh working-copy change from a verified base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option. Create a task bookmark only when the caller's workflow requires one.
- **Isolate an existing ref.** Resolve the named bookmark, PR head, tag, or commit exactly and create a new working-copy change on it. JJ permits multiple workspaces based on the same revision; do not import Git's one-branch-one-worktree restriction. Preserve existing PR/source bookmarks and push targets; workspace naming must not rename them.

## Step 0: Detect existing isolation

Resolve the current absolute root with `jj workspace root`, then run every JJ command with its working directory set to that absolute root (`(cd "$workspace_root" && jj ...)`; `jj -R` alone is not sufficient). Inspect `jj workspace list` and the harness's workspace ownership/session information to identify the current registered workspace and whether isolation already exists. Do not infer isolation merely from a directory name or colocated metadata.

**Already isolated:** report its existing name, absolute path, revision, and bookmarks, then work in place. Reuse its verified existing name even if it is not date-prefixed or colocated; do not rename, recreate, or modify its metadata to enforce new-creation rules. In existing-ref mode, verify whether `@` (or an empty `@` directly above the target) is already aligned. Only align a clean workspace to the exact verified target when authorized; preserve unrelated tracked, ignored, untracked, or conflicted work and use the safe decision path below when alignment is unsafe. Do not nest workspaces. If existing isolation or harness compatibility is uncertain, report the blocker rather than guessing.

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native workspace primitive, use its supported colocated JJ capability, preserving its ownership and lifecycle contract. Apply Step 2's dated identity and exact verified base to the request; verify the resulting registered name, destination basename, revision, and `jj git colocation status` from its absolute root, then adopt it through the harness's supported session-move capability. Unsupported colocation or required naming is a compatibility blocker, not permission to use a Git-only tool or silently accept another name. Do not bypass harness ownership by creating a second workspace behind its back.

## Step 2: Native JJ creation

Only when there is no native workspace tool, Step 0 found no existing isolation, and the harness can adopt an externally created JJ workspace.

1. Record the source workspace's absolute root. Keep destinations and all temporary files under its local `.tmp/` (for example, `.tmp/workspaces/`). Ensure `.tmp/` is covered in the root `.gitignore` before creating anything; inspect the ignore rules locally, never with Git. Do not place artifacts in global temporary storage.
2. Capture the local creation date **once** as `YYYYMMDD`. Derive a meaningful kebab-case slug from the task, PR, or revision: `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing a dated name. Persist the selected identity/date in the caller's run record outside the destination before creation; retries, resumes, and midnight boundaries keep that selection, not a newly calculated date.
3. Use **one identity** for both the registered JJ workspace name and the destination directory basename. Check `jj workspace list` registrations and filesystem destinations, including dangling symlinks. On a collision with unrelated state, select `-2`, `-3`, etc. and record that selection before attempting creation. Never overwrite, use timestamps/PIDs/random suffixes, or silently choose a new identity after a failed attempt. On retry, first determine whether the selected workspace was already successfully created and can be safely resumed; unresolved partial state is a blocker.
4. Resolve the exact base to a verified commit ID. For new work, inspect the configured remote/default bookmark and repository instructions; refresh the selected bookmark with `jj git fetch --remote <verified-remote> --bookmark <verified-bookmark>` when applicable. A refresh failure is non-fatal only if a verified local base exists; disclose that it was not refreshed. Do not guess `main`, silently replace an unavailable requested ref, or fetch another ref as a substitute. For an existing bookmark/tag/revision, resolve that exact target. For a PR, run repository-scoped `gh` with `GIT_DIR=$(jj git root)` from the source root to verify its head repository, remote, bookmark, and commit; fetch that exact head with JJ and verify its identity. Preserve the PR's source bookmark and fork-safe push destination for the fix loop; workspace identity is not its push bookmark.
5. Create from the source workspace's absolute root, using the recorded name, absolute destination, and verified revision:

   ```bash
   (cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
   ```

6. From the created workspace's absolute root, run `jj git colocation status`, inspect the workspace registration and working-copy revision, and verify the name equals the destination basename. Do not rely on configuration-dependent colocation defaults. Adopt the absolute destination through the harness's supported session-move capability (for example, OpenCode `session_move`), then report the path, name, revision, bookmarks, and verified colocation. A successful creation without harness adoption is not completed isolation.

If creation, colocation verification, or session adoption fails, requested isolation is not established. Preserve any partially created state and report it. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission or compatibility issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, bypass a denial, or retry alternative paths automatically.

## Retiring a workspace

Completion alone does not authorize removal. Respect the user's cleanup authorization and the harness owner's lifecycle authority. Before deleting a run-owned workspace:

1. Stop its workers. Verify its exact registered name, absolute path, and run ownership; never remove unrelated, ambiguously owned, still-referenced, or non-disposable content.
2. Inspect its tracked changes, conflicts, and ignored/untracked files from its absolute root. Prove integration when the caller requires it. Preserve recovery bookmarks/references; copy required evidence outside the target directory and read it back before removal. JJ removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot.
3. Leave the target and move any active harness sessions to a surviving workspace through the supported session-move capability. From that surviving workspace's absolute root, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`, subject to harness-owned lifecycle authorization. JJ manages colocated metadata; do not perform separate Git cleanup.
4. Verify both deregistration and directory disappearance. A successful exit alone is insufficient: directory-deletion failures can be warnings. On failure or incomplete cleanup, preserve remaining state and report the blocker; never force-delete or fall back to Git removal. Keep bookmark deletion separate and retain best/archive/recovery bookmarks and references still needed.

Use `jj workspace forget <verified-workspace-name>` **only** for an authorized unregister-only operation that preserves the files, never as a prelude to directory deletion.

---
name: ce-worktree
description: Set up isolated colocated Jujutsu workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure work happens in an isolated workspace without disturbing the user's main checkout. Most coding harnesses provide isolation at session start, so **detect existing isolation before creating anything**.

**Done when:** the caller is working in an isolated workspace, existing or newly created, and its absolute path, registered name, revision, and relevant bookmarks have been reported, or a blocker has been reported instead.

**Order:** detect isolation -> prefer supported harness-native colocated JJ creation -> explicit colocated JJ creation only if the harness can adopt it. Never create invisible workspace state or fall back to a Git-only worktree.

**Two modes:**

- **New work (default):** create a fresh working-copy change from a verified base. This is what `ce-work` and `ce-code-review` use when the user chooses isolation. A workspace identity is not a bookmark name; create a task bookmark only when required by the workflow.
- **Existing ref:** resolve the caller's bookmark, PR head, or revision to an exact verified revision. Preserve existing PR/source bookmarks and their push targets. JJ allows separate working-copy changes above the same revision; do not import Git's one-branch-one-worktree restriction or move a source bookmark merely to isolate it.

Use [JJ workspace documentation](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), the [Git migration guide](https://docs.jj-vcs.dev/latest/git-experts/), and the [command table](https://docs.jj-vcs.dev/latest/git-command-table/). Execute workspace behavior agentically with JJ, not workspace bridge scripts.

## Step 0: Detect existing isolation

Resolve the current workspace's absolute root, then run JJ with that root as the command's working directory:

```bash
workspace_root=$(jj workspace root)
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj log -r @ --no-graph)
(cd "$workspace_root" && jj git colocation status)
```

Match the current absolute path to its registered JJ workspace and consult the harness's isolation metadata and ownership. A subdirectory, submodule, or the mere presence of a repository is not proof of isolation. If ambiguous, report a blocker rather than guessing.

If already isolated, **reuse its verified existing name**, even when not date-prefixed. Report root, name, revision, bookmarks, ownership, and colocation state. Do not rename, recreate, nest another workspace, or silently change colocation to enforce new-creation rules. An unmet required capability goes through the safe decision path below. In existing-ref mode, verify alignment with the requested target; an empty `@` directly above that target is already aligned. Only align a clean workspace when authorized. Preserve unrelated tracked, ignored, and untracked work and conflicts; uncertain or unsafe alignment is a blocker, never a reset or discard.

## Step 1: Select a stable dated identity and verified base

For **every newly created workspace**, including caller-selected and harness-native names:

1. Capture the local creation date **once**, as `YYYYMMDD`, and retain it with the selected identity in the caller's run state. Preserve the identity across retries, resumes, and midnight boundaries; do not recalculate on each attempt.
2. Derive a meaningful kebab-case slug from the task, PR, or revision: `fix-email-validation`, `pr-214`, or `review-efcb657`. Normalize caller-supplied names; strip an existing date prefix before applying the captured creation date to avoid double-prefixing. On resume preserve the already selected date and identity. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Never substitute timestamps, PIDs, or random identifiers.
3. Use **one identity** for the registered workspace name and destination directory basename. Preserve the caller's existing absolute local `.tmp/` parent layout; otherwise use `<source-root>/.tmp/workspaces/<identity>`. Ensure `.tmp/` is ignored in `.gitignore` before creation. All temporary, fallback, and error artifacts belong under local `.tmp/`, never OS-global temporary storage.
4. Check both JJ registrations and filesystem destinations for collisions. Append `-2`, `-3`, etc. to the dated slug for both name and basename, never overwriting state. Persist the chosen suffix across retries. Reuse matching already-created retry state only after verifying path, ownership, base, and colocation; unrelated or partial state is a blocker, not permission to recreate it.
5. Verify an exact base revision before creation. For fresh work inspect the configured remote's default/trunk bookmark, falling back to a verified local base if refresh is unavailable. Refresh with `(cd "$workspace_root" && jj git fetch --remote "<verified-remote>")` when appropriate. A missing remote or failed fetch is non-fatal only if a usable local base is verified and the offline/stale condition is reported. Do not guess that `origin` or `main` exists.
6. Resolve existing refs unambiguously through JJ. For PRs verify repository, head repository, remote, head bookmark, and exact commit; fetch the head with JJ and resolve it before creation. Preserve the PR source bookmark and fork-safe push mapping, not a replacement bookmark or detached Git checkout. Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> --json headRefName,headRefOid,headRepository,headRepositoryOwner)` and the same preamble for other `gh` operations.

## Step 2: Prefer the harness-native lifecycle

Use the harness's supported **colocated JJ** creation capability when available, requesting the selected dated identity, matching absolute destination basename, and verified base. Verify actual registration, name, path, base, and `jj git colocation status` from the resulting absolute root. A request alone is not verification. Adopt the workspace with the harness's supported session-move capability before working there.

If the primitive cannot guarantee required naming or colocation, report a compatibility blocker through the safe decision path. Do not silently create a noncompliant workspace, use another harness's dispatcher, or bypass native ownership/lifecycle authority. Existing isolation retains its existing name.

## Step 3: Explicit JJ creation when supported

Only when Step 0 found no isolation, no supported native creation capability exists, and the harness supports adopting an agent-created JJ workspace:

```bash
# Values are verified; destination is absolute and its basename equals workspace_name.
(cd "$workspace_root" && jj workspace add --colocate \
  --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
(cd "$absolute_destination" && jj workspace list)
(cd "$absolute_destination" && jj log -r '@ | @-' --no-graph)
```

Verify exact name/path, registration, base relationship, and colocation. Move the active harness session to the absolute destination through its supported session-move tool, then run work with that root as the command's working directory. `jj -R` does not set the working directory. Report identity, path, base, revision, and relevant bookmarks. Do not mutate bookmarks to match the workspace name.

If creation, naming, colocation verification, or adoption fails, including sandbox/permission denial, isolation is not established. Do **not** work in the original checkout, retry alternate paths automatically, use Git-only creation, upgrade tools, or evade permissions. Use the safe decision path.

## Retirement and unregister-only operations

Completion alone does not authorize deleting a user's workspace. Respect explicit cleanup authorization and harness-owned lifecycle authority; when the harness owns it use its lifecycle with the same verified JJ removal and safeguards. Before retiring an authorized run-owned disposable workspace:

1. Stop and await all workers and processes using it. Leave the target directory and move all active harness sessions to a surviving workspace before removal.
2. From the surviving workspace's **absolute root**, verify the exact registered target name, absolute path, run ownership, and absence of remaining session/workflow references. Never remove unrelated, ambiguously owned, still-referenced, or non-disposable content.
3. Inspect target tracked changes, conflicts, ignored and untracked content from its absolute root. Prove integration when required by the workflow. Preserve best/archive/recovery bookmarks and needed references. Removal snapshots working-copy state, but ignored files and content left untracked are not protected by that snapshot.
4. Copy required evidence, receipts, recovery information, and needed ignored/untracked artifacts **outside the target**, into surviving local `.tmp/` storage; read back the copies before removal. If integration, ownership, recovery, evidence, or disposal safety cannot be proved, stop and report the blocker.
5. Remove through JJ, not unregister-then-delete:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
   (cd "$surviving_workspace_root" && jj workspace list)
   ```

6. Verify **both** exact deregistration and disappearance of the absolute directory. Successful exit alone is insufficient because deletion failures can be warnings. On failure or incomplete cleanup retain remaining state and report the blocker; never force-delete or fall back to Git worktree removal.

Use `(cd "$surviving_workspace_root" && jj workspace forget "$verified_workspace_name")` **only for an explicitly intended unregister-only operation preserving files**, after verifying ownership and lifecycle authority. Report the retained path; do not follow with directory deletion. Bookmark deletion is a separate authorized decision, never an automatic cleanup side effect; preserve recovery and still-needed references.

## Safe decision path

Report the precise blocker, offer “work in the current checkout” versus “stop and resolve the compatibility or permission issue,” and wait for the user's choice. Use the host's blocking question tool already in the current tool list (match by capability, not host-specific name). Presence in that list proves availability; never call a user-facing question tool merely to discover it. If listed but unloaded, use the host's discovery primitive to load the capability, not another host's tool name. Only if no matching tool is listed or a real question call errors, present numbered options in chat and wait. Never skip confirmation or silently weaken requested isolation.

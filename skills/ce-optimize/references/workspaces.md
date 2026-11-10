# Native JJ experiment workspace lifecycle

Run every repository command from its target **absolute workspace root**, by setting shell cwd or `(cd "$workspace_root" && ...)`; never use `-R` as a substitute. Resolve the root with `jj root`. Never invoke Git directly, even for status, history, fallback, packing or cleanup. For repository-scoped GitHub commands export `GIT_DIR=$(jj git root)` from that root before `gh`.

Keep all new state, prompts, measurement scratch and errors under the absolute workspace root's `.tmp/ce-optimize/`, with new ledgers in `<spec-name>/` as resolved in `references/persistence.md`; never use OS-global temporary storage or automatically relocate a pre-existing ledger. Harness durable state may retain a reference or receipt to the ledger. Preserve harness-owned isolation. Inspect `jj workspace list` and the ledger before creating isolation. Reuse only a verified workspace owned by this exact experiment at its recorded path/base; do not reset reused workspaces or clean their files. Concurrent experiments require independent workspaces, not shared edits.

Before new creation, verify supported harness adoption, navigation and lifecycle management for the requested colocated JJ workspace; unavailable support is a compatibility blocker. For new isolation, capture local `YYYYMMDD` once with `date +%Y%m%d` and persist it in the ledger. Derive a meaningful normalized task slug and experiment index. Form `YYYYMMDD-optimize-<spec>-exp-<NNN>` without a double date prefix; use the identical identity as workspace name and destination basename beneath the surviving root's `.tmp/workspaces/`. Check **both** all registered names and disk paths; suffix collisions `-2`, `-3`, etc. Persist the chosen name/path before launch so retries/resumes keep their identity. No PID/random substitute. Existing isolation and source/PR bookmarks retain their names.

Resolve the optimization bookmark to a unique verified immutable base with `jj log -r '<optimization-bookmark>' --no-graph -T 'commit_id'`; stop on absent/ambiguous/conflicted bases. From the surviving absolute root create:

```sh
jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination"
```

Then from the new absolute root run `jj git colocation status`, verify registration/name/path and base, and record evidence. Adopt it through supported native session navigation or an explicit authorized handoff; verify each worker's absolute cwd before launch. Unsupported naming, colocation or adoption is a compatibility blocker, never a Git fallback. Copy only explicitly configured shared files after validating source/destination containment and symlinks; never overwrite existing user files. Count registrations and pending owned creations for the concurrency budget.

## Guarded removal

Before removal, stop/join all workers using the workspace and move any session out to a surviving absolute root. Require explicit authorization covering the exact owned name/path and disposal of its contents (the approved experiment lifecycle may provide this authorization); unknown ownership or retained references blocks cleanup.

Copy logs, `result.yaml`, metrics, decision evidence and needed files outside the target to the surviving root's local `.tmp/`, then read them back. Record immutable candidate/base/integration IDs and create/verify recovery bookmarks for unintegrated work; verify winning changes actually appear in the integration revision. Inspect `jj status`, `jj diff --summary`, conflicts, tracked files and a filesystem inventory including ignored/untracked files. A JJ snapshot does **not** protect ignored/untracked content. Preserve such content outside the target and verify it, or obtain explicit authorization for its disposal. A recovery bookmark alone does not satisfy this check.

Only after all checks, from the surviving absolute root:

```sh
jj workspace remove "$verified_workspace_name"
```

Verify both deregistration with `jj workspace list` and absence of the exact directory. Warnings, remaining files, active sessions, uncertain integration, missing recovery or incomplete evidence are cleanup blockers; retain the workspace and report it. Never force-delete, prune, reset, or use a Git/manual-deletion fallback. `jj workspace forget` is **unregister-only**, preserves files, and must never be described as removal or successful cleanup. Keep recovery bookmarks until separately authorized to delete them.

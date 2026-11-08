# Native experiment workspace lifecycle

Use latest JJ, never the Git executable. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace . Every JJ call runs with cwd at the target absolute workspace root, not merely `-R`. Repository-scoped GitHub commands use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

1. Detect existing isolation first; reuse its verified name, path and harness lifecycle unchanged. Do not rename/recreate existing isolation to enforce new naming or colocation. For new harness isolation request supported colocated JJ creation and the dated identity below, then verify both; unsupported naming/colocation is a blocker, not permission to bypass ownership.
2. Resolve source absolute `workspace_root`, verify the optimization bookmark's exact base with `jj log`, and persist its immutable commit ID as `verified_base`. All temporary storage belongs under the source root's ignored `.tmp/`; ensure `.tmp/` is ignored before creation.
3. Capture local `YYYYMMDD` once per new workspace, persist it in the ledger and preserve across retries, resumes and midnight. Derive a meaningful kebab slug such as `optimize-parser-exp-003`, `pr-214` or `review-efcb657`. Normalize caller names without double date prefixes. Use one identity `YYYYMMDD-<slug>` for registered name AND destination basename under the absolute source `.tmp/rocketclaw/optimize/` parent. Check `jj workspace list` and destinations; suffix collisions `-2`, `-3`, never overwrite/reset. Reuse recorded existing workspaces only after proving identity, ownership and base. Preserve PR/source bookmarks.
4. From the source root create and verify:

   ```sh
   (cd "$workspace_root" && jj workspace add --colocate --name "$persisted_dated_name" --revision "$verified_base" "$absolute_owned_destination")
   (cd "$absolute_owned_destination" && jj git colocation status)
   ```

   Verify registration, exact root and base too; record identity/path before dispatch. Copy declared shared files and required environment resources only after resolving symlinks and proving source/destination containment; preserve relative layout, never replace existing content. Apply configured per-experiment ports and mitigations.
5. Retirement is separately authorized, not implied by completion. Stop workers and pending references, leave the target and move any active OpenCode session to a surviving workspace. Prove exact registered name, absolute path, run ownership and disposal authorization. For winners prove integration; retain recovery bookmarks/revisions. Copy required markers, metrics and evidence outside the target and read them back. Inspect `jj status`, conflicts, tracked changes, and filesystem ignored/untracked content, which removal's snapshot does not protect. Preserve unrelated, ambiguous, still-referenced or non-disposable content; do not remove it.
6. From a surviving absolute root only, run `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Verify BOTH deregistration in `jj workspace list` and directory disappearance; success can contain deletion warnings. Preserve remaining state and report failures, never force-delete or use another removal route. `jj workspace forget` is unregister-only preserving files. Bookmark deletion is separate: retain best/archive/recovery and needed references. Harness-owned workspaces remain under harness lifecycle authority.

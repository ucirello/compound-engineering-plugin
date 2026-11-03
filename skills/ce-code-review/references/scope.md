# Determining the reviewed diff and scope

## Stage 1: capture exact scope

Resolve `workspace_root` once with `jj root` from the current absolute cwd. Every JJ command thereafter executes `(cd "$workspace_root" && jj ...)`, including helpers, reads, fetches and failure paths, never merely `-R`. Root-relative paths stay root-relative; do not rewrite path strings to simulate cwd. No direct Git executable, including history, patch parsing, pickaxe, transport, or ignore queries. Git-format patch data from `jj diff --git` is supported.

Repository-scoped GitHub commands use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. They never check out a PR. Review target selection is not mutation permission. Any required fetch is explicit JJ transport; never move `@` to review another tree.

- **`base:`:** reject a simultaneous PR/branch target. Resolve exactly the supplied base to one commit ID using `jj log --no-graph -r '<base>' -T 'commit_id ++ "\n"'`; capture current `@` ID as head. Do not recompute a merge base for an explicit base.
- **PR:** first query `gh pr view <target> --json state,title,body,files`. Closed/merged skips. Delegate the conservative trivial-automation judgment on the cheapest permitted suitable model, inheriting when overrides are forbidden; doubt means review. A missing delegate cannot prove triviality. Drafts are reviewed. Skips return plain reason or `{"status":"skipped","reason":"..."}` in agent mode. Then query title/body/baseRefName/baseRefOid/headRefName/headRefOid/isCrossRepository/url/files/reviews/comments. Preserve prior-comment detection and metadata for later stages.
- **Local alignment:** require verified matching bookmark, non-fork source, and PR head ancestry in the current workspace (`jj log --no-graph -r '<pr-head> & ::@' -T commit_id`). A matching name alone is not enough. An empty `@` above the PR head may be aligned; inspect `@-` bookmarks and PR metadata. Local scope includes all captured working-copy changes.
- **Remote PR:** use `gh pr diff <target> --color=never`, saving and checking its exit before filtering. Never fall back to workspace checkout. Best-effort `jj git fetch --remote <verified-source> --branch <head-name>` and corresponding base fetch, using the actual fork source for fork PRs. Resolve the fetched head and base IDs and compare to metadata OIDs. Never substitute a same-named origin branch or default ref. If unavailable/mismatched, unset the corresponding `PR_HEAD_REF`/`PR_BASE_REF`, use provided hunks only and report degraded coverage. Logical `BASE=pr:<target>` is not a diffable ID.
- **Branch:** prefer its open PR metadata. Otherwise resolve exactly the named local/remote bookmark (fetch via JJ only when needed). Review without checkout. The head is that verified commit, not `@`, except a verified current-bookmark target follows local scope. Select the repository's actual default/base from metadata/project intent, not a hardcoded main/master. Resolve a unique common ancestor with `jj log --no-graph -r 'heads(::<base> & ::<head>)' -T 'commit_id ++ "\n"'`. Multiple/absent ancestors are a scope error, not permission to select one arbitrarily.
- **Standalone:** resolve the current bookmark's PR/base/default from metadata and repository instructions. Capture the unique common ancestor as above and current workspace head. If no base resolves, stop: a single-working-change diff would silently omit committed work.

Capture immutable `DIFF_A`/`DIFF_B` full IDs once for every local and remote path. Store scope mode, source/base/bookmark provenance and endpoint IDs in run metadata; use these same IDs for helper, peer, every reviewer, validator and receipts. Recheck local workspace hasn't changed before treating workspace reads as head reads; if it changed, read captured revision files or report incomplete scope. Never replace a multi-commit range with `jj diff -r @`.

From the target absolute root collect `jj diff --name-only --from "$DIFF_A" --to "$DIFF_B"` and `jj diff --git --context=10 --from "$DIFF_A" --to "$DIFF_B"`. Remote hunk-only scope uses the saved API diff, never unrelated local endpoints. Retain a private full patch for mechanics, but remove deleted-file body hunks from reviewer prompts while retaining deletion headers. Read a deleted body only as needed with `jj file show -r "$DIFF_A" '<root-relative-path>'`. Preserve executable modes and binary markers.

JJ automatically tracks eligible new files; inspect `jj status` and file list, and explicitly report ignored/untracked paths excluded from captured scope. Never add files just to review them. Do not claim these files were reviewed if absent from the captured tree.

## Stage 1b: deterministic scope facts

Invoke retained `scripts/review-scope.py` directly from the absolute workspace root:

```sh
(cd "$workspace_root" && python3 "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --docs-root "<root>" --scope-mode "$SCOPE_MODE")
```

Always pass both endpoints, including empty strings on failed remote resolution, so failure closes rather than comparing against the local tree. Do not estimate counts or reproduce the helper's mechanics in agent prose. The helper counts added + deleted production/test executable lines, preserves root-relative rename destinations, executable modes and binary/uncounted files, and separates whole-file deletions into `deleted_files`, `deleted_exec_nontest_lines`, and deletion band. The **200 production executable changed-line floor** forces full; whole-file deletions are banded separately and do not alone force full. `hard_block_full` and unknown scope are floors, never a lite award. `silent_pass_classes` forbid lite. All other path signals are prompts for consequence judgment, not automatic selection.

`declared_packs` is local config-only evidence (resolver `--declared-only`, no cache/network); remote scope returns null. Local unknown means inspect `packs:` yourself. `pack_roots` stays zero. Use `test_files_changed`, `agent_surface`, `has_learnings_corpus`, declarations, and path signals under the depth and persona rules. Read the depth gate before later references.

## Stage 1c: criteria and run artifacts

Enumerate `CODING_STANDARDS.md`, `AGENTS.md`, and `CLAUDE.md` at every depth in the **captured reviewed tree**, using `jj file list -r "$DIFF_B"` and `jj file show -r "$DIFF_B" <path>` from the root. Keep only ancestors of changed paths. Every governing standards file applies; instruction files supply criteria only where no standards file governs. Never grade a file against both kinds. Packs are separate learning sources, not criteria. An uncertain search is coverage unknown, not absence.

Create an owned private run directory under absolute `$workspace_root/.tmp/reviews/<run-id>`; refuse symlink/ownership ambiguity. No OS temp/TMPDIR fallback; outside JJ use absolute current directory `.tmp`. Run IDs may use local time and randomness (workspace names have separate rules). All paths/depths write artifacts there. Stage log is `<run-dir>/stages.jsonl`, written by retained `run-log.py`:

```sh
python3 "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Later transitions use `--end <stage> --start <stage>` with counts/facts. Lite/focused: scope→review→receipt, peer overlaps focused review. Full: scope→select→dispatch→validate→merge→report, peer overlaps dispatch. Fold logging into existing shell calls, not separate waiting turns. Summarize at receipt.

## Stage 1d: trusted review policy

Read applicable root/ancestor `REVIEW.md` from captured base `DIFF_A`, never the reviewed head. Root standalone `@<path>` includes are read once, one level deep, from that same base; skip includes already read as criteria. Policy governs severity, skips, evidence and checks; it is not criteria. Stage at `<run-dir>/review-policy.md` with source paths and governed paths. Missing policy is complete absence; unread policy is a Coverage gap. When this change edits/adds/deletes policy, explicitly state the change's policy version was not applied.

Expose outcome-oriented progress via native task tracking when available, otherwise normal concise updates. No simulated task list or blocking questions.

# Stage 1: Capture review scope

Resolve the target from explicit `base:`, PR URL/number, branch/revision, or current workspace. Set `workspace_root` to the absolute `jj workspace root`. Every JJ command below runs with that absolute root as cwd: `(cd "$workspace_root" && jj ...)`. A repository selector alone is insufficient. Repository-scoped GitHub calls run `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Never invoke Git directly, even for history, diff parsing or fallback.

Capture concrete immutable commit IDs before review. Resolve each endpoint with `jj log --no-graph -r '<verified-revision>' -T 'commit_id ++ "\n"'` and require exactly one result. Resolve the actual project/default base from project instructions, remote metadata and bookmarks; never guess `main`. Fetch only the verified repository/remote and bookmark when needed with `jj git fetch --remote <verified-remote> --bookmark <verified-bookmark>`. Resolve a unique common ancestor using `heads(::<base-ref> & ::<head-ref>)`; ambiguity or missing base stops review, not a fallback to the working-copy parent. Capture that ancestor once as `BASE` and the exact reviewed head once as `HEAD`; no later helper may recompute or substitute a merge base.

## Scope modes

- **Explicit base/current workspace:** verify the requested base, or resolve the default base and unique common ancestor. Capture the current `@` commit ID after JJ snapshots it, including tracked working-copy changes. JJ has no staging area. Set `local-aligned` and compare captured `BASE` to captured `HEAD`.
- **PR:** read number, title, body, files, base/head repository identity, base/head bookmark and exact OIDs with repository-scoped `gh pr view --json ...`. Scope alone never authorizes checkout, editing, pushing or PR mutation. Local alignment requires matching head bookmark/repository and the PR OID to be an ancestor of current `@`; verify with JJ revsets, not a same-name assumption. An empty `@` directly above the exact head is aligned. If aligned, local committed and tracked working-copy changes are canonical; do not mix in remote hunks. Otherwise select `pr-remote`.
- **PR remote:** obtain `gh pr diff <target> --color=never` into a local run file, checking its exit status before processing. Failure stops review rather than reading the checkout. Fetch head/base best-effort with JJ from their verified repositories and bookmarks; require the resolved head ID to equal metadata `headRefOid`, including fork PRs. On mismatch, omit `PR_HEAD_REF` and report the exact failure; use supplied hunks only. `BASE: pr:<number-or-url>` is a logical marker, not a revision; `PR_BASE_REF` must be the actual verified diff base and `PR_HEAD_REF` the exact head. Missing endpoints force unknown mechanical scope/full review and disclose missing file/history checks. Never assume another base. Prefer a JJ diff of the verified exact range when available and check that it represents the captured PR.
- **Branch/revision:** resolve a concrete local or verified remote bookmark/revision. If it is the aligned workspace, use local mode; otherwise use `branch-remote`, capture its head and unique actual default-base ancestor. Missing target/base stops review, never a fallback to unrelated workspace changes.

Emit `BASE:`, `HEAD:`, `FILES:`, `DIFF:`, `UNTRACKED:` and the scope mode. Use `jj diff --from "$BASE" --to "$HEAD" --name-only` and `jj diff --from "$BASE" --to "$HEAD" --git --context 10` from the absolute workspace root. The captured range is authoritative everywhere: scope mechanics, reviewers, validator, peer, receipt and output. A style-history sample never replaces it. For remote scope, reviewers and validators use `jj file show -r <captured-head> <path>` or supplied hunks, not Read/Grep on unrelated workspace files. Deleted bodies come from captured base only when needed. Summarize deleted bodies out of the shared prompt, preserving headers and listing deleted paths; retain the full exact patch privately for targeted inspection. Check surviving callers/registrations/string references before declaring a deletion safe.

Inspect `jj status` and `jj file list -r "$HEAD"` for untracked/ignored exclusions under project tracking policy; do not change tracking to expand scope. Report excluded paths and continue. Never claim ignored or untracked content is covered by the snapshot. Existing unrelated work remains untouched.

## Stage 1b: Compute scope signals

Run the retained mechanical helper directly from `workspace_root` after capturing endpoints. Do not estimate counts or derive multi-commit range statistics from parent-relative commit statistics:

```bash
(cd "$workspace_root" && python3 "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --docs-root "<root>")
```

`DIFF_A` is the exact captured diff base, `DIFF_B` the exact captured reviewed head (including snapshotted local changes). In remote scope pass empty flags when an endpoint is unavailable so the helper fails closed, never defaults to unrelated `@`. Set `CE_REVIEW_REMOTE_SCOPE=1` for remote scope so local pack configuration is not treated as the reviewed tree's configuration. The helper validates endpoints, counts added plus deleted lines in the exact range, separates production/test lines and whole-file deletions, detects executable modes, binary/uncounted files, renames and path classes. `hard_block_full` is a floor: named hard-block classes, uncounted files or at least 200 executable non-test changed lines require full. Below 200 never awards lite. Whole-file deletions band separately (`deleted_files`, `deleted_exec_nontest_lines`, `deleted_band`); binary deletions are uncounted too. `silent_pass_classes` forbid lite. Signals prompt persona consideration but do not automatically select it. Unknown mechanics force full and an explicit coverage limit.

`has_learnings_corpus`, `declared_packs` and `pack_roots` are repository facts, not diff heuristics. Local declared-pack parsing reads layered configuration only; it resolves no sources and `pack_roots` stays zero. `null` locally means inspect `packs:` yourself. Remote configuration is not the local checkout: report `null` there. Apply the Review depth gate in `modes-and-output.md` now, before later spine references.

## Stage 1c: Map criteria files to changed paths

Enumerate `CODING_STANDARDS.md`, `CLAUDE.md` and `AGENTS.md` at all depths in the **captured reviewed tree**, using `jj file list -r "$HEAD"`. Keep ancestors of changed paths. Every governing `CODING_STANDARDS.md` applies; instruction-file criteria apply only where no coding-standards file governs, never double-grade a path against both kinds. Declared packs select the separate learnings pass and are not a criteria kind. A violation of both standards and a pack yields one finding per source. An empty mapping is complete; failed/uncertain search is a recorded coverage gap, not an empty result.

## Local artifacts and stage log

Create a private run directory below `$workspace_root/.tmp/rocketclaw/ce-code-review/`, never OS temporary storage. Reject symlinked/unowned scratch directories, preserve private permissions, and stop if no safe writable local path exists; no global fallback. Ensure `.tmp/` is ignored. Use a unique run ID and retain artifacts through receipt/report completion.

Every run records stage costs in `<run-dir>/stages.jsonl` through `scripts/run-log.py`, including lite/focused paths:

```bash
python3 "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

At each boundary use `--end <stage> --start <stage>` together and record `--reviewers`, `--candidates`, `--tokens` only when supplied by the host, or `--fact key=value` as applicable. Stage names are `scope`, `review`, `receipt` for lite/focused; full uses `scope`, `select`, `dispatch`, `validate`, `merge`, `report`; `peer` may overlap native dispatch. Fold calls into existing work rather than narrating bookkeeping. The receipt's `summarize` folds stage costs into `metadata.json`.

Use native task visibility when available for review outcomes, not individual personas or setup. If unavailable, continue without inventing a task list. Evidence searches prefer symbol-aware references, then structural/AST search, then bounded text search. Preserve exact target scope and report uncertainty rather than prompting or guessing.

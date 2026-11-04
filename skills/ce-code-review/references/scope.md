# Stage 1: Resolve exact review scope

## Stage 1a: Target and endpoints

Resolve `workspace_root` by walking to the enclosing `.jj` directory, then verify `(cd "$workspace_root" && jj root)` equals that absolute path. Every JJ invocation below runs inside `(cd "$workspace_root" && ...)`; `-R` alone is insufficient and paths remain repo-relative. Repository-scoped `gh` receives `GIT_DIR` captured by `(cd "$workspace_root" && jj git root)`. Never invoke the Git executable, switch revisions, or treat a review target as mutation authority.

Capture a unique concrete commit ID using `jj log --no-graph -r '<resolved-ref>' -T 'commit_id ++ "\n"'`. Empty, ambiguous or failed resolution is not a usable endpoint. Capture the reviewed local `@` once after snapshotting; a remote review uses the verified remote head instead. Never substitute `main@origin` or another endpoint after capture.

- **`base:<ref>`:** resolve the supplied ref and local head. Resolve their unique common ancestor with `heads(::(<base-id>) & ::(<head-id>))`; fail on ambiguity rather than using the raw base as a fallback.
- **Standalone:** discover the actual configured/default remote bookmark, not a hardcoded main/master assumption. Resolve its unique common ancestor with the captured local head. If no base resolves, stop; reviewing only working-copy changes would miss committed work.
- **PR number/URL:** get title, body, URL, files, base/head repository, base/head names and exact OIDs using `gh pr view`. Preserve repository identity. `local-aligned` requires the corresponding local bookmark identity, matching repository, and PR head ancestry in the local reviewed head (use `jj log -r '<pr-head-id> & ::<local-head-id>'`). An empty `@` above the exact PR head can be aligned. Same bookmark name alone is insufficient. Aligned scope compares the verified PR common ancestor to the captured local head and includes local work; do not append remote hunks.
- **`pr-remote`:** otherwise use `gh pr diff --color=never`, saving and checking its status before processing. Failure stops, never checks out. Keep `BASE: pr:<number-or-url>` as logical marker, separately from diffable endpoints. Fetch the actual head/base remote bookmarks with `jj git fetch --remote <verified-remote> --branch <name>` only as needed; never assume origin carries a fork head. Set `PR_HEAD_REF` only when its captured ID equals metadata `headRefOid`, and `PR_BASE_REF` only for the verified exact base used by the PR diff. A moved, unavailable or mismatching endpoint stays unavailable; reviewers use supplied hunks and Coverage names missing tree access. Never use a different base to make the count succeed.
- **Named branch/bookmark:** if it identifies the current reviewed local tree use standalone local scope. Otherwise prefer its associated PR; failing that resolve the exact local or remote bookmark (fetch the verified remote/name when needed), discover the actual default base and unique common ancestor, and use `branch-remote`. Pass `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref>` to every reviewer and validator.

For captured exact `DIFF_A` and `DIFF_B`, use:

```bash
(cd "$workspace_root" && jj diff --from "$DIFF_A" --to "$DIFF_B" --name-only)
(cd "$workspace_root" && jj diff --from "$DIFF_A" --to "$DIFF_B" --git --context 10)
```

Save the **full** diff for mechanical counting before suppressing whole-file deletion bodies for reviewer delivery. Retain deleted mode/path headers; read a deleted body only when needed using `jj file show -r '<captured-base>' '<repo-relative-path>'`. Remote reviewers never Read/Grep current workspace versions of reviewed files: use `jj file show -r '<verified-reviewed-head>' '<path>'` and search its output, or supplied hunks only. Compare manifest, full patch and remote files inventory; missing or inconsistent coverage forces unknown/full, never a smaller range.

JJ snapshots eligible new files; these are part of captured `@`, not a separate Git staging area. Inspect `jj status`, `jj file list -r '<captured-head>'`, and the workspace inventory including ignored/non-snapshotted paths. List excluded paths in `UNTRACKED:`/Coverage without adding them or stopping. Preserve ignored/unrelated work.

## Stage 1b: Deterministic scope facts

Run the mechanical helper, not a prose estimate. Use the exact same captured endpoints as the review patch; it must not recompute a merge-base. Remote calls pass both flags even when missing, so the helper fails closed rather than substituting the local tree.

```bash
SKILL_DIR="<absolute directory containing this SKILL.md>"
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"
[ -n "$PY" ] || exit 1
(cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --scope-mode "$SCOPE_MODE" --docs-root "<root>")
```

`hard_block_full` is a floor, never an award of lite: migrations, uncounted/binary/special files, unknown scope and >=200 executable non-test added+deleted lines on non-deleted files force full. `exec_lines` includes test code; `exec_nontest_lines` excludes tests. Whole-file deletions are counted in `changed_lines` and separately in `deleted_exec_nontest_lines` / `deleted_band` (`none`, `small`, `large`), not the non-deleted executable floor. Test-only volume, prose, `unclassified_lines` and path `signals` invite consequence judgment, not automatic lite. `silent_pass_classes` (CI workflow paths) forbids lite but does not alone force full. Apply the depth gate before later stages.

Set `SCOPE_MODE` to `standalone`, `local-aligned`, `base` (for `base:`), `pr-remote` or `branch-remote`. Explicit local head capture does not make local config remote; the scope-mode flag preserves that distinction.

Use `test_files_changed`, `agent_surface`, `has_learnings_corpus` and `declared_packs` as reviewer-selection facts, not automatic decisions. `declared_packs` parses local config only, resolving nothing (`pack_roots` stays 0). For remote scope it is null; no local pack resolver runs. In local scope null requires reading config's `packs:` key yourself. Preserve exact-ref failure diagnostics and report unavailable scope honestly.

## Stage 1c: Criteria mapping and run artifacts

Enumerate `CODING_STANDARDS.md`, `AGENTS.md` and compatibility `CLAUDE.md` from the **reviewed tree**, using `jj file list -r '<head>'` for remote scope. Keep files whose directory is an ancestor of a changed path. Every governing `CODING_STANDARDS.md` applies together; instruction files supply criteria only to changed files with no governing designated standards. Never grade a path against both kinds. Packs are separate rule sources, not a criteria kind; grade them in context on lite/focused and through learnings on full. Missing criteria is complete, failed/uncertain criteria discovery forces full and is named in Coverage.

Create private run artifacts only below the absolute workspace-local `.tmp`; refuse symlinks or an unowned root:

```bash
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw"
[ ! -L "$workspace_root/.tmp" ] && [ ! -L "$SCRATCH_ROOT" ] || exit 1
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1
[ -O "$SCRATCH_ROOT" ] && [ -w "$SCRATCH_ROOT" ] || exit 1
chmod 700 "$SCRATCH_ROOT" || exit 1
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ')
RUN_DIR="$SCRATCH_ROOT/ce-code-review/$RUN_ID"
(umask 077; mkdir -p "$RUN_DIR") || exit 1
```

### Stage log

Use the bundled `scripts/run-log.py event --run-dir "$RUN_DIR" --start scope` with a working Python interpreter and absolute skill path. Subsequent boundaries use `--end <stage> --start <stage>` together, with `--reviewers`, `--candidates`, `--tokens` only when known, and `--fact key=value`. Stage names: `scope`, then `review`/`receipt` on lite/focused, or `select`, `dispatch`, `validate`, `merge`, `report` on full; `peer` may overlap review/dispatch. Close scope with facts `exec_nontest_lines`, `changed_lines`, `size_band`, `deleted_band`, `unclassified_lines`, `depth`. The final writer uses `run-log.py summarize --run-dir "$RUN_DIR"` to merge cost into metadata; incomplete stages remain partial.

## Stage 1d: Review policy

Read governing root/ancestor `REVIEW.md` from the captured **base**, never the changed tree. A policy governs review behavior, severity, exclusions, caps and evidence, not coding criteria. Root `@<path>` includes are read one level deep from the same base; skip includes already read as criteria. Stage each file with its path and governed paths in `<run-dir>/review-policy.md`. No policy is complete; an unread found policy is an honest gap. When the change edits/adds/deletes policy, the base copy applies and Coverage says its changed version was not applied.

For full review use native task tracking when available, showing review outcomes rather than individual tool calls; otherwise continue without a simulated task list.

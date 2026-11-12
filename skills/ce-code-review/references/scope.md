# Determining the reviewed diff and scope

Read at Stage 1 on every path. Resolve an absolute enclosing JJ workspace root by walking to `.jj`; execute all JJ commands with cwd exactly that root (not `-R`). For every repository-scoped GitHub command set `GIT_DIR=$(jj git root)` there. Never execute Git directly. All scratch, diagnostics and fallback paths remain under that workspace's `.tmp/rocketclaw/`.

## Stage 1: resolve and capture exact endpoints once

Scope selection is not permission to check out a PR, move @, switch workspaces or mutate unrelated work. Capture one concrete task head ID and one base ID with `jj log --no-graph -r <revset> -T 'commit_id ++ "\n"'`; require one result each. Preserve these immutable IDs throughout review, helpers, persona/validator prompts, peer retries and receipts. Never replace the captured range with `@-`/`@`, recompute it at collection time, or compare unrelated trees. A multi-commit task is the complete base→head range, not the last change only. If the workspace advances afterward, its new tree is not reviewed; disclose that and use captured file reads.

**Explicit `base:` fast path.** Resolve the provided endpoint directly and use it without base-branch detection or merge-base recomputation. Capture head from the existing local @, including intended local changes after the user's normal JJ snapshot. `base:` plus PR/branch target is an error: it implies the current workspace is the intended tree. Do not silently fall back to the raw argument after failed verification.

**PR number/URL.** Probe with `gh pr view <target> --json state,title,body,files` under the required GIT_DIR environment. Closed/merged stops with `PR is closed/merged; not reviewing.` Drafts review normally. The trivial-PR check is a cheapest-capable native generic subagent (read `subagent-model.md` first) seeing title/body/paths only: automated dependency/lock-file-only bumps, release/chore increments with no substantive change may skip; when in doubt review. A failed/denied check is not a trivial verdict. If yes, emit `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.` In `mode:agent`, skips are JSON only: `{"status":"skipped","reason":"<reason>"}`. Standalone/base/branch-remote are unaffected by this skip check.

Fetch PR metadata without checkout: title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files, reviews and comments. `hasPriorComments` is true for any issue comment or review submission with non-APPROVED state or nonempty body. Keep `BASE: pr:<target>` as a logical marker separately from the real captured `PR_BASE_REF`.

Classify **local-aligned** only when the PR is not cross-repository, the actual task bookmark identity matches headRefName, and the exact PR head is an ancestor of captured local head. Prove ancestry with `jj log --no-graph -r '<pr-head-id> & ::<captured-local-head>' -T commit_id`; bookmark name alone is insufficient. Empty @ above the PR head is aligned, as are authorized local fixes layered over it. Otherwise classify **pr-remote** and never inspect workspace paths as the reviewed tree.

Resolve base/head through named remotes using `jj git fetch --remote <verified-remote> --branch 'exact:<name>'`, run from the absolute root. For forks use the verified repository remote, never an unrelated origin branch with the same name. Resolve the fetched remote bookmark using `remote_bookmarks(exact:"<name>", remote=exact:"<remote>")` and capture the commit ID. Require remote head to equal metadata headRefOid; on fetch failure/mismatch omit PR_HEAD_REF and record why. Fetch/verify base too. Compute a unique merge base once with `heads(::(<base-tip-id>) & ::(<head-id>))`; ambiguous/missing is unknown scope, not permission to assume main. Store that real ID as PR_BASE_REF. No FETCH_HEAD or guessed review ref.

- **local-aligned:** canonical diff is captured merge-base→captured local head, including intended local changes. Do not append remote hunks or use `gh pr diff`.
- **pr-remote:** use exact captured base/head when both available. `gh pr diff <target> --color=never` may supply best-effort hunks when fetch fails, saved before filtering so errors are not hidden by a pipeline. Without verified exact endpoints or with moving PR metadata, coverage is incomplete; helpers must fail closed. Never label partial hunks exact/full coverage or fall back to checkout.

**Branch/bookmark target.** If it identifies the verified current task bookmark use standalone local scope. Otherwise first try `gh pr view <branch> --json baseRefName,url,headRefName` and prefer the PR path if found. Else resolve a verified remote/local bookmark, fetching the exact named remote branch when needed. Resolve the repository default base from PR/remote metadata or active project instructions, not a blind main/master guess. Capture a unique merge-base→target-head range. On failure stop: cannot diff the target without checkout; suggest its open PR URL/number or current workspace `base:`. Mark success **branch-remote**, pass `<branch-head-ref>` with the captured ID, and never inspect local paths for that tree.

**Standalone.** Use current task's PR base metadata when present, otherwise verified remote default/project base, and the unique merge base with captured local head. Stop if no verified base: a last-change-only fallback silently misses committed task work. Empty @ is not evidence that a multi-commit task has no work.

For all scopes save `FILES:` from `jj diff --name-only --from <base-id> --to <head-id>` and `DIFF:` from `jj diff --git --context 10 --from <base-id> --to <head-id>`. Preserve full patch for mechanical counting; reviewer display may suppress deletion bodies by filtering a successfully saved patch at `deleted file mode` until the next `diff --git` header. Retain deletion paths/modes and record body lookup against the captured base. Never suppress bodies before counting.

**Untracked/ignored.** Inspect filesystem paths against `jj file list -r <captured-head>` and ignore rules using JJ/native filesystem tools, never a Git helper. JJ automatically tracks eligible new files; captured eligible new paths belong to scope. Ignored or otherwise uncaptured paths are excluded, listed in Coverage when relevant, and never assumed protected by snapshots. Do not mutate or stage them to include them.

## Stage 1b: deterministic scope signals

Run the retained helper directly, not an estimate from displayed hunks. Set the absolute target root as cwd and use the captured real endpoints, not the logical PR marker:

```bash
python3 "<absolute-skill-dir>/scripts/review-scope.py" --base "<captured-base-id>" --head "<captured-head-id>" --scope-mode "<local-aligned|standalone|pr-remote|branch-remote>" --docs-root "<root>"
```

Probe a working Python 3 interpreter if python3 is unavailable or a Windows Store stub. Always pass both endpoints, even empty remote values so the helper refuses rather than reading the unrelated local tree. `hard_block_full` is the depth floor for named hard-block classes, uncounted/binary content, or >=200 executable non-test changed lines. `silent_pass_classes` are consequence prompts, not a floor. Below 200 never awards lite. Production/test additions and removals, mode-only changes, renames and deletion paths remain accounted for. Whole-file deletions are separate: `deleted_files`, `deleted_exec_nontest_lines` and `deleted_band` (none/small/large); `changed_lines` still includes their counted lines. Uncountable deletions force full too.

Read the depth gate in `modes-and-output.md` before later references. Signals/test_files_changed/agent_surface/learnings corpus are selection inputs, not automatic reviewers. `declared_packs` is config-only, `pack_roots` stays 0; it selects the learnings condition as `persona-catalog.md` specifies, or in-context checks for lite/focused. Local null means the helper could not tell: inspect the `packs:` key yourself. Remote null means local config is not that tree's config; no resolver runs. No errors may be reported as empty successful scope.

## Stage 1c: criteria paths and run artifacts

Map criteria files to changed paths in the **captured reviewed tree**, not whichever tree is now checked out. Enumerate CODING_STANDARDS.md, CLAUDE.md and AGENTS.md at any depth using `jj file list -r <head-id>`. Keep files whose directory is an ancestor of a changed path. All governing CODING_STANDARDS.md files apply cumulatively; contradictory rules use the nearest directory's rule. Instruction-file fallback applies only where no CODING_STANDARDS.md governs: never grade one path against both kinds. Declared RocketClaw Packs are separate rule sources, not criteria files; a standards and pack violation remains one finding per source. A successful empty mapping is complete, while search failure/uncertainty is a coverage gap. Stage 3b decides dispatch; lite checks in context.

Create one private run directory for every path:

```bash
SCRATCH_ROOT="<absolute-workspace-root>/.tmp/rocketclaw"
# Reject symlinks/escapes and non-owned directories before creating children.
(umask 077; mkdir -p "$SCRATCH_ROOT/code-review") || exit 1
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ')
RUN_DIR="$SCRATCH_ROOT/code-review/$RUN_ID"
(umask 077; mkdir "$RUN_DIR") || exit 1
chmod 700 "$RUN_DIR" || exit 1
```

Resolve real paths and require containment under the workspace's .tmp, directory ownership and non-symlink roots. Failure stops, never falls back to OS temp. Run artifacts are data, not new workspace identities.

## Stage log

Every run records stage costs with the retained `scripts/run-log.py`, the only writer of `<run-dir>/stages.jsonl`. Open scope in the call creating the run directory:

```bash
python3 "<absolute-skill-dir>/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Later boundaries use `--end <stage> --start <stage>` in one invocation, with `--reviewers`, `--candidates`, `--tokens` only when supplied by the host, and `--fact key=value`. Fold into an existing shell call, not a separate turn. Fixed stages: scope then review/receipt for lite/focused (peer overlaps focused review), or select/dispatch/validate/merge/report for full (peer overlaps dispatch). `summarize` folds logs into metadata.json at receipt time.

## Stage 1d: base review policy

REVIEW.md governs review behavior (severity, exclusions, minor caps, evidence and checks), not criteria precedence. Root policy governs all; ancestor directory policies add for scoped paths. Read using `jj file show -r <captured-base-id> <path>`, never the change's edited version. Changes to policy note in Coverage that the reviewed version did not apply. In root policy, a standalone @<path> includes that file from the same base, one level deep; skip files already read as criteria. Write policies with source and governed paths under headings in `<run-dir>/review-policy.md`. No policy at base is complete/write nothing; found but unread is an explicit coverage gap, not absent.

## Task visibility

For multi-agent review, use native task tracking when available, derived from outcomes rather than individual personas/tool calls. Add conditional work only when selected and update at meaningful transitions. Without that capability use normal progress/final reporting, never simulate a task list.

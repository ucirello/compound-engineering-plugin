# Determining the reviewed diff and scope

Read at Stage 1. Resolve the exact tree without checkout or changing bookmarks. JJ source: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/. All JJ commands run with working directory set to the target workspace's **absolute root**; `-R` alone is not sufficient. Obtain that root with `jj workspace root`, then perform inspection from it. Every repository-scoped GitHub CLI call uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, including error/recovery calls. No Git workspace/branch commands.

## Stage 1: determine scope

### Explicit `base:`

Do not combine `base:` with a PR or bookmark target: stop with `Cannot use base: with a PR number or branch target — base: reviews the current workspace. Pass one target only.` Skip default-base discovery. Resolve the given revision (`origin/main` becomes the verified `main@origin` remote bookmark). Resolve a unique common ancestor with `jj log -r 'heads(::(<base>) & ::@)' --no-graph -T 'commit_id ++ "\n"'`; if unavailable/ambiguous, use only a verified explicit base endpoint, never a guessed one. Set `BASE`/`DIFF_A` to that commit, `DIFF_B` absent, scope `standalone`. Produce files with `jj diff --from "$BASE" --to @ --name-only` and exact patch with `jj diff --from "$BASE" --to @ --git --context 10`. These include committed and working-copy changes, not merely the last change.

### PR number or URL

Probe `gh pr view <target> --json state,title,body,files` with the repository preamble above. Closed/merged stops: `PR is closed/merged; not reviewing.` For trivial-PR judgment this skill explicitly requests one lightweight native subagent, seeded only with title/body/paths: automated manifest/lockfile-only bumps, release/version increments with no substantive behavior may be skipped; when in doubt answer no. Resolve cheapest capable tier with `opencode.models` only when a model override is permitted. If user model request is required and absent, omit model and inherit. If delegation is forbidden/unavailable/depth-limited, perform this non-independent precheck inline and disclose it if material; uncertainty must not skip the review. A yes stops: `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument or pass base:<ref> to review the current workspace.` Default emits the reason, mode:agent emits only `{"status":"skipped","reason":"<same reason>"}`. Drafts are reviewed normally.

Read `gh pr view <target> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments,headRepository,headRepositoryOwner`. Keep all intent metadata and compute `hasPriorComments` from nonempty/non-approved reviews or issue comments. `BASE:pr:<target>` is a logical marker, not a diffable revision.

Classify `local-aligned` only when the PR repository is verified the same, the verified local head bookmark matches `headRefName`, and `headRefOid` is an ancestor of `@` (`jj log -r '<headRefOid> & ::@'` yields that exact commit). Allow local changes on top, including an empty `@` above the head; bookmark absence on the empty tip is not proof of mismatch. Resolve bookmarks on `@-` as needed. Otherwise scope is `pr-remote`. Name collisions/fork branches are not alignment proof.

- Local-aligned: fetch/resolve the verified base remote bookmark with `jj git fetch --remote <verified-remote> --bookmark <baseRefName>` if needed. Resolve unique common ancestor of base and `@`, then use local `jj diff --from <ancestor> --to @ --name-only/--git --context 10`. Do not append `gh pr diff` hunks. Coverage: `scope: local-aligned (PR; local tree diff)`.
- PR-remote: files are the PR files array; patch is `gh pr diff <target> --color=never` with valid GIT_DIR. Failure stops with actionable error, never checkout fallback. Best-effort fetch the verified head repository/remote/bookmark via `jj git fetch`; expose `PR_HEAD_REF` only if its resolved `commit_id` equals metadata `headRefOid`. Recheck moving-head/fork identity rather than trusting successful fetch. Fetch verified base similarly and expose concrete `PR_BASE_REF`; never use the logical `pr:` marker or assume main. Missing/mismatched endpoints are Coverage gaps; reviewers use hunks only where unavailable.

Provide remote scope tags and verified head/base endpoints to reviewers and validators. In remote scope never inspect changed files from the unrelated workspace: use `jj file show -r <verified-head> <path>` and revision-aware search, or hunks only.

### Bookmark/revision target or no target

For a named target, resolve it to an exact verified local/remote bookmark or revision without switching. If its tree matches the current reviewed tree, use standalone. Otherwise try `gh pr view <target> --json baseRefName,url,headRefName` with the repository preamble and prefer the PR path. If no PR, best-effort fetch the verified remote bookmark via JJ; resolve the default base from verified repository metadata/project instructions. A unique `heads(::(<base>) & ::(<target>))` is required. Diff from ancestor to exact target, scope `branch-remote`; pass remote head tag and prohibit local changed-file inspection. Unresolvable target stops with `Cannot diff target without checkout. Pass its open PR URL/number or review the current workspace with base:.`

No target uses bookmarks on `@` and, when `@` is an empty tip, `@-` to resolve its associated PR/default base. Do not assume `gh pr view` can infer an active Git branch from JJ. If base cannot be resolved, stop: reviewing only `@` would silently miss earlier committed work. On success diff base ancestor to `@`, scope standalone. Review scope never authorizes `jj edit/new`, workspace creation, bookmark mutation, checkout, commits, push or PR changes.

Inspect `jj status` and the configured snapshot exclusions. JJ automatically tracks eligible new files; these are in the reviewed diff. Files deliberately left untracked/excluded are not silently included: name excluded paths in Coverage and continue; ignored content is not disposable. Record `BASE:`, `FILES:`, `DIFF:`, `UNTRACKED:` with repository-relative paths (e.g. `src/example.py`, never workspace-prefixed paths). Metadata `head_sha` is exact `commit_id`; `branch` is verified relevant bookmark identity, not a fictitious Git current branch.

## Stage 1b: deterministic scope signals

Run retained `scripts/review-scope.py` directly from the absolute workspace root, using an execution-probed Python interpreter and this skill's absolute directory. `--base` is the real local ancestor or remote base; remote scope always includes `--head` even when empty so failure cannot compare against the unrelated local tree. Pass resolved `--docs-root`. The helper validates endpoints, exact diff counts and path classes; it never awards lite. Its read-only Git patch parser is only for numstat, which JJ does not provide, and uses `jj git root` for backend context.

```bash
(cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>")
# Remote scope instead:
(cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>")
```

Load JSON. `hard_block_full` floors review depth for hard-block classes, uncounted files or large executable non-test changes; `silent_pass_classes` forbids lite. Small count alone never awards lite. Signals are heuristics, not automatic reviewer selection. Use test changes, agent surface, plausible learnings corpus and declared packs in the selection contract. `declared_packs` is local-config-only (nothing resolved; pack_roots 0), null remotely or when uncertain. In local uncertainty read `packs:` yourself. Apply `modes-and-output.md` depth gate before later references.

## Stage 1c: criteria mapping and run directory

Enumerate `CODING_STANDARDS.md`, `CLAUDE.md`, `AGENTS.md` in the reviewed tree, not the unrelated current tree for remote scope. Keep ancestors of changed paths. Every governing CODING_STANDARDS applies; instruction files are fallback only where no such standard governs, never grade one file against both kinds. Declared packs are independently graded by learnings, not criteria here. Missing/deleted criteria must match the reviewed revision. Empty successful search is complete; error/uncertainty is a gap, never empty. Paths, not contents, form the mapping consumed by lite/full paths.

Create private local run state for every depth:

```bash
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw"
[ ! -L "$workspace_root/.tmp" ] && [ ! -L "$SCRATCH_ROOT" ] || exit 1
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1
[ -O "$SCRATCH_ROOT" ] && [ -w "$SCRATCH_ROOT" ] || exit 1
chmod 700 "$SCRATCH_ROOT" || exit 1
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ')
RUN_DIR="$SCRATCH_ROOT/ce-code-review/$RUN_ID"
(umask 077; mkdir -p "$RUN_DIR") || exit 1
chmod 700 "$RUN_DIR" || exit 1
```

No OS temp fallback, including errors. Confirm `.tmp/` ignored; preserve existing ignore entries. Read/verify ownership and symlinks before consuming artifact paths. Write exact files/diff once to run paths for large shared context.

## Stage log and visibility

Retain `scripts/run-log.py` profiler: use `event --run-dir "$RUN_DIR" --start scope` at first boundary, `--end <stage> --start <stage>` thereafter, count reviewers/candidates, record tokens only when observed. Resolve interpreter in the same shell call (`python3`, `python`, `py`, execution probe); never assume a previous shell variable persists. Skill dir is absolute. Fold events into existing shell calls rather than narration. Lite/focused stages are scope, review, receipt (peer overlaps review); full stages are select, dispatch, validate, merge, report (peer may overlap dispatch through native collection). Final `summarize` folds stages into metadata.

Use native task tracking when available for review outcomes and conditional coverage, not persona machinery. No simulated task list if absent. This skill explicitly requests reviewer dispatch: apply actual user-or-skill delegation exception where allowed, separately gate model arguments and effective nesting depth as `dispatch-reviewers.md` and `cross-model-review.md` require. Never conflate depth with denied permission or required cross-model independence with same-model seating.

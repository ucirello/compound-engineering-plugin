# Determining the reviewed diff and scope

Read at Stage 1. Resolve scope without changing the workspace's revision. Use latest native JJ (https://docs.jj-vcs.dev/latest/cli-reference/), never the Git executable. Resolve the absolute root with `jj workspace root`, and run every subsequent repository command with cwd that absolute root, e.g. `(cd "$workspace_root" && jj ...)`. Before repository-scoped GitHub calls export `GIT_DIR` using `(cd "$workspace_root" && jj git root)` and run `gh` at that same root. Combine inspection where useful, but check each command's status, not a pipeline's last status.

## Stage 1: Determine scope

Capture concrete full commit IDs once with `jj log --no-graph -r '<verified-revision>' -T 'commit_id ++ "\n"'`; require exactly one result. Capture the working-copy head after snapshotting with `jj status` when local scope applies. Never recalculate endpoints later or replace the captured range with parent-relative statistics or a style sample.

### Explicit `base:` fast path

The caller already knows the base: resolve that exact revision directly, skip default-base discovery and merge-base computation. Capture local `@` as head. Reject `base:` combined with a PR/branch target: `Cannot use base: with a PR number or branch target — base: implies the current workspace is already the correct branch. Pass base: alone, or pass the target alone and let scope detection resolve the base.` A supplied SHA or bookmark must resolve uniquely; never substitute another ref.

### PR number or URL

Do not check out the PR. Probe `gh pr view <number-or-url> --json state,title,body,files` with the GIT_DIR context above. Closed/merged stops with `PR is closed/merged; not reviewing.` Drafts are reviewed normally.

For the trivial-PR judgment this skill explicitly requests one lightweight generic native subagent. The desired tier is cheapest capable unless user/project/config role intent selects otherwise; use `opencode.models` to resolve available IDs only when model choice is authorized. If host policy needs explicit user model request, omit optional `model` and inherit. A user-or-loaded-skill delegation rule permits this requested reviewer without another approval; higher unconditional prohibition or denial still applies. Classify nesting/capacity separately. When unavailable do the cheap judgment inline (it is not required independence), recording the limitation rather than skipping substantive review. Give title/body/changed paths and ask: `Is this an automated or trivial PR that does not warrant a code review? Consider dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt answer no: false negatives (skipped reviews that should have run) are more costly.` A yes stops with `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

Skip emits plain text by default, or JSON only in `mode:agent`: `{"status":"skipped","reason":"<same message>"}`. Standalone, explicit-base and branch-remote paths are unaffected.

Otherwise obtain `title,body,baseRefName,baseRefOid,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,url,files,reviews,comments` from `gh pr view`. Preserve title/body and `hasPriorComments` (nonempty/non-approved reviews or comments), and the file path inventory. `BASE:pr:<number-or-url>` remains a logical scope marker only; keep separate real `PR_BASE_REF`/`PR_HEAD_REF` IDs.

Classify **local-aligned** only if all hold: the verified associated local bookmark is `headRefName`; the PR is not cross-repository; and the exact metadata head is an ancestor of local captured head, proven by a nonempty `jj log --no-graph -r '<headRefOid> & ::<captured-local-head>' -T 'commit_id'`. Empty `@` above the PR commit is allowed. A same-named bookmark alone proves nothing. Otherwise use **pr-remote** and prohibit workspace Read/Grep for changed paths.

For local-aligned, resolve the actual base bookmark (fetch through `jj git fetch --remote <verified-base-remote> --branch <baseRefName>` only if needed), then compute the **unique** greatest common ancestor with `jj log --no-graph -r 'heads(::<resolved-base> & ::<captured-local-head>)' -T 'commit_id ++ "\n"'`. Capture that result as real base; diff to local captured head, including local fixes. Never append remote hunks to it.

For pr-remote save `gh pr diff <number-or-url> --color=never` first and check success; failure stops with an actionable error, never a checkout fallback. Set FILES from metadata. Retrieve exact head/base using native `jj git fetch` against verified remotes belonging to the actual head/base repositories, not a fork's same-named branch on origin. Resolve candidate IDs and compare to metadata `headRefOid` and `baseRefOid` before assigning `PR_HEAD_REF`/`PR_BASE_REF`. Fetch success is not identity proof. Do not add/change remotes or workspace/bookmarks without authority; unavailable exact refs are omitted with a Coverage reason, never silently replaced. Reviewers then use only supplied hunks for unavailable bodies/checks, and missing mandatory coverage remains incomplete.

Provide `<pr-scope-mode>pr-remote</pr-scope-mode>` plus verified `<pr-head-ref>` and `<pr-base-ref>` when available. In local-aligned, local inspection is valid; remote reviewers/validators use `jj file show -r <captured-head> <path>`, `jj file annotate -r <captured-head> <path>` and targeted `jj log`, never a mismatched workspace tree. Schema checks use `jj diff --from <captured-base> --to <captured-head> -- <path>`; unavailable refs do not imply main.

### Branch/bookmark argument

Do not switch revisions. If the supplied bookmark is verified as associated with local head, use standalone below. Otherwise try `gh pr view <branch> --json baseRefName,url,headRefName` first and prefer PR scope when found. Else resolve the exact `<branch>@<verified-remote>` or local bookmark, fetching with `jj git fetch --remote <verified-remote> --branch <branch>` if needed. Resolve the repository's actual default base from verified GitHub metadata/project instructions, not a guessed main. Compute the unique common ancestor as above and capture concrete base/head IDs. If unavailable, stop: `Cannot diff branch <branch> without checkout. Pass its open PR URL/number, or review the current workspace with base:.`

Set **branch-remote**, include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref>`; use captured-head file/history inspection only.

### Standalone

Resolve associated bookmark/PR using verified JJ bookmark state (including `@-` for an empty tip); GitHub lookup must use the explicit verified bookmark when there is no Git HEAD branch. Prefer its actual PR base; otherwise resolve verified repository default base. Stop if no base can be resolved: a working-copy-only fallback would silently miss committed work. Compute the unique common ancestor with captured local head, then save that exact range.

### Common output

Publish `BASE:` (real ID except PR logical marker), captured real endpoints, `FILES:` from `jj diff --from <base> --to <head> --name-only`, and `DIFF:` from `jj diff --from <base> --to <head> --git --context 10`. Save full diff before locally suppressing whole-file-deletion bodies for reviewer input. For remote hunks or local output the deletion-body filter is `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`; never pipe a failing producer directly into it. Retain deletion headers/path; retrieve old bodies selectively from captured base only when evidence needs them.

`UNTRACKED:` comes from `jj status` plus local filesystem inspection against `jj file list` for files left untracked (including configured auto-track exclusions); inspect ignored files without automatically adding them. JJ auto-tracked new files are part of captured `@`; files still untracked are excluded and named in Coverage. Never silently omit them, prompt, or stage them. Inspection is not permission to mutate, create a workspace or clean content.

## Stage 1b: Compute scope signals

Run the retained mechanical helper directly, from the absolute root; do not estimate counts or inspect its source unless it fails. Supply captured concrete endpoints even for local scope:

```bash
(cd "$workspace_root" && python3 "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --local-scope --docs-root "<root>")
```

Omit `--local-scope` for pr-remote/branch-remote. Always pass both remote flags even if empty, so absent refs fail closed rather than diffing an unrelated workspace. Local `--local-scope` preserves config/pack signals while retaining the captured head. `hard_block_full` is a floor: named classes, uncounted/binary entries and production executable additions+deletions at **200** force full. Below 200 never awards lite. `silent_pass_classes` forbids lite but does not force full; consequence decides. Whole-file deletions band separately in `deleted_files`, `deleted_exec_nontest_lines` and `deleted_band`; `changed_lines` includes counted deletions, whereas `exec_lines`/`exec_nontest_lines` exclude those whole-file deletions. Retain rename, mode-only and executable-bit facts. Unknown/conflicted/unreadable/binary data is uncounted and cannot become zero-size proof.

Path heuristics `signals`, `test_files_changed`, `agent_surface` and `has_learnings_corpus` prompt consideration, never automatic roster choices. `declared_packs` reports declarations in local RocketClaw config only, without resolving (`pack_roots` stays 0); remote scope returns null and never applies local packs. Local null means read config's `packs:` key yourself. Apply the Review depth gate before later references; Stage 3 still judges content-based auth/payment/mutation/I/O/concurrency/process risks.

## Stage 1c: Map criteria files to changed paths

Enumerate `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth in the **reviewed tree**, not an unrelated checkout. Keep files whose directory is an ancestor of a changed path. The root governs all; nested files govern their descendants. Capture paths and governing changed paths, not full contents.

Every governing `CODING_STANDARDS.md` applies together. Instruction-file fallback supplies criteria only for changed files with no governing `CODING_STANDARDS.md`; never grade a file against both criteria kinds. No governing criteria is a complete result; failed/uncertain search is not absence. Declared Compound Packs are separate, graded by learnings on full and in-context on lite/focused, with distinct findings per source. Finish when no file could be graded against two kinds. Stage 3b decides project-standards dispatch from this mapping.

Create the private local run directory for every depth:

```bash
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root not owned: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ');
RUN_DIR="$SCRATCH_ROOT/code-review/$RUN_ID";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
```

Verify `.tmp` is ignored, all resolved parent paths stay inside the workspace, and no symlink escape exists; report unsafe/unwritable storage rather than falling back to global temp.

### Stage log

Record `<run-dir>/stages.jsonl` only with the retained `scripts/run-log.py`; fold into `metadata.json` using `summarize` at the end. Open scope in the existing shell call where possible:

```bash
SKILL_DIR="<absolute directory containing this SKILL.md>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
[ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Later boundaries combine `--end <stage> --start <stage>` with `--reviewers`, `--candidates`, `--tokens` only if runtime supplied, and `--fact key=value`. Stage names: scope, then review/receipt on lite/focused (peer overlaps review on focused), or select/dispatch/validate/merge/report on full (peer overlaps dispatch). Fold calls into existing shell calls, never a dedicated turn.

## Stage 1d: Stage review policy

Read repository `REVIEW.md` instructions from captured **base**, never reviewed-tree edits: root policy governs the whole change, ancestor-directory policies add for their paths. A changed/added/deleted policy uses the base copy (none for a new file); Coverage says reviewed version was not applied. Root lines containing only `@<path>` include that file at the same base, one level deep; skip criteria files already read such as `@CODING_STANDARDS.md`. This policy governs review behavior, not grading criteria, and does not displace them. Claude Code Review reads the same format.

Write relevant policies to `<run-dir>/review-policy.md`, with headings naming source and governed paths. No base policy is a complete result (write nothing); an unreadable policy is recorded unread, not absent.

## Task visibility

On the multi-agent path use native task tracking when available, derived from review outcomes, not persona/setup/tool mechanics. Add conditional work only when applicable and update at meaningful transitions. Without that capability use normal progress/final reporting, not a simulated task list.

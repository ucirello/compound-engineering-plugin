# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the exact diff range, file list, and diff. Run every JJ and repository-scoped `gh` command with cwd set to the target **absolute workspace root**, discovered with `jj root`; never use `-R` as a cwd substitute. Before repository-scoped `gh`, export `GIT_DIR=$(jj git root)` in that root. Do not invoke Git directly, even for read-only inspection or fallback. Review never switches or creates workspaces.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-branch detection, remote resolution, and merge-base computation. Use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log --no-graph -r "$BASE_ARG" -T 'commit_id ++ "\n"')
```

Then produce the same output as the other paths:

```
jj diff --summary --from "$BASE" --to @
jj diff --git --context 10 --from "$BASE" --to @
jj status
```

Require exactly one full commit ID; an absent or ambiguous endpoint is a blocker. Use the supplied base exactly, not a newly computed common ancestor. JJ refs include commit IDs, bookmarks and remote bookmarks such as `main@origin`. **Do not combine `base:` with a PR number or branch target.** If both are present, stop with the same incompatible-scope error: `base:` selects the current workspace, while a target selects its own reviewed head.

**If a PR number or GitHub URL is provided as an argument:**

Do **not** check out the PR branch. Scope comes from GitHub read APIs plus optional local alignment when HEAD already matches the PR head branch.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: read `subagent-model.md`, then use a native lightweight capable subagent if delegation is permitted. Use configured choices subject to host model permission, else suitable inheritance. Give it title, body and paths and ask whether this is only an automated dependency/release/version chore without substantive code. When unsure answer no: wrongly skipped reviews are more costly than unnecessary reviews. If the check cannot delegate, assess conservatively in the parent and disclose the missing independent pre-check; never bypass denial/depth. Only a clear yes skips: `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

If the user's or project's active instructions or the live prompt name a model for this subagent, use that model instead of the default tier above. They can name it by the subagent's tier, by its prompt-asset name, or for the subagents being dispatched. Without such an instruction, a model configured for this subagent's role takes precedence over the default tier.

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a commit ID). Set current-workspace exclusion notes from `jj status` and `jj file list -r @`; they are not remote reviewed content.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. `jj bookmark list` identifies the PR's source bookmark at the verified workspace history head. Do not infer a current branch from JJ's empty working-copy change; inspect `@-` when `@` is empty.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. Resolve `headRefOid` to one full commit ID and verify it is in the ancestors of `@` with `jj log --no-graph -r '<headRefOid> & ::@' -T 'commit_id ++ "\n"'`. The result must equal the metadata OID. An empty `@` immediately above that verified head is aligned; local descendants may include unpushed fixes. Conflicts or uncertainty prevent local alignment.

- **`local-aligned`** — all three checks pass. Local Read/Grep and targeted JJ annotation against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve the PR base remote bookmark, fetching only when needed with `jj git fetch --remote <verified-remote> --branch <baseRefName>`. Resolve `heads(::<resolved-base-ref> & ::@)` to exactly one full ID and set `BASE` to it; ambiguity is a blocker, never a fallback to the base tip. Set `FILES` from `jj diff --summary --from "$BASE" --to @` and `DIFF` from `jj diff --git --context 10 --from "$BASE" --to @`. Includes committed and snapshotted working-copy changes. Do not append remote hunks; the local tree is canonical. Note local alignment in Coverage.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout. Then drop deleted-file bodies from that saved output the way `--irreversible-delete` does on the local paths, with `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`; never pipe `gh pr diff` straight into the filter, because the pipe hides its failure.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the head with `jj git fetch --remote <verified-head-repository-remote> --branch <headRefName>`. Verify that remote's URL against the PR head repository; never assume origin for a fork or silently add/remap remotes.
2. Resolve the fetched remote bookmark with `jj log --no-graph -r '<headRefName>@<verified-remote>' -T 'commit_id ++ "\n"'`. Set `PR_HEAD_REF` only when its single full OID equals metadata `headRefOid`; otherwise omit it and disclose diff-only inspection. A successful fetch alone is not proof, including races while the PR moves.
3. Best-effort fetch the verified base repository bookmark with JJ. Resolve exactly one common ancestor `heads(::<verified-base-tip> & ::<verified-head>)`; set `PR_BASE_REF` to its full ID only when the exact PR diff endpoints are verified. Keep `pr:<number-or-url>` as a logical scope marker, never a diffable endpoint. Missing/ambiguous base or head means unknown scope counts and hunk-only evidence, never an assumed default branch.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when verified, otherwise use only supplied diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If bookmark and ancestry verification proves the named bookmark is the workspace's history head (including empty `@` above it), use the standalone path. A matching name alone is insufficient.

Otherwise diff the remote/local ref **without checkout**:

1. Try `gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve `<branch>` as `<branch>@<verified-remote>` or a verified local bookmark after `jj git fetch --remote <verified-remote> --branch <branch>` when needed.
3. Resolve the actual default base bookmark from repository metadata, not a hardcoded name. Resolve `heads(::<base-ref> & ::<branch-ref>)` to one full ID and use it as `BASE`; diff with `jj diff --git --context 10 --from "$BASE" --to <branch-ref>`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without checkout. Check out that branch, pass its open PR URL/number, or review the current branch with `base:`."

On remote branch success, set **branch-remote scope** and pass the mode plus verified full head ID in `<branch-head-ref>`. The workspace is not that tree. Reviewers/validators use `jj file show -r <verified-branch-head> <path>` or supplied hunks, never workspace Read/Grep.

Produce:

```
jj diff --summary --from "$BASE" --to <branch-ref>
jj diff --git --context 10 --from "$BASE" --to <branch-ref>
jj status
```

**If no argument (standalone on current branch):**

Apply the same base-detection logic as branch mode above, using the current branch (i.e., `gh pr view --json baseRefName,url` with no argument defaults to the current branch).

If no base can be resolved, **stop**. Do not fall back to `jj diff` against only `@-`: that silently misses committed work. Without an associated PR, resolve the repository's actual default bookmark from metadata and verify one common ancestor with `@`.

On success, produce the diff:

```
jj diff --summary --from "$BASE" --to @
jj diff --git --context 10 --from "$BASE" --to @
jj status
```

The exact `--from "$BASE" --to @` range includes committed and working-copy changes; JJ has no staging-area distinction. Pin full endpoint IDs for helpers, reviewers, history, validation and receipts so a moving workspace cannot change the reviewed range unnoticed.

**Whole-file deletions carry no body in reviewer input.** Preserve the raw exact-range JJ patch privately for counting. Stage a separate reviewer copy that retains each deleted section's header/path/mode but strips its old body (the saved-output filter above applies to JJ's patch format too). JJ has no `--irreversible-delete` option. Read a deleted body from the exact base only when evidence needs it.

**Untracked file handling:** Inspect `jj status` and `jj file list -r @`. JJ auto-tracks eligible new files; those snapshotted into `@` are in scope, not excluded for lacking a Git staging action. Report any untracked/ignored exclusions explicitly in Coverage. Do not mutate tracking to expand review scope.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A` is the exact full base ID and `DIFF_B` the full snapshotted `@` ID captured with the saved diff; set `SCOPE_MODE=base` for `base:`. Pin both, even locally.
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --scope-mode "$SCOPE_MODE" --docs-root "<root>";
fi
```

Remote scope always passes both endpoints, even empty after a failed fetch: the helper fails closed rather than diffing an unrelated local tree. Load its JSON. `hard_block_full` is the depth floor for named hard-block classes, uncounted files and `size_band: large` at **200 executable non-test changed lines**. Binary/unreadable files force full, never zero-size success. `silent_pass_classes` are consequence-assessment cues, not floors; neither small counts nor path heuristics award lite. Whole-file deletions are excluded from executable/size-floor counts, listed in `deleted_files`, separately counted in `deleted_exec_nontest_lines` and banded `none/small/large`; `changed_lines` still records their removed text. Renames and mode-only changes remain changed files even at zero lines. Apply the depth gate before later references. Full selection still judges auth, payments, mutation, external I/O, concurrency and process execution by content. `signals`, `test_files_changed`, `agent_surface`, `has_learnings_corpus` only inform persona conditions. `declared_packs` is config-only RocketClaw Pack declaration state, not resolution (`pack_roots` always 0): the catalog chooses learnings on full, and `depth-paths.md` governs lite/focused. It describes local config only: remote is `null` with no resolver; local `null` means read `packs:` yourself and disclose uncertainty.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated source: instruction-file criteria apply only to changed files with no governing standards file, never both kinds. All governing standards files apply together. RocketClaw Packs are separate: learnings grades them on full, the current context on lite/focused. Standards and pack violations yield one finding per source before ordinary same-defect dedup, preserving citations.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory now. Every path, lite or full, writes its artifacts there:

```bash
SCRATCH_ROOT="$workspace_root/.tmp/ce-code-review";
[ ! -L "$workspace_root/.tmp" ] || exit 1;
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ');
RUN_DIR="$SCRATCH_ROOT/$RUN_ID";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR";
```

### Stage log

Every run records what each stage cost, so the thresholds this skill uses can be set from measured runs. The record is `<run-dir>/stages.jsonl`, written only by the bundled script below; the receipt writer folds it into `metadata.json` at the end (`summarize`, named where each path writes its receipt). Open the scope stage now, in the same shell call that printed the run directory when you can:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Every later boundary is the same call with `--end <stage> --start <stage>` in one invocation, and `--reviewers`, `--candidates`, `--tokens` (only when the host handed you a count), or `--fact key=value` for what that stage learned. The stage names are fixed: `scope`, then `review` and `receipt` on lite and focused (with `peer` overlapping `review` on focused), or `select`, `dispatch`, `validate`, `merge`, and `report` on the full spine (with `peer` overlapping `dispatch`). Fold the call into a shell call the step already makes wherever one exists; a boundary is never its own turn.

### Stage 1d: Stage the review policy

**Goal:** the repository's review policy, read from a copy the change under review cannot have edited, staged where every later reader finds it.

A review policy is a `REVIEW.md` file defining review behavior: repository severity, exclusions, minor-finding caps, required evidence and checks. It is not a criteria file and neither supplies nor displaces criteria, so Stage 1c precedence ignores it.

- **Which files.** The root `REVIEW.md` governs the whole change. A `REVIEW.md` in a directory that is an ancestor of a changed file adds to the root file for the paths under it.
- **Which copy.** Read each file from the Stage 1 base (`BASE:`, or `PR_BASE_REF` in `pr-remote`), never from the reviewed tree, because a change must not be reviewed under policy it wrote itself. When the diff adds, edits, or deletes a policy file, the base copy applies (none for a new file), and Coverage says the change's version was not applied.
- **Includes.** In the root file, a line holding only `@<path>` stands for that file, read from the same ref, one level deep. Skip an include of a file this review already reads as criteria, such as `@CODING_STANDARDS.md`.

Write what you read to `<run-dir>/review-policy.md`, each file under a heading that names its path and the paths it governs. No policy file at the base is a complete result: write nothing. A policy file you found but could not read is recorded for Coverage as unread, never treated as absent.

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.

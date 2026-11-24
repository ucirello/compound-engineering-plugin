# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Discover `workspace_root` as the absolute `jj workspace root`. From then on run JJ commands at that absolute root, for example `(cd "$workspace_root" && jj …)`. Use `--ignore-working-copy` for captured-revision inspection; initially resolve `@` with normal snapshotting to capture local changes. All repository-scoped GH calls run as `(cd "$workspace_root" && git_dir="$(jj git root)" && export GIT_DIR="$git_dir" && gh …)`; a failed root lookup is not permission to call unscoped GH. See [JJ CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/) and [revsets](https://docs.jj-vcs.dev/latest/revsets/).

**Capture once.** Resolve each selected revision to exactly one immutable commit ID, using `jj log --no-graph -r "$rev" -T 'commit_id ++ "\n"'`. For an inferred merge base use `fork_point(<verified-base-tip> | <verified-head>)`, not a default branch guess. Stop if a required local endpoint or fork point is missing or ambiguous. Use the same concrete `DIFF_A` and `DIFF_B` for the diff, helper, reviewer prompts, validation, and any peer. To resolve a current bookmark, check exact local bookmarks on `@` and its parent, respecting task context; an empty working-copy change over the named bookmark is normal. Do not infer a current branch when several names fit. The local reviewed head still includes working-copy changes.

- **Explicit `base:`:** use its exact resolved ID as `DIFF_A` and the captured `@` as `DIFF_B`, with `standalone` scope. No auto-detection, fetch, or second merge-base pass. Use native JJ bookmark syntax such as `main@origin`; a legacy `origin/main` spelling can map to the verified equivalent, never an unrelated same-named local bookmark. If combined with a PR or branch target, stop: pass `base:` alone for the current workspace, or the target alone so scope resolution can choose the base.
- **PR number/URL:** do not check out the PR. Use the scoped `gh pr view <number-or-url> --json number,state,title,body,baseRefName,baseRefOid,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,url,files,reviews,comments`. `hasPriorComments` is true for any comment or review other than a bodyless approval. Stop on CLOSED/MERGED. For an apparently automated/trivial PR, use the cheap native reviewer of `references/subagent-model.md` to judge the title/body/file paths. Only skip on a positive judgment (lock-file or manifest-only bumps, release automation, version-only increments); uncertain or unavailable judgment means review. Draft PRs are reviewed normally. Emit skipped reasons as plain text, or `{"status":"skipped","reason":"<same message>"}` in agent mode.
  - Resolve the captured base tip and head OIDs locally, fetching only if needed from the corresponding verified remotes without changing the workspace: `(cd "$workspace_root" && jj --ignore-working-copy --config git.abandon-unreachable-commits=false git fetch --remote "$remote" --branch "$exact_branch_pattern")`, using `exact:"<branch>"` pattern syntax. Use the actual PR head repository (including a fork when a corresponding verified remote is available); a successful fetch is not proof of the requested OID. If the exact OID is still unavailable, omit the unavailable endpoint and record why. Never use a different branch tip.
  - **`local-aligned`** requires a verified local bookmark matching the PR head name, a non-fork PR, and the verified PR head in the captured workspace head's ancestry (`<headRefOid> & ::<working-copy-id>` resolves to the head OID). Use the unique fork point of the verified base tip and local head for `DIFF_A`, with the workspace head as `DIFF_B` and `BASE:` equal to `DIFF_A`. The local tree includes committed work and unpushed fixes; do not mix in GitHub hunks. If the required base is unavailable, do not silently switch to a remote-only review that omits local changes.
  - **`pr-remote`** otherwise: `BASE:` is `pr:<number-or-url>` (logical marker); `PR_HEAD_REF`/`DIFF_B` is the verified head OID when available, and `PR_BASE_REF`/`DIFF_A` is the unique fork point of that head and the verified base tip when proven. Use the exact native endpoint diff when both are known. Otherwise obtain `DIFF:` with scoped `gh pr diff <number-or-url> --color=never`, and `FILES:` from PR metadata. Verify the PR head and base OIDs still match after obtaining the remote diff; if the diff failed or the PR moved, stop and give the caller the reason rather than using the working tree. Note missing evidence and endpoint limits in Coverage. Do not use an assumed base like `main` for policy, deleted bodies, or schema checks.
- **Branch target:** if it is verified as the current bookmark, use standalone below. Otherwise try scoped `gh pr view <branch> --json baseRefName,url,headRefName`; when an associated PR exists, prefer the PR route. Without one, resolve the branch on the verified remote (`<branch>@<remote>`, fetch the exact branch if necessary) or the corresponding verified local bookmark; stop if unresolved without a checkout. Resolve the verified default base, then use the unique fork point and captured branch head. Scope is `branch-remote`; set `BASE:` to `DIFF_A`.
- **Standalone, no explicit base:** use the current bookmark's PR base when known (pass the verified bookmark explicitly to scoped `gh pr view`), otherwise the repository's verified default branch, e.g. via scoped `gh repo view --json defaultBranchRef`. Resolve that base on the verified remote or the corresponding verified local bookmark. Use the unique fork point and captured workspace head. If the base cannot be established, stop; reviewing `@` against its parent would silently miss committed changes.

**Stage the selected evidence.** For native comparisons get `FILES:` from `jj diff --from "$DIFF_A" --to "$DIFF_B" --name-only` and save the successful output of `jj diff --from "$DIFF_A" --to "$DIFF_B" --git --context 10` locally. Do not use a default revision. For both native and GitHub patches, retain whole-file deletion headers and omit their bodies for reviewers. Filter the already saved patch (so diff failure is never hidden):

```bash
awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}' "$raw_diff" > "$review_diff"
```

Use private workspace-local scratch as specified below whenever writing evidence, including early PR fallback. `UNTRACKED:` records known paths omitted from the snapshot, including any JJ untracked/oversized warnings; explicitly ignored paths stay out of scope. JJ normally snapshots new non-ignored files as tracked: those are in scope, with no separate staging step. When there are omitted paths, list them in Coverage and continue with the captured tree.

Pass the absolute `workspace_root`, both exact endpoints, and the scope mode with review context. In `pr-remote` pass `<pr-head-ref>` and `<pr-base-ref>` only when verified; in `branch-remote` pass `<branch-head-ref>`. In either remote mode reviewers and validators must not Read/Grep workspace paths for changed files: use the pinned `jj file show` recipe in `references/diff-scope.md` against the verified head, or supplied hunks when unavailable. Local reviewers may inspect live files only while they still match the captured head.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` and both exact endpoint IDs as captured in Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  (cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>");
else
  (cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --local --base "$DIFF_A" --head "$DIFF_B" --docs-root "<root>");
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then refuses to count rather than comparing with the unrelated workspace. Load the JSON result. `hard_block_full` is the floor for the Review depth gate in `references/modes-and-output.md`: named hard-block classes, uncounted files, and a `size_band` of `large` (executable non-test added plus deleted lines at the full floor). `silent_pass_classes` names guards for consequence assessment, not a floor. No count alone awards lite. Whole-file deletions contribute to `changed_lines` when countable, never the executable floor; `deleted_files`, `deleted_exec_nontest_lines`, and `deleted_band` (`none`, `small`, or `large`) preserve separate deletion coverage. `signals`, `test_files_changed`, `agent_surface`, `has_learnings_corpus`, and `declared_packs` inform selection without making it automatic. `declared_packs` is read from local configuration alone (`pack_roots` stays 0); it is `null` without a local scope, and a local `null` means read the configuration's `packs:` key directly. The depth gate precedes content-based risk assessment on the full spine.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out. Use `(cd "$workspace_root" && jj --ignore-working-copy file list -r "$DIFF_B")` when the tree is not the live workspace (including remote scope). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not. An unavailable head is uncertain coverage, not proof that no criteria apply.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` applies cumulatively. When two of them state rules that cannot both hold for the same changed file, the one whose directory is nearer that file decides it, so a nested file's rule wins only for changed files under its directory. Declared Compound Packs are not a criteria kind here. On the full spine they select `learnings-researcher`, which grades them; on the lite and focused paths they are graded in context. Either way they are graded separately from criteria files, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory when Stage 1 first needs to save evidence, and reuse it for every path. If outside JJ and writing a failure receipt, use the absolute local directory in place of `workspace_root`. Never fall back to OS-global storage:

```bash
for part in .tmp .tmp/rocketclaw .tmp/rocketclaw/code-review; do
  dir="$workspace_root/$part";
  [ ! -L "$dir" ] && (umask 077; mkdir -p "$dir") && [ ! -L "$dir" ] && [ -O "$dir" ] || exit 1;
done
RUN_DIR=$(umask 077; mktemp -d "$workspace_root/.tmp/rocketclaw/code-review/run-XXXXXXXX") || exit 1;
RUN_ID="${RUN_DIR##*/}";
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

A review policy is a `REVIEW.md` file: instructions for how review behaves in this repository, such as what each severity means here, paths or classes of finding to skip, a cap on minor findings, the evidence a class of finding needs, or checks to run on every change. Claude Code Review reads the same file. It is not a criteria file: it neither supplies criteria nor displaces them, so Stage 1c's precedence ignores it.

- **Which files.** The root `REVIEW.md` governs the whole change. A `REVIEW.md` in a directory that is an ancestor of a changed file adds to the root file for the paths under it.
- **Which copy.** Read each file from the captured `DIFF_A`, never from the reviewed tree, because a change must not be reviewed under policy it wrote itself. Use `(cd "$workspace_root" && jj --ignore-working-copy file show -r "$DIFF_A" -- "$policy_path")`. When the diff adds, edits, or deletes a policy file, the base copy applies (none for a new file), and Coverage says the change's version was not applied. If the base could not be verified, record policy coverage as unavailable, not as no applicable policy.
- **Includes.** In the root file, a line holding only `@<path>` stands for that file, read from the same ref, one level deep. Skip an include of a file this review already reads as criteria, such as `@CODING_STANDARDS.md`.

Write what you read to `<run-dir>/review-policy.md`, each file under a heading that names its path and the paths it governs. No policy file at the base is a complete result: write nothing. A policy file you found but could not read is recorded for Coverage as unread, never treated as absent.

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.

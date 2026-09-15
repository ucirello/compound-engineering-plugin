# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-bookmark detection, remote resolution, and common-ancestor computation. Use the provided value directly:

```
workspace_root=$(jj workspace root) || { echo "not a jj workspace" >&2; exit 1; }
BASE_ARG="{base_arg}"
BASE=$(cd "$workspace_root" && jj log -r "heads(::@ & ::$BASE_ARG)" --no-graph -T 'commit_id ++ "\n"' -n 1) || BASE="$BASE_ARG"
```

Then produce the same output as the other paths (all `jj` commands with cwd at the workspace root so file lists are repo-relative):

```
(cd "$workspace_root" && echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --context 10 && echo "UNTRACKED:")
```

Unignored files are already in the working-copy change; `UNTRACKED:` is empty. This path works with any revset — a commit id, `main@origin`, a bookmark name. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or bookmark target — `base:` implies the current workspace is already the correct change. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** edit the PR bookmark. Scope comes from GitHub read APIs plus optional local alignment when `@` already matches the PR head bookmark.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
workspace_root=$(jj workspace root) || { echo "not a jj workspace" >&2; exit 1; }
GIT_DIR=$(cd "$workspace_root" && jj git root)
GIT_DIR="$GIT_DIR" gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
GIT_DIR="$GIT_DIR" gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` (logical marker — not a commit id). Set `UNTRACKED:` empty on the **current** workspace (unignored files are already in the working-copy change; usually empty during PR-remote review).

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. Bookmarks on `@` (`jj log -r @ --no-graph -T 'bookmarks'`, cwd at the workspace root) include `headRefName`.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. The PR head commit is contained in the local workspace: `jj log -r '<headRefOid> & ancestors(@)' --no-graph -T 'commit_id ++ "\n"' -n 1` prints a commit id. This confirms the working copy actually carries the PR head (allowing unpublished local fixes layered on top) rather than an unrelated same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep/`jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working copy is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-ref>` from `baseRefName` (fetch if needed). Compute `BASE` as the unique common ancestor (`jj log -r 'heads(::@ & ::<resolved-base-ref>)' --no-graph -T 'commit_id ++ "\n"'`), then set `FILES:` from `jj diff --from $BASE --name-only` and `DIFF:` from `jj diff --from $BASE --context 10` (cwd at the workspace root; includes the working-copy change on the PR bookmark). Do **not** call `gh pr diff` or append remote hunks — when unpublished fixes exist, the local tree is canonical. Note in Coverage: `scope: local-aligned (PR; local tree diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `GIT_DIR="$GIT_DIR" gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to editing the working copy.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch PR head without changing the working copy: `(cd "$workspace_root" && jj git fetch --remote origin --branch <headRefName>)`.
2. When fetch succeeds, set `PR_HEAD_REF=<headRefName>@origin` for reviewers and validators. When fetch fails, omit `PR_HEAD_REF` and note in Coverage — reviewers must rely on diff hunks only.
3. Best-effort fetch the PR base without changing the working copy: `(cd "$workspace_root" && jj git fetch --remote origin --branch <baseRefName>)`. When it succeeds, set `PR_BASE_REF` to `<baseRefName>@origin` — a **real jj base revset** reviewers and validators use for file-level diffs (e.g. `data-migration-reviewer` runs `jj diff --from <PR_BASE_REF> -- db/schema.rb`/`structure.sql`). The `pr:<number-or-url>` logical marker in `BASE:` stays the scope marker; `PR_BASE_REF` is the diffable base. When the fetch fails, omit `PR_BASE_REF` and note in Coverage — schema-drift and other diff checks fall back to diff hunks only and must **not** assume `main`.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a bookmark name is provided as an argument:**

Substitute the provided bookmark name as `<branch>`. Do **not** edit `<branch>`.

If bookmarks on `@` include `<branch>`, use the **standalone (current bookmark)** path below — same tree, explicit bookmark name; do not use remote-only diff.

Otherwise diff the remote/local ref **without changing the working copy**:

1. Try `GIT_DIR="$GIT_DIR" gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve `<branch>` as `<branch>@origin` or `<branch>` after `(cd "$workspace_root" && jj git fetch --remote origin --branch <branch>)` when needed.
3. Resolve default base bookmark (same logic as standalone). Compute `BASE` as `jj log -r 'heads(::<base-ref> & ::<branch-ref>)' --no-graph -T 'commit_id ++ "\n"'` and `jj diff --from $BASE --to <branch-ref> --context 10`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff bookmark `<branch>` without editing the working copy. Edit that bookmark, pass its open PR URL/number, or review the current change with `base:`."

On success for remote bookmark diff, set **branch-remote scope**. The working copy is **not** `<branch>`. Include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref><branch-ref></branch-head-ref>` in the Stage 4 review context bundle. Reviewers and Stage 5b validators must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <branch-ref> <path>` or diff hunks only.

Produce (cwd at the workspace root):

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to "<branch-ref>" --name-only && echo "DIFF:" && jj diff --from "$BASE" --to "<branch-ref>" --context 10 && echo "UNTRACKED:"
```

**If no argument (standalone on current bookmark):**

Apply the same base-detection logic as bookmark mode above, using the current bookmark (i.e., `GIT_DIR="$GIT_DIR" gh pr view --json baseRefName,url` with no argument defaults to the current bookmark).

If no base can be resolved, **stop**. Do not fall back to `jj diff` (working-copy vs parent) — a standalone review without the base would only show the current change and silently miss ancestor work on the bookmark.

On success, produce the diff (cwd at the workspace root):

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --context 10 && echo "UNTRACKED:"
```

Using `jj diff --from $BASE` diffs the common ancestor against the working-copy commit, which includes the whole unpublished change.

**Untracked file handling:** Always inspect `UNTRACKED:`. Unignored files are already in the working-copy change (`jj diff`); ignored untracked paths stay out of scope. When `UNTRACKED:` is non-empty, list excluded files in Coverage and continue on the reviewed change only — never stop or prompt.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a real SHA/ref), `DIFF_B` empty (diffs base vs working tree).
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then refuses to compute rather than comparing the fetched base to the unrelated local workspace. Load the JSON result. `hard_block_full` and a `size_band` other than `small` are floors for the Review depth gate in `references/modes-and-output.md`; they do not award lite. `signals` are path heuristics, not selection decisions and not a lite block. After this stage, apply that gate before reading any later reference. On the full spine, Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, `has_learnings_corpus`, and `declared_packs` as inputs to the conditions that select generic reviewers, not as automatic spawn decisions. `declared_packs` reports whether the local RocketClaw config names any Pack, read from the config alone (nothing is resolved, so `pack_roots` is always 0); the learnings selection rule in `references/persona-catalog.md` decides what that fact selects. It describes the local checkout, so the helper evaluates it only in local scope: in remote scope it is `null` and no resolver runs. In local scope, `null` means the helper could not tell; read the config's `packs:` key yourself.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` still applies together. Declared Packs are not a criteria kind here: they select `learnings-researcher` on the full spine and are graded by it independently, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory now. Every path, lite or full, writes its artifacts there:

```bash
workspace_root=$(jj workspace root) || { echo "not a jj workspace" >&2; exit 1; }
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw";
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ');
RUN_DIR="$SCRATCH_ROOT/ce-code-review/$RUN_ID";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR";
```

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.

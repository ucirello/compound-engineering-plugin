# Determining the reviewed change and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Use Jujutsu for local repository state, revision resolution, history, file content, and diffs. Jujutsu snapshots non-ignored working-copy files into `@`; it has no staging area or current branch. Use `trunk()` for the configured default remote bookmark and `fork_point()` when a review needs the common ancestor of two revisions. Produce Git-format patches with `jj diff --git` because reviewer tooling consumes that patch format; this is an output format, not Git repository behavior.

**If `base:` is provided:**

The caller supplied the comparison base for the current workspace. Resolve exactly one fork point between it and `@`; stop if either revision or the fork point is missing or ambiguous.

```bash
BASE_ARG="{base_arg}"
BASE=$(jj log -r "exactly(fork_point($BASE_ARG | @), 1)" --no-graph -T 'commit_id ++ "\n"')
```

Then produce the local scope:

```bash
printf 'BASE:%s\nFILES:\n' "$BASE"; jj diff --from "$BASE" --to @ --name-only; printf 'DIFF:\n'; jj diff --from "$BASE" --to @ --git --context 10
```

Do not combine `base:` with a PR number or bookmark target. If both appear, stop: `base:` means the current workspace is the reviewed source.

**If a PR number or GitHub URL is provided:**

Do not change the working-copy revision. Keep GitHub review/provider operations in `gh`. In a non-colocated Jujutsu repository, set `GIT_DIR="$(jj git root)"` for `gh` commands so GitHub CLI can locate the backing repository.

First run `gh pr view <number-or-url> --json state,title,body,files`. Stop without reviewer dispatch when the PR is closed or merged. Use the existing lightweight judgment for trivial automated PRs; draft PRs remain reviewable. Return the existing plain-text or `mode:agent` JSON skip shape.

Fetch metadata without checkout:

```bash
gh pr view <number-or-url> --json number,title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,baseRepository,headRepository,files,reviews,comments --jq '{number, title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, baseRepositoryUrl: .baseRepository.url, headRepositoryUrl: .headRepository.url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Resolve the GitHub base and head repository URLs against `jj git remote list` by canonical repository identity, treating equivalent HTTPS, `ssh://`, and SCP-style URLs and an optional `.git` suffix as the same repository. Each URL must map to one remote name. Stop on multiple matches rather than choosing by order or name. When no remote matches a URL, keep that side provider-only and do not invent a remote; this makes the scope `pr-remote` unless the missing side is irrelevant to the required local operation. Record the unique matches as `BASE_REMOTE` and `HEAD_REMOTE` and use those names in every fetch and remote-bookmark revset below; never assume `origin`.

Set `BASE:` to `pr:<number-or-url>`. When `HEAD_REMOTE` is available, fetch `<headRefName>` from it before testing local alignment. Classify the scope as `local-aligned` only when the PR is not cross-repository, both repository URLs resolved to unique remotes, the PR head commit resolves locally, and it is an ancestor of `@`. Check ancestry by counting `commit_id(<headRefOid>)::@`; a bookmark-name comparison is invalid because Jujutsu has no current bookmark.

- **`local-aligned`:** Fetch the base bookmark with `jj git fetch --remote "$BASE_REMOTE" --branch <baseRefName>` when needed. Resolve `BASE` as exactly one `fork_point(<baseRefName>@<BASE_REMOTE> | @)`. Set `FILES:` and `DIFF:` with `jj diff --from "$BASE" --to @ --name-only` and `jj diff --from "$BASE" --to @ --git --context 10`. Do not append `gh pr diff`; the workspace revision is canonical and may include local follow-up changes.
- **`pr-remote`:** Set `FILES:` from the PR `files` array and `DIFF:` from `gh pr diff <number-or-url> --color=never`. If that fails, stop rather than changing revisions. Supply `<pr-head-oid>` and the PR number in review context. Reviewers inspect remote file content with `gh api repos/{owner}/{repo}/contents/<path>?ref=<headRefOid>` and decode the returned content, or rely on supplied diff hunks. They never read changed workspace paths as if those represented the PR.

For `pr-remote`, do not fetch a synthetic local ref. The full GitHub patch is authoritative, and provider content APIs supply reviewed-head files. Schema-drift and other file-level comparisons use the supplied patch when the workspace is not aligned.

**If a bookmark name is provided:**

Do not change the working-copy revision. First try `gh pr view <bookmark>` and prefer the PR path when it resolves. Otherwise inspect the exact local bookmark and every exact-name remote bookmark from `jj bookmark list --all-remotes <bookmark>`. Reconcile their targets before choosing scope: fetch the named bookmark from each matching remote when refresh is needed, then resolve the local bookmark and all `<bookmark>@<remote>` candidates to commit IDs. Continue only when all surviving candidates identify one commit; stop when they disagree or any candidate is conflicted. If no candidate resolves, stop and ask for an open PR URL/number, an existing Jujutsu revision, or `base:<revision>` for the current workspace. Use the reconciled commit as `<bookmark-revision>`; do not prefer `origin`, the local bookmark, or the first listed remote.

If the target resolves to `@`, use the standalone path. Otherwise resolve `BASE` as exactly one `fork_point(trunk() | <bookmark-revision>)`, set scope to `bookmark-remote`, and produce:

```bash
printf 'BASE:%s\nFILES:\n' "$BASE"; jj diff --from "$BASE" --to "<bookmark-revision>" --name-only; printf 'DIFF:\n'; jj diff --from "$BASE" --to "<bookmark-revision>" --git --context 10
```

Include `<pr-scope-mode>bookmark-remote</pr-scope-mode>` and `<bookmark-revision>...</bookmark-revision>` in reviewer context. Reviewers use `jj file show -r <bookmark-revision> <path>`, `jj file annotate -r <bookmark-revision> <path>`, targeted `jj log`, or supplied hunks; they do not inspect changed workspace paths.

**If no target is provided:**

Resolve `BASE` as exactly one `fork_point(trunk() | @)`. If `trunk()` resolves only to the virtual root because no default remote bookmark is configured, stop rather than silently reviewing an incomplete range. Produce the local scope with the same `jj diff --from "$BASE" --to @` commands as the `base:` path.

For GitHub metadata discovery, inspect bookmarks on `::@` with `jj bookmark list -r '::@'` and try the relevant local bookmark with `gh pr view`; never infer a current branch. If no associated PR is found, continue as standalone.

**Tracked-file behavior:** The reviewed local tree is revision `@`, including automatically tracked additions after Jujutsu snapshots the workspace. Ignored or explicitly untracked files are outside the revision and therefore outside review scope. State that exclusion in Coverage when `jj status` reports such paths; do not prompt.

### Stage 1b: Compute scope signals

Run `scripts/review-scope.py` from this skill's directory. It validates Jujutsu revision endpoints, counts executable lines from `jj diff --git`, derives changed-path signals, and fails closed for lite eligibility.

Set `DIFF_A` and `DIFF_B` to the exact endpoints already used:

- **`local-aligned`, standalone, or `base:`:** `DIFF_A="$BASE"`, with no `--to`; the helper compares to `@`.
- **`bookmark-remote`:** `DIFF_A="$BASE"`, `DIFF_B=<bookmark-revision>`.
- **`pr-remote`:** Do not call the local helper against unrelated revisions. Derive only path signals from the authoritative GitHub file list and force `lite_eligible:false`; remote patch size or parse uncertainty fails closed to the full roster.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "bookmark-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --to "$DIFF_B" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>";
fi
```

Load the JSON result. `exec_lines:null`, any `uncounted_files > 0`, remote-scope uncertainty, or helper failure disqualifies the lite path. Signals inform reviewer selection but never decide it by themselves.

# Determining the reviewed diff and scope

Read at Stage 1. Resolve endpoints once, without moving the user's working copy. All JJ commands execute from the target workspace's absolute root, not merely with `-R`. Set `workspace_root` to the absolute result of `jj workspace root`; use `(cd "$workspace_root" && jj ...)`. For every repository-scoped GitHub call use `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`.

Authoritative commands: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.

## Stage 1: Resolve scope

- **Explicit `base:`:** validate it resolves to exactly one JJ revision and use it directly, without base detection. Resolve Git-style remote names to verified JJ remote bookmarks (`main@origin` rather than `origin/main`). Reject `base:` combined with a PR or branch target; it means the current workspace is the reviewed tree.
- **PR number/URL:** never check out or edit to the PR. Probe `gh pr view <target> --json state,title,body,files` with the preamble above. Closed/merged PRs stop as skipped. Explicitly request a lightweight trivial-PR judgment reviewer, using a cheap capable model only when model overrides are permitted; otherwise inherit. Give title/body/paths and ask whether it is automated/trivial (manifest-only bumps, automated release/version changes); uncertainty means review. If delegation cannot run, conservatively continue, not silently skip. Draft PRs are reviewed normally. Default skipped output is plain text; `mode:agent` is only `{"status":"skipped","reason":"<reason>"}`.
- Fetch PR metadata via `gh pr view <target> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments,headRepository,headRepositoryOwner`. Preserve prior-comment presence. Classify **local-aligned** only with verified head repository/remote identity, non-cross-repository PR, matching local bookmark, and the exact PR head as an ancestor of `@` (`jj log --no-graph -r '<headOid> & ancestors(@)'`). An empty `@` directly above the head is aligned. Matching names alone never suffice. Otherwise use **pr-remote**.
- **local-aligned:** resolve/fetch the verified base bookmark through `jj git fetch --remote <verified-remote> --branch <base>`, choose the single `heads(::@ & ::<base>)`, and diff that base to `@`. Missing or multiple common-ancestor heads fail closed rather than selecting an arbitrary base. Run fetch and revision queries from the target workspace's absolute root. Includes recorded and current working-copy changes; never mix remote hunks into this canonical local diff.
- **pr-remote:** use PR `files` and `gh pr diff <target> --color=never`, with scoped `GIT_DIR`. Failure stops with an actionable error, never checkout fallback. Set logical `BASE=pr:<target>`. Best-effort fetch verified PR head/base repositories and bookmarks through JJ. Only set `PR_HEAD_REF` when its commit ID equals the metadata head OID; a same-named origin branch is not proof for fork PRs. Set `PR_BASE_REF` to the verified concrete base ID, never the logical PR marker or a guessed `main`. If unavailable/moved, omit endpoints, report Coverage, and use supplied hunks only.
- **Branch/bookmark target:** if the verified bookmark identifies the current reviewed lineage, use standalone scope. Otherwise try its PR first; absent a PR, fetch/resolve the verified remote bookmark through JJ without checkout. Resolve the default base, select a single common ancestor, and diff to the selected head as **branch-remote**. An unresolved/ambiguous target stops; never inspect unrelated workspace files.
- **Standalone:** inspect bookmarks on `@` and, for an empty working-copy tip, `@-`; resolve the eligible PR/default base against the verified remote. Stop if no base is known: diffing only `@-` would silently miss recorded work. Select the single common ancestor of `@` and verified base.

For a real base/head pair, obtain paths with `jj diff --from <base> --to <head> --name-only` and exact hunks with `jj diff --from <base> --to <head> --git`. Use `head=@` for local scope. Preserve `BASE`, `FILES`, `DIFF`, and `UNTRACKED` outputs. Inspect `jj status` and applicable tracking rules for files left untracked; list excluded paths in Coverage, never automatically track them or stop to prompt. Newly JJ-tracked paths in the diff are in scope; there is no Git staging distinction.

Remote reviewer/validator context contains `<pr-scope-mode>pr-remote</pr-scope-mode>` or `branch-remote`, plus verified `<pr-head-ref>`, `<pr-base-ref>`, or `<branch-head-ref>` when available. Inspect remote files with `jj file show -r <head> <path>` and list with `jj file list -r <head>`. Never Read/Grep changed workspace paths for remote scope; absent a verified head, use hunks only.

## Stage 1b: Deterministic scope signals

Keep the support helper `scripts/review-scope.py`: it computes exact patch counts, path classes and floors, not dispatch or workspace lifecycle. Invoke from the absolute target root:

```bash
(cd "$workspace_root" && python3 "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>")
# Remote scope always supplies --head, including empty values after a failed fetch:
(cd "$workspace_root" && python3 "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>")
```

Local `DIFF_A` is the concrete base; remote endpoints are verified base/head IDs. Never compare a remote base to local `@` after a failed fetch. `hard_block_full` forces full for hard-block classes, uncounted files, unknown endpoints and large executable non-test changes (200 lines). `silent_pass_classes` forbids lite for guards. Neither a small count nor heuristic `signals` awards lite. Apply the depth gate in `references/modes-and-output.md` before later references. Stage 3 judges content risks (auth, payment, mutation, external I/O, concurrency, process execution). `test_files_changed`, `agent_surface`, `has_learnings_corpus` are selection inputs, never automatic spawns. `declared_packs` is local config fact only, resolver `--declared-only`, `pack_roots=0`; remote scope returns null. Unknown local declarations require reading `packs:` directly.

## Stage 1c: Criteria mapping

Enumerate `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` in the reviewed tree. Keep files whose directories are ancestors of changed paths. All governing standards files apply together. Instruction files supply criteria only for paths with no governing standards file; never grade a path against both kinds. Declared Compound Packs select learnings independently, not a criteria kind. An empty successful mapping is complete; failed/uncertain search is Coverage uncertainty, never an empty mapping.

Create one private run directory under `$workspace_root/.tmp/rocketclaw/code-review/<run-id>/`; all lite/full/focused artifacts, errors and fallback files stay there. Reject symlinks or ambiguous ownership, create with umask 077, verify ownership and permissions, and preserve its absolute path. Without a JJ repository use local `.tmp/` only. Never fall back to OS-global temporary storage.

## Stage log and visibility

Retain `scripts/run-log.py` for `<run-dir>/stages.jsonl` and receipt summaries. Use Python 3 from the absolute workspace cwd; start `scope` when creating the run dir. Later calls use `event --run-dir "$RUN_DIR" --end <stage> --start <stage>` and applicable `--reviewers`, `--candidates`, `--tokens` only if supplied by the host, and `--fact key=value`. Stages remain `scope`, then `review`/`receipt` for lite/focused with peer overlapping review, or `select`, `dispatch`, `validate`, `merge`, `report` for full with peer overlapping dispatch. Fold boundaries into existing shell calls, never waiting turns. `summarize` folds the log into metadata.

Use supported task tracking for outcomes after scope resolves, not individual setup calls/personas. Add a cross-model task only after a native peer starts; close it on terminal collection. Without task tracking continue normally, not a simulated chat task list.

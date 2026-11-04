# Determining the reviewed diff and scope

## Stage 1: Capture scope once

All JJ subprocesses run with cwd set to the absolute target workspace root. Locate it by walking to the nearest `.jj` entry, then verify `jj root` there. Shell examples use `(cd "$workspace_root" && jj ...)`. Never invoke the Git executable, even for history or review. Scope repository GitHub calls as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

Resolve every revision to exactly one full commit ID with `jj log -r <revset> --no-graph -T 'commit_id ++ "\n"'`; zero, ambiguous, or conflicted endpoints fail closed. Escape literal bookmark names in revsets. Capture reviewed head and base IDs before counting or dispatch. Never replace that captured range with parent/per-commit statistics, a hardcoded main, or a subsequently recomputed merge base.

- **`base:`:** mutually exclusive with a PR/branch target. Use the explicitly supplied verified base directly against the captured working-copy commit `@`. Do not silently replace it with a common ancestor.
- **PR number/URL:** do not check out or edit the target. Read state/title/body/files first with scoped `gh pr view`; closed/merged skips. A native lightweight trivial-PR judge may skip automated dependency/release-only changes only when certain; doubt means review. Use `dispatch-reviewers.md` permission/model rules, including inherited model when override permission is absent. Fetch metadata including `baseRefName`, `baseRefOid`, `headRefName`, `headRefOid`, repository identities, comments/reviews and URL. Draft PRs are reviewed normally.
- **Local-aligned PR:** require verified source repository/remote identity, matching bookmark identity, non-fork PR, and PR head in `::@`. An empty `@` above the PR head is normal. Preserve local fixes, dirty/conflicted work and ignored/untracked content; no checkout, rewrite or cleanup. Resolve the unique common ancestor using `heads(::(<base>) & ::(<captured-head>))`. Local scope includes all captured working-copy changes, not merely remote PR hunks.
- **PR-remote:** any failed alignment check means remote scope. Use scoped `gh pr diff <target> --color=never`, checking success before filtering. Best-effort `jj git fetch --remote <verified-remote> --branch <name>` from the absolute root may make endpoints available; never assume origin's same-named branch is a fork head. Accept `PR_HEAD_REF`/`PR_BASE_REF` only when exact IDs equal metadata. Otherwise use remote hunks only, omit unavailable endpoints and record incomplete evidence. Logical `BASE: pr:<target>` is not a diffable revision. Never inspect changed workspace files for a remote review.
- **Branch:** prefer its verified PR if present. Otherwise resolve the exact local/remote bookmark without checkout; a non-current target is `branch-remote`, inspected through `jj file show -r <captured-head> <path>` or hunks only. Resolve its verified base from actual PR/default-remote metadata, not a guessed main/master. No resolvable base means stop, not review only `@-..@`.
- **Standalone:** resolve current bookmark/PR and actual default remote base, choose the unique common ancestor, and capture the working-copy head. Stop if intent/base is ambiguous.

Persist scope mode, `BASE`, `DIFF_A`, `DIFF_B`, target identities and head IDs. Save `files.txt` and the exact full Git-format patch from `(cd "$workspace_root" && jj diff --from "$DIFF_A" --to "$DIFF_B" --git)` as `full.diff`. Use `jj diff --summary` for human inventory, not line counts. The helper counts this same exact endpoint range. A reviewer-facing copy may omit whole-file deleted bodies while retaining deletion headers; keep the full patch for mechanics. Read deleted bodies only as needed with `jj file show -r <base> <path>`. Do not stage files to include them: JJ tracks eligible new files automatically; ignored/untracked paths outside the captured tree stay excluded and are listed in Coverage. Verify the tree/range remains the captured one before dispatch/apply; movement requires explicit recapture and recount, never mixed artifacts.

## Stage 1b: Deterministic scope signals

Run the retained `scripts/review-scope.py` from the absolute root with `--base "$DIFF_A" --head "$DIFF_B" --docs-root "<root>"` for remote scope. For local scope omit `--head` (the helper reads captured `@`; verify it still matches the saved head). Remote endpoints remain explicit even if missing: unknown scope must fail closed, never fall back to local files.

Read the JSON facts, never estimate counts from a summary. Production/test classification, added plus removed lines, renames, binaries/uncounted files, executable modes, whole-file deletion bands and the **200 executable non-test changed-line full-spine floor** remain authoritative. Deletions band separately; binary deletions remain uncounted. `hard_block_full` is a floor, not a lite award. Silent-pass guard classes forbid lite. Other risk decisions still depend on consequence. `declared_packs` is config-only and local-scope-only; null means read `packs:` yourself, not no packs. `has_learnings_corpus` resolves `<docs_root>/solutions` relative to the absolute root. Apply the Review depth gate before later references.

## Stage 1c: Criteria and artifacts

Enumerate `CODING_STANDARDS.md`, `AGENTS.md`, and `CLAUDE.md` in the reviewed tree, not an unrelated workspace. Retain ancestor-directory criteria for changed paths. Every governing standards file applies; instruction-file criteria fill only paths with no governing standards file, never grade the same file against both kinds. Declared knowledge packs are a separate grading source. No criteria is valid; uncertain enumeration is an explicit coverage gap.

Create a private run directory only below `$workspace_root/.tmp/rocketclaw/ce-code-review/<run-id>` (date plus random suffix). Reject symlinked/escaping/unowned scratch paths; no OS temporary directory fallback. Persist `files.txt`, `full.diff`, scope facts and stage artifacts there on success and failure.

### Stage log

Use retained `scripts/run-log.py event --run-dir "$RUN_DIR" --start scope`. At subsequent boundaries combine `--end <stage> --start <stage>` with `--reviewers`, `--candidates`, `--tokens` only when provided by the host, and `--fact key=value`. Lite/focused stages are scope/review/receipt, full stages scope/select/dispatch/validate/merge/report; peer may overlap review/dispatch. Summarize into metadata with the retained helper. Stage boundaries are not extra waiting turns.

## Stage 1d: Review policy

Read governing ancestor `REVIEW.md` files from the captured base, never the change's edited version. Root single-line `@<path>` includes expand one level from that same base except files already consumed as criteria. Save policies and path ownership under headings in `<run-dir>/review-policy.md`. No policy is valid; unread policy is a coverage gap. Record any added/changed/deleted policy that was not applied. Policy is behavioral guidance, separate from criteria.

## Task visibility

Use native task tracking when available for review outcomes, not every persona/tool. Add peer tracking only after native launch succeeds; close it on collection/cancellation. No simulated task list or detached waiting when unavailable. Default skips return the reason; `mode:agent` skips emit only `{"status":"skipped","reason":"<reason>"}`.

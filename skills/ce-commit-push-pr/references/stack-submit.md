# Opt-in stack construction and submission with JJ

Before composing any layer description, read `commit-and-push.md` in full and execute its runtime full-guide and verified-history comparison. Repository syntax wins; do not derive a fixed syntax from this stack procedure.

Only enter for explicit stack intent or standing preference; do not suggest artificial stacks. A standing preference alone does not require splitting one logical change. Explicit stack intent is required and cannot silently fall back to one PR. Read `gh-stack-cli.md` before probing repository compatibility.

Run all commands in the target absolute JJ workspace root; export `GIT_DIR=$(jj git root)` before repository gh. Probe installed JJ/gh capabilities and repository stack support without invoking a local Git stack manager. Missing required stack support is a clear residual; a soft preference may fall back with disclosure.

## Topology and retrospective construction (before Step 3)

Record original revision, bookmark targets and complete change set, including intended untracked paths. Preserve a recovery bookmark before changing topology; never treat a snapshot as protection for ignored/untracked files. Resolve a named parent by PR number and exact head owner/OID, then fetch and verify the authoritative parent through JJ. An existing local-only parent is valid only when verified current; never substitute a stale remote or default base. Stop on conflicting bookmark identity or unproven topology rather than overwriting it. Preserve existing stack topology and ownership; another author's parent remains an untouched trunk unless adoption is authorized.

Plan the smallest independently reviewable linear layers, foundations first, using whole-file groups or existing commit boundaries. Inspect complete changes against the verified base, not just the latest commit. Each layer must stand against its immediate parent. One unambiguous safe split needs no additional ask under explicit stack intent. Materially different boundaries require a proposal; pipeline mode returns that proposal as a residual. Hunk partitioning or published-history rewrites require explicit permission, never implicit pipeline approval.

Honor `exclude:<paths>` on every layer: never save, move, restore or commit excluded work. Stop if construction could overwrite it. Preserve original work and human author/trailer identity; use JJ revisions/bookmarks rather than staging or branch checkout. Apply `commit-and-push.md`'s full runtime Go/history contract to every layer, with neutral repository-style descriptions and known single-unit IDs only. Existing suitable commit boundaries may simply receive verified bookmarks. For mixed working changes, use explicit-path `jj commit` and verify both committed and residual paths. Do not rewrite published layers without authorization.

Verify each parent edge, layer bookmark, recovery reference and the complete top-layer result against the original intended change set before submission. No earlier step submits.

## Submission (Step 5 only)

Apply the Project publishing gate to every outgoing layer. Resolve archival before publishing; if archival is requested and no stack-safe archival route exists, return a residual rather than silently disabling it or adding a post-submit explainer commit.

Reverify remote, permissions, base and PR presence for every layer. Publish each explicit bookmark through `jj git push --remote <remote> --bookmark <layer>` in dependency order. For a new PR use `gh pr create --head <layer> --base <immediate-parent>` with the composed title and local `.tmp/` body file. Query by head owner and bookmark before each create to avoid duplicates. Existing draft layers remain draft unless explicitly authorized ready; draft-only publication is a hard residual before default babysit, not successfully shipped ready work.

Map every created PR to its exact URL and head. Compose each body in PR mode against its actual immediate parent. Existing PRs preserve titles/bodies unless authorized factual maintenance or explicit rewrite applies; pipeline optional rewrite defaults to no. Do not invent stack-specific title improvements.

Report the bottom open non-draft PR and transfer follow-on to `ce-babysit-pr`, `posture:stack-ready` by default or `posture:stack-land` only on explicit land intent, passing stack-wide scope for pipeline submission. Never individually merge members. If the landing manager is incompatible with JJ, report that blocker; do not use a Git fallback.

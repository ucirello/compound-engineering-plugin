# Opt-in stack construction and submission

Load only for an explicit stack request or standing stack preference. An explicit request is required intent; unavailable hosted stack capability is a hard residual. A preference alone is soft intent: report unavailable capability and use the single-PR path. Do not invent artificial slices for one logical change unless the user explicitly requested them.

Run JJ from the target absolute workspace root; export `GIT_DIR=$(jj git root)` there before repository-scoped `gh`. Never invoke Git directly or through Git-backed stack helpers. Read `references/gh-stack-cli.md` before probing supported GitHub-only topology/link operations. Separate pre-Step-3 probe/topology/construction from Step-5 publishing: no earlier phase submits PRs.

## Probe and topology

Check `gh` availability and its GitHub-only stack-link capability with help. Record the original work bookmark, exact tip and complete pending diff before any topology changes. Preserve recovery bookmarks. Resolve any named parent by PR metadata when possible, verifying owner, head bookmark, exact head ID and base. Fetch only the exact necessary ref with JJ. A branch-only parent can be verified locally but must not be claimed as a hosted stack member without evidence.

For a confirmed managed parent, preserve its topology and use that exact parent, never silently the top of another layer. If the named parent is not the top and the hosted manager cannot insert the layer there, report a residual. Ambiguous membership, unsupported stacks and unproven parents are residuals. For a standalone parent, keep it as an untouched trunk unless the user owns the PR and adoption is authorized. A same-name local bookmark at a different commit is a collision: stop, never reset it. Validate command-bound bookmark names and pass arguments without shell interpolation.

Use the authoritative verified parent tip: current remote-tracking tip when it contains the parent's latest work, otherwise a verified local unpublished parent tip. Do not hardcode origin or use the repo default for an upstack layer. Existing isolation and excluded files remain untouched.

## Retrospective construction (before Step 3)

Inspect the complete range plus tracked and untracked pending changes. Plan the smallest useful linear, independently reviewable whole-file layers, foundation first, each coherent against its parent. Existing commit boundaries may be reused. Multiple materially different review boundaries require a concise bottom-to-top decision; pipeline mode returns that proposal as a residual. Hunk partitioning or rewriting published history requires explicit interactive authorization; pipeline mode stops with the required confirmation, never guesses.

On the default bookmark with no named parent, follow `branch-creation.md`, including fresh-base and unpushed-local-work decisions. On an existing feature bookmark, resolve the exact bottom base independently; never treat the entire feature tip as the bottom parent. Preserve original tip recovery bookmarks before rewriting owned unpublished changes.

Construct layers with native JJ: create each change at its verified parent with `jj new <verified-parent>`, commit only its planned whole-file paths using `jj commit <owned-paths> -m "<message composed from the standards above>"`, and create a unique bookmark at its verified commit with `jj bookmark create <layer> -r <verified-layer-commit>`. Before every message, read the full composition standards in `commit-and-push.md`, including runtime guide and full-history comparison. Preserve known unit IDs as semantic context, not fixed syntax.

Before changing working-copy revisions, preserve pending owned work in recoverable JJ changes and verify content. Never save, move, restore or commit `exclude:<paths>`; they belong to no layer and must remain exactly as found. If construction cannot preserve them or unrelated ignored/untracked content in place, stop with a residual. Do not discard or overwrite collisions. Reuse existing committed boundaries by bookmarking their exact tips; preserve human authorship and trailers. Verify every parent edge, bottom-to-top order and that the top contains the complete original change set minus excluded paths before publishing.

## Submit (Step 5 only)

Apply the project publishing gate to every exact layer being sent. Resolve teaching archival before publishing; if enabled, stop with a residual rather than making unmanager-aware post-submit explainer changes or silently disabling archival.

Verify head repository, push authority, remote, bookmark and commit for every layer. Push only those bookmarks with `jj git push --remote <verified-remote> --bookmark <layer>`; authorize new remote bookmarks explicitly with `--allow-new` where necessary. Create each PR against its immediate parent and link the verified hosted topology using the documented GitHub-only link operation. If unsupported or incomplete, report the precise partial state and residual, never claim successful stack submission.

Preserve existing drafts: do not mark any ready unless the user explicitly authorized it. Create new ready PRs for the shipping flow, unless the user requested drafts. A draft-only result is a hard residual before babysit when monitoring is on; never report a draft as shipped-ready. Existing stack titles/bodies remain unchanged absent an explicit update, authorized factual maintenance or separately approved optional rewrite; pipeline mode defaults to no optional rewrite.

For each new PR, compose from that explicit PR URL so its metadata supplies the immediate parent and exact head; apply through `gh pr edit <url> --body-file <local-file>`. Never select by the current bookmark implicitly. All body files live under the target workspace's `.tmp/`.

Step 5 exclusively owns submission and post-submit descriptions. Hand off the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only on explicit landing intent, preserving stack-wide scope for pipelines. Respect monitoring opt-outs and draft boundaries. Never use `gh pr merge` on managed members: landing belongs to the authorized stack landing workflow, with prohibited Git-backed operations reported blocked rather than bypassed.

# Opt-in JJ stack construction and publication

Load only when the user requests a stack or a standing preference wants one. Before Step 3 perform Probe, Topology and Construction only. Step 5 exclusively owns publishing and description application. Use JJ for local operations and `gh` for GitHub metadata/PRs; no Git stack checkout or index workflow.

Run JJ from the target workspace's absolute root and export `GIT_DIR=$(jj git root)` there before repository-scoped `gh`. Temporary saved evidence belongs under that workspace's `.tmp/`. See `references/gh-stack-cli.md` and https://docs.jj-vcs.dev/latest/git-command-table/ .

## Probe and topology

Check actual GitHub stack capability through `gh stack <command> --help` and repository metadata. If unavailable, explicit multi-PR intent or a standing preference requiring stacks stops with a clear residual; soft intent reports the residual and may use the ordinary single-PR path. Do not guess from an authentication/network failure that the parent is standalone.

When a parent is named, resolve its PR number preferentially and verify head owner/repository, bookmark, remote and exact commit after fetch. A same-name stale bookmark is a blocker, not permission to reset it. Branch-only parents are untouched trunks. Preserve confirmed existing topology. Base every new upstack layer on the authoritative immediate parent tip: the verified current remote bookmark, or verified local parent tip when its newest work is not yet pushed. Never fall back to the default base when a parent was named.

Record the original working change, feature bookmark and tip before discovery. Native metadata probes do not move `@`. Preserve recovery bookmarks before rearranging any owned revisions. Validate externally supplied bookmark names before interpolation or use argv-safe calls; never permit shell expansion from a PR name.

When standing preference alone wants a stack but the work is one logical change or only artificial slices are possible, use single-PR mode. An explicit stack request is not refusable on those grounds. Multiple reasonable review boundaries require a concise bottom-to-top proposal and decision; pipeline returns that proposal as a residual.

## Retrospective construction

Inspect the complete original change set against the verified base: existing revisions, tracked/newly tracked and untracked work. Derive the smallest useful independently reviewable linear layers in dependency order, foundation first. Use whole-file groups or existing commit boundaries, never hunk partitioning to force a split. Each layer must work against its parent without upstack dependencies.

Default-bookmark construction with no named parent follows `references/branch-creation.md`, including the local-unpushed-commit decision. Feature construction uses the freshly verified remote base, not the whole original feature tip as bottom parent. A verified materialized fork parent uses its exact commit. Record and preserve the original tip with a recovery bookmark before any rearrangement.

For uncommitted whole-file groups, use path-limited `jj commit` or a verified whole-file `jj split` to form owned layers, inspecting each parent and scope. Excluded/user paths belong to no layer and must remain exactly as found. Do not save, move, restore, commit or overwrite them. If the required operation cannot preserve excluded or ignored/untracked work, stop with a residual. Keep recovery state until the constructed top is proved to contain the complete original change set minus exclusions. Existing coherent committed boundaries can simply receive nonconflicting bookmarks at their verified layer tips. Reuse the original feature bookmark only when its unchanged tip is one of those tips.

Before composing every layer description, read and apply all runtime standards and verbatim source guidance in `references/commit-and-push.md`: full Go guide, several recent backend subjects AND bodies, repository syntax wins, no fixed templates. Describe the layer's semantic content and include an already-known unique unit ID compatibly; do not hunt for a plan.

Unpublished rearrangement requires recovery references and verification of the final diff. Hunk partitioning or published-history rewriting requires explicit approval in interactive mode; pipeline reports the necessary partition/rewrite and confirmation as a residual. Never rewrite published history without explicit confirmation.

## Submit — Step 5 only

Apply the **Project publishing gate** to each exact layer state. Resolve archival first: when teaching archival is on, stop before publication with a residual; do not add an unplanned explainer layer after submit or silently disable archival. The user can rerun with `archive:off`.

Re-query existing PRs, matching owner/repo and bookmark, and verify base/head relationships. Preserve existing drafts unless the user explicitly authorized opening them; never mark someone's WIP ready automatically. Publish only the verified layer bookmarks with `jj git push --remote <verified-remote> --bookmark <layer>` (`--allow-new` for authorized new bookmarks). Create missing PRs with explicit immediate-parent `--base`, verified `--head` and composed title/body file; ordinary full-workflow new PRs are ready unless draft intent says otherwise. Do not create duplicates when PR state is unknown.

Use a supported GitHub-only stack-link route for JJ-managed branches when available, grounding flags in `gh stack link --help`. Verify each explicit PR URL's base/head chain and complete top diff afterward. Missing required linkage is a residual, not successful stack submission. Do not invoke Git-mutating `gh stack submit` as a fallback.

For each PR created in this run, pass its explicit URL into ordinary PR-description composition so PR mode uses that layer's immediate parent and exact head; apply with `gh pr edit <pr-url>`. Existing bodies retain titles, unrelated content and links unless an explicit rewrite or already-authorized factual maintenance applies. Pipeline preserves the conservative optional-no-rewrite default. Declined optional rewrites never block otherwise authorized handoff.

When babysit is on, a draft-only result is a hard residual before handoff. Hand off the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only on explicit land intent, plus stack-wide scope for pipeline submission. Monitoring opt-outs and draft watch boundaries still apply. Step 5 owns submission; earlier steps never publish.

## Landing boundary

Never use `gh pr merge` on a managed stack member. `ce-babysit-pr` or the user owns the supported stack merge path and its explicit final-merge authorization. Missing capability, ambiguity or denied permission stops safely without another harness or Git mutation fallback.

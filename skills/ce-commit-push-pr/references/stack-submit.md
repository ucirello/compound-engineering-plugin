# Opt-in stack construction and submission with native JJ

Load only for explicit stack intent or a standing stack preference. Before ordinary Step 3, perform Probe, Topology and Construction only; Step 5 exclusively owns Submit and newly-created PR descriptions. Run commands from the absolute target workspace root; export `GIT_DIR=$(jj git root)` before repository-scoped gh. No direct Git or Git-mutating gh stack helpers. Read `gh-stack-cli.md` for GitHub-only integration limits.

## Probe

Verify gh authentication, repository stack support and an available GitHub-only stack linking interface from actual command help/API documentation. Do not install tools. If unavailable, explicit stack intent or forced standing preference is a hard residual; soft intent may fall back to one PR with the reason reported. Do not claim independent PRs are a registered stack.

## Topology

Record the original working revision, feature bookmark, complete change set and recovery bookmark before changing topology. Resolve a named parent by PR number where available; verify head repository, author, bookmark and exact head ID. Fetch using JJ from the verified remote and verify that exact revision. A missing/stale/colliding local bookmark is not permission to reset it. A branch-only parent can serve as a verified trunk, not proof of remote stack membership.

Verify any existing stack's actual bottom-to-top topology through GitHub. Preserve it. A named parent must be the immediate parent of the requested new layer; if it is not the top where the remote stack contract requires top-only addition, report a residual rather than silently changing parents. Standalone parent may remain an untouched trunk, or be adopted as the bottom layer only when owned by the current user and authorized. Ambiguous membership, unavailable stack support or uncertain head is a residual.

Use the authoritative parent tip: fetched remote tip when current, otherwise the verified local parent tip if its latest work is still unpublished. Never hardcode origin or default-base a requested upstack layer. Validate caller-supplied names and pass them as literal argv values, never interpolated shell code.

If no explicit stack request and the complete work is one logical change or only artificial slices are possible, use one PR. Explicit requests are not refusable on those grounds.

## Construction

Inspect the complete range plus tracked and untracked working changes, excluding `exclude:<paths>`. Plan the smallest useful linear independently reviewable layers, foundation first, using whole-file groups or existing change boundaries, never forced hunk splitting. One safe topology may proceed under stack authorization. Multiple material alternatives require a bottom-to-top proposal; pipeline mode returns that proposal as a residual. Hunk partitioning or published-history rewrites require explicit approval; pipeline stops rather than rewriting.

On the default bookmark without a named parent, use `branch-creation.md`, including its local-only commit decision. Existing feature work uses the verified fetched base or verified local parent, not the entire original feature tip as the bottom parent. Preserve recovery bookmarks and original work until the top is verified complete.

For committed work already matching the plan, `jj bookmark create <layer-name> -r <verified-layer-tip>` for each layer. Reuse an existing name only if it already names exactly the intended tip. For uncommitted file groups, use JJ's path-scoped commit operations from `commit-and-push.md`, starting from the verified bottom parent, creating each next owned change on its immediate parent. Explicitly name owned paths in each commit; excluded files belong to no layer and must remain unchanged. Stop if a rebase/working-copy transition could overwrite or absorb them or ignored/untracked content. No stash, reset or discard workaround.

Before each layer description, read the full Go guide, compare several complete subjects/bodies at the actual verified history head, and apply `context.md` runtime message standards and source guidance. Compose dynamically; record a known unit ID as semantic content only when applicable, without fixed subject syntax. Preserve human authorship and do not rewrite other people's commits into yours.

Verify every parent edge using JJ, confirm layer coherence and that the top contains the complete original intended change set minus exclusions. Check conflicts and unrelated work before publishing.

## Submit (Step 5 only)

Apply the Project publishing gate to every outgoing layer. If explainer archival is on, stop before submission with the existing residual: no safe stack-aware archival path is defined; do not silently disable it or create post-submit explainer commits.

Re-verify exact repositories, remotes, bookmarks and heads. Push each verified layer bookmark via `jj git push --remote <verified-remote> --bookmark <layer>`; new remote bookmarks require authorized `--allow-new`. Create or reuse each matching PR by explicit owner/head matching, with its immediate parent as base. Do not duplicate a PR on an unknown/nonzero query. Register the intended stack using the verified GitHub-only interface and read back membership/order. Partial failure retains recovery state and reports precisely what published and what did not; never blindly retry create.

Do not mark existing drafts ready unless explicitly authorized. New PRs are ready unless the user/project requests draft. Remaining draft layers are a hard residual before default babysit, never a successfully shipped ready stack.

Map every new PR to explicit URL, head bookmark and immediate parent. Compose its description in PR mode using that URL and apply via `gh pr edit`; never infer it from current `@`. Existing PR bodies remain unchanged except explicitly authorized rewrites or already-authorized factual babysitting refresh. A declined optional rewrite does not block monitoring. Report the bottom open non-draft PR and hand off with `posture:stack-ready`, or `posture:stack-land` only on explicit land intent; pipeline carries stack-wide scope. Do not merge members independently.

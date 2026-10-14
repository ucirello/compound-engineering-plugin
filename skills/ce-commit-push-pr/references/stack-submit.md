# Opt-in JJ stack construction and submission

Load only when explicit intent or standing preference wants a stack. Explicit multi-PR intent is required: do not reinterpret it as a single PR with custom base. If only preference requested it and work is one logical change or artificial slices, use a single PR. Probe capability before changing state; missing required stack support is a hard residual, while soft intent may report it and fall back to single PR.

Read `references/gh-stack-cli.md`. Run all JJ commands from the target absolute root and every repository `gh` call with `GIT_DIR=$(jj git root)` there. All saved work and temporary evidence goes under local `.tmp/`. JJ owns local topology; no Git branch/index or harness workspace bridge.

## Topology (before ordinary Step 3)

Record original revision and bookmark before classification and preserve a recovery bookmark before moving/rebasing anything. Prefer parent PR number when provided; verify head repository/owner, exact head and immediate base. Branch-only parents must resolve to a verified remote or local bookmark. Never classify by name alone. Preserve existing managed topology; a named parent that is not a permissible top produces a residual, not permission to parent elsewhere. Treat unproven membership as unproven, not standalone.

For standalone parents, use the verified exact parent as an untouched trunk; adopt it as a layer only when its author is the current user and adoption is authorized. Resolve fresh remote parent when it contains latest work; if latest parent work is verified local-only, use that exact local tip instead. Never reset a colliding bookmark or hard-code origin. Validate caller names before interpolation, pass arguments safely, and return a residual on unsafe names.

## Retrospective construction

Inspect complete work against the resolved base: existing commits and tracked/untracked working changes, minus all `exclude:<paths>`. Derive the smallest useful linear independent file-level layers, foundation first. Every layer must be coherent without its descendants. One clear topology proceeds under stack authorization; materially different review boundaries require a concise proposal and approval. Pipeline mode returns that proposal as a residual. Hunk partitioning or published-history rewriting requires separate explicit approval; pipeline stops rather than rewriting. Never rewrite published work without confirmation.

On the default bookmark with no named parent, use `branch-creation.md`, including the unpushed-default decision. On an existing feature, fetch and verify its resolved bottom base without importing all feature commits into the bottom. Preserve original revision and recovery bookmark. Keep excluded files exactly where found: never save, move or restore them. If an operation would overwrite them or ignored/untracked content, stop. Preserve all other original work until the final top is verified complete.

For whole-file working changes, commit only each layer's selected paths using `jj commit -- <layer-files>` with a dynamically composed message under the complete runtime-history/Go standards in `commit-and-push.md`. Include known unambiguous U-ID semantic content compatibly with local syntax. Build dependency ancestry with bounded JJ operations on only authorized unpublished revisions; create collision-free feature bookmarks at each planned tip. Existing coherent commit boundaries can be adopted by bookmarking their unchanged tips. Preserve recovery before rearrangement. Verify parent order, each layer diff, and the top's complete original non-excluded change set before publication.

## Submit (Step 5 only)

Apply the Project publishing gate to each exact state. Resolve teaching archival before submitting: if on, stop with a residual rather than create post-submit manager-unaware archival commits or silently disable it. Re-verify push authority, repositories, remotes and bookmarks, then publish each layer using `jj git push --remote <verified-remote> --bookmark <layer>`.

Query matching PRs by head owner/repository and bookmark against the correct base before creating. Failures mean unknown and block duplicate creation. Create each missing PR with its immediate parent as base, using explicit PR URL for subsequent edits. Compose descriptions in PR mode against each exact head and parent; apply via local `.tmp/` body files. Preserve existing titles/bodies unless explicitly requested optional rewrite is approved; authorized babysitting factual refresh remains the no-repeat-approval exception. Pipeline defaults to no optional rewrite.

Preserve all existing draft status unless opening was explicitly authorized. Never use flags that silently open pre-existing drafts. Draft-only submission is a hard residual before default babysitting, not shipped-stack success. Use external JJ stack linkage only after verifying the CLI/repository supports the required topology; report missing management capability rather than claiming unmanaged independent PRs form a verified managed stack.

Step 5 exclusively owns publication and description application. After successful submission, hand off the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only under explicit land intent; pipeline passes stack-wide scope. Report ownership transfer to prevent duplicate bare babysitting. Managed landing is never `gh pr merge`; unresolved manager support stays a needs-human residual.

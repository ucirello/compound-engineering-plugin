# Opt-in JJ stack construction and submission

Enter only for explicit stack intent or standing preference. Explicit multi-PR intent is required; do not reinterpret it as one PR. A standing preference alone does not justify artificial slices. Read `gh-stack-cli.md` and `commit-and-push.md` first.

Before Step 3, probe scoped GitHub access and inspect existing stack topology, JJ revisions/bookmarks, and complete committed plus tracked/untracked work against the verified base. Required unavailable functionality is a hard residual; soft preference may fall back to one PR with disclosure. Never mutate a Git worktree through an extension.

For a named parent, verify its latest authoritative tip after fetch: use its current tracking remote tip or verified local-only tip as appropriate. Do not substitute the default base or assume origin. Preserve parent/source bookmarks. Plan the smallest useful dependency-ordered independently reviewable layers, foundation first. Each must be coherent against its parent. Use whole files or existing commit boundaries, not forced hunk partitioning. One clear safe topology may proceed under shipping intent; materially different choices need a proposal and decision (pipeline: residual). Published-history rewriting always needs explicit confirmation.

Preserve the original tip with a recovery bookmark and record the complete intended change set before topology changes. Excluded paths belong to no layer: never save, move, commit or restore them. Stop if operations would affect excluded, ignored or unrelated work. Use `jj new <verified-parent>` and explicit-path `jj commit` only where working-copy state permits, or JJ revision operations preserving unrelated changes. Compose every message at runtime under `commit-and-push.md`, including known unit identity semantically without fixed syntax. Create one bookmark per verified layer tip. Adopt coherent existing boundaries without rewriting. Verify every parent edge and that the final top contains the complete original intended change set.

## Step 5 exclusively owns submission

Apply the Project publishing gate to every exact layer state and push only verified bookmarks with JJ. Create/update corresponding PRs with scoped `gh`, each based on its immediate parent and matched by exact head repository/owner/bookmark. Preserve existing manager metadata/topology. If required stack registration cannot be performed safely, stop with a concrete residual rather than presenting independent PRs as a managed stack.

Resolve teaching archival before submission. If on, stop with the unsupported stack-archival residual; do not disable it silently or create a post-submit explainer commit. Never mark existing drafts ready without explicit authorization. Draft-only outcomes are hard residuals when babysit is on.

Compose/apply each new PR description using its explicit URL, immediate base and exact head. Existing descriptions remain unless authorized maintenance or explicit apply intent permits refresh; optional rewriting follows `apply-and-handoff.md`. Hand off the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only for explicit landing intent, including stack-wide scope for pipeline submission. Never merge individual managed members with `gh pr merge`.

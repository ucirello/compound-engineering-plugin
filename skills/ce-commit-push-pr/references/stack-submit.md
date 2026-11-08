# Opt-in JJ stack construction and submission

Use only for explicit stack intent or a standing preference. No separate stack package is required. Read `gh-stack-cli.md` for exact parent resolution. Every JJ operation runs from the absolute target workspace root; every repository-scoped `gh` call there uses `GIT_DIR=$(jj git root)`.

## Before Step 3: topology and construction only

Capture original task head, bookmark, complete owned change set and recovery bookmarks before any rewrite. Resolve and fetch the exact default base or user-named parent. Never use default-base creation when the user specified a parent. Resolve fork parents by repository, owner and exact head OID, not name alone; do not reset a colliding bookmark. Preserve existing managed topology and the named parent unchanged. Use the authoritative verified remote parent, or verified local parent when its latest unpublished work is local; never silently choose another layer.

Inspect the entire range plus working changes, including new files. Plan the smallest useful linear independently reviewable layers in dependency order. Do not manufacture artificial slices for a standing preference; an explicit stack request cannot be silently reduced to one PR. With multiple meaningful topologies, ask interactively; pipeline mode returns the proposal as a residual. Hunk-level partitioning or published-history rewrite requires explicit confirmation; pipeline mode stops with that residual. Preserve original recovery bookmarks until complete coverage is verified.

Use existing change boundaries or whole-file `jj split <owned-paths>` to isolate unpublished work, and `jj rebase -r <owned-change> -d <verified-parent>` only when authorized and safe. Create a bookmark at each exact layer tip using `jj bookmark create <layer> -r <tip>`. Do not move other authors' work or excluded paths. `exclude:<paths>` belongs to no layer and remains untouched; a collision involving it blocks construction. Inspect tracked, ignored/untracked content and conflicts before moving changes. No stash, discard or collision deletion.

Before composing each layer description, read and follow the complete standards and verbatim Go source guidance in `commit-and-push.md`: full Go guide, several full recent subjects and bodies at the verified actual history head, repository syntax first. Describe each isolated layer with `(cd "$workspace_root" && jj describe -r <owned-layer> -m "<message composed from the standards above>")`. Include known plan unit IDs as semantic requirements without imposing a fixed prefix. Verify every layer against its immediate parent and the final top against the complete original owned change set.

## Step 5 only: publish and describe

Apply the Project publishing gate to every exact layer state. Resolve archival first; if enabled, stop before publishing with a residual until a stack-safe archival route is explicitly available, never silently disable it or add unplanned commits after submission.

Push only the verified layer bookmarks with `jj git push --remote <verified-head-remote> --bookmark <layer>` from the workspace root. Re-check each PR by base repository, head owner and bookmark before creation. Create bottom-to-top with `gh pr create --head <verified-head> --base <immediate-parent-bookmark> --title <composed-title> --body-file <local-file>`. Preserve existing drafts; never mark them ready without explicit authorization. Explicitly requested drafts remain drafts. A draft-only result is a residual before default babysitting, not successful ready shipment.

Map each new PR URL to its exact bookmark. Pass each URL to ordinary description composition in PR mode so it uses the immediate base/head. Apply through the ordinary body-file path. Existing PRs retain titles/bodies unless explicit rewrite intent or already-authorized factual maintenance applies; pipeline defaults to no optional rewrite. Partial publication is reported with exact URLs and residuals, never retried blindly.

Hand off the bottom open non-draft PR with explicit topology and `posture:stack-ready`, or `posture:stack-land` only with explicit land intent. The callee must support native JJ topology; an unavailable capability is a truthful blocker, not permission to run a Git-backed stack manager. Step 5 alone owns submission; no earlier step publishes.

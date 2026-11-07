# Opt-in native JJ stack construction and submission

Explicit stack intent is required; do not suggest artificial stacks. Before Step 3 probe and plan topology, then construct only. Step 5 exclusively publishes and applies descriptions. Never invoke Git-backed stack helpers or harness dispatch bridges. Run JJ from the absolute workspace root; every repository `gh` call uses `GIT_DIR=$(jj git root)`.

## Probe and topology

Resolve the task's exact base, original tip, bookmarks, all working changes and PR head/base metadata. Missing capabilities or unknown auth/topology are residuals, never guesses. A required stack blocks on these; a soft preference may fall back to single-PR with disclosure. If the request is not explicit and only artificial slices exist, retain one PR.

For a named parent verify PR number, head owner/repository, exact head commit and local bookmark identity. Fetch with native `jj git fetch` from the verified remote; do not overwrite a stale/colliding bookmark. A parent without a PR can serve as an untouched trunk. Adopt someone else's parent PR only with authorization; preserve author/content. Never move to a different top layer merely to make a command succeed. Preserve existing managed topology and authoritative local parent tips not yet pushed. Consult `gh-stack-cli.md` for capability boundaries.

## Construction

Capture the original exact revision and preserve a recovery bookmark before any rewrite. Inspect the complete original change set against the verified base, including committed, tracked, untracked and ignored work. Choose the smallest independently reviewable linear whole-file layers, foundation first. Multiple materially different choices require a decision; pipeline mode returns a proposal as a residual. Hunk partitioning or published-history rewriting requires explicit authorization, never inferred from stack intent.

Use existing boundaries when possible; create a verified feature bookmark per layer with `jj bookmark create <layer-name> -r <exact-layer-tip>`. If splitting unpublished work is necessary, use explicit owned whole-file `jj split <paths>` and verify resulting revisions. Never move, save, restore or include `exclude:<paths>`; stop if construction cannot preserve them exactly. Preserve ignored/untracked content and recovery evidence. Every upstack layer's parent is its immediate verified predecessor, never the default base.

Before describing **every** layer follow `commit-and-push.md`'s full runtime standards: read the complete Go guide and compare several full JJ subjects and bodies. Repository/user syntax wins, including unit IDs only when compatible. Use `jj describe -m "<message composed from the standards above>"`. Preserve human/source credit, no model/harness attribution.

Verify full layer order and that the final top contains exactly the original intended change set minus exclusions before submission. Keep recovery bookmarks.

## Step 5 submission

Apply the Project publishing gate to each exact published state. Resolve archive settings first: requested archival without a safe stack-aware path is a hard residual before publication, never silently disabled. Preserve preexisting drafts; opening them requires explicit authorization. Draft-only outcome blocks default babysit success unless opted out; explicit watch preserves draft boundaries.

Push each verified layer using `jj git push --remote <verified-head-remote> --bookmark <layer>`; an authorized new remote bookmark may use `--allow-new`. Reverify PR presence before each create, matching owner and name; only exit-0 `[]` permits creation. Create each PR against its immediate parent bookmark using explicit `--base`, `--head` and `--body-file`, never an inferred current branch. Unknown or partial submission is a residual; reconcile PRs before retrying, never create duplicates.

For every newly created PR compose from its explicit URL and exact parent/head with the ordinary references, then apply. Existing titles/bodies stay unchanged unless explicitly requested or authorized factual maintenance applies. No stack-specific title syntax.

Report bottom open non-draft PR and complete layer map; transfer stack-wide ownership to `ce-babysit-pr` with `posture:stack-ready`, or `posture:stack-land` only on explicit land intent. No standalone merge. Preserve typed needs-human residuals, bounded retries and recovery evidence; incomplete publication or monitoring ownership is not success.

# Opt-in JJ stack construction and submission

Load only for explicit stack intent or a standing stack preference. Follow `context.md`'s absolute cwd, remote identity and repository-scoped `gh` rules. Configuration remains authoritative. No direct Git invocation or Git-checkout mutation is permitted. Use JJ for local topology and publish each layer through GitHub, preserving stack semantics via the documented external-manager route in `gh-stack-cli.md`.

## Probe and topology (before ordinary Step 3)

Inspect `gh stack --help` and `gh stack link --help` for external JJ-managed stacks, plus existing PR base/head metadata and any available stack view. Distinguish unavailable stack support from simply not belonging to a stack. Missing required stack support is a hard residual for explicit/forced intent; otherwise report it and fall back to single PR. Never silently replace an explicit multi-PR request with a single PR.

When the user named a parent, resolve its exact PR number, head repository, branch and `headRefOid` with `gh pr view`. Fetch the named branch using JJ and verify its commit equals that OID. A branch-only parent must have its remote and exact tip verified directly. Names must match `[A-Za-z0-9._/-]+` before interpolation; pass argv safely. Do not substitute the default base. Parent work not yet pushed may use the verified local parent commit; never blindly choose `origin` or a stale tracking tip.

Preserve confirmed existing topology. If the requested parent is not the top layer, report that conflict instead of silently parenting onto the top. Never adopt another author's standalone PR into a managed stack without authorization; it may remain an untouched trunk. Multiple candidate parents or unproven stack membership are residuals, not guesses. Preserve the original work bookmark and exact tip before topology inspection; no checkout-based classifier may move it.

Without an explicit stack request, one logical change or artificial slices use the single-PR path. An explicit request is not refusable on that ground.

## Retrospective construction

Inspect the complete range plus owned tracked and untracked working changes. Derive the smallest independently reviewable linear layers, foundation first. Use whole-file groups or existing commit boundaries, not forced hunk partitions. A clear safe topology proceeds under stack authorization. Materially different review boundaries require a concise bottom-to-top proposal; pipeline mode reports it as a residual. Hunk-level partitioning or published-history rewrites need explicit interactive approval; pipeline mode stops. Never rewrite published history without it.

If starting on the default bookmark with no named parent, follow `branch-creation.md`, including the unpushed-local-commit decision. Existing feature work uses the exact fetched verified base (or verified local parent), not the entire original feature tip as its bottom parent. Preserve the original tip with a recovery bookmark before any rewrite.

Preserve all working content in JJ changes before rearrangement. Excluded paths belong to no layer and must never be moved, saved, committed or restored by construction; if a required operation cannot preserve them in place, stop. Keep saved owned work until the top is verified complete. Build each layer with native `jj new`, owned-path `jj commit`, and `jj bookmark create`/`set` at its verified commit; each upper layer must have the immediate lower layer as parent. For existing coherent commit boundaries, create bookmarks at those exact tips instead of rewriting. Reuse the original feature bookmark only if its unchanged tip is a planned layer tip.

Every layer message follows the full runtime guide/history comparison in `commit-and-push.md`, without fixed subject syntax. Record a known plan unit's U-ID in repository-compatible syntax only when that layer belongs to it; never hunt for a plan. Verify parent edges, ordered bookmarks and that the final top contains the complete original non-excluded change set before submitting. Preserve human authorship, existing trailers and recovery references.

## Submit — Step 5 exclusively

Apply the Project publishing gate to every exact layer being sent. Resolve archival first: requested teaching archival remains a residual before submission until a manager-aware route exists; do not silently disable it or append explainer commits after submission.

Push each verified layer bookmark with `jj git push --remote <verified-head-remote> --bookmark <layer-bookmark>` (allowing new remote bookmarks only when intended). Recheck PR presence by exact head owner/repository and branch. Create missing PRs bottom-to-top with `gh pr create --base <immediate-parent-branch>` and the composed body file; compose each in explicit PR mode once its URL exists so its exact parent/head range is used. Never select a PR from the incidental current workspace bookmark. Link layers using the verified external-JJ stack route; if unavailable or unverifiable, report stack coverage incomplete rather than claiming success. Do not rerun creation blindly after partial failure.

New PRs are ready unless the user/project requests drafts. Preserve all existing drafts unless explicitly authorized to mark them ready. Draft-only submission is a hard residual before default babysitting. Existing PR titles/bodies remain unchanged unless explicitly requested or authorized babysitting maintenance applies; pipeline mode defaults to no optional rewrite.

Report the bottom open non-draft PR and hand off to `ce-babysit-pr` with `posture:stack-ready` by default, `posture:stack-land` only for explicit land intent, and stack-wide scope for pipeline submission. Never merge a managed member with `gh pr merge`; landing belongs to the stack-aware callee and must preserve the verified topology. Report unsupported landing capability as a blocker, not permission to bypass it.

# Opt-in stack construction and submission

Explicit stack intent is required; never proactively propose stacks or artificial slices. Preserve existing managed topology. Read context.md and gh-stack-cli.md: absolute JJ cwd, scoped gh, no Git executable even inside helpers.

## Before Step 3: topology and construction

Resolve named parent PR metadata through scoped `gh pr view <ref> --json headRefName,headRefOid,author,baseRefName,isDraft`. Verify exact OID, remote and bookmark; fetch with JJ transport when needed. Stale/colliding names and unproven parent classification are residuals, never permission to reset or create a second stack. Preserve original work and recovery bookmarks. A foreign parent remains untouched trunk absent explicit authority.

Inspect the complete original change set against the verified base, including existing commits, tracked and untracked changes. Excluded paths stay untouched and belong to no layer. Plan the smallest coherent independently reviewable linear layers. Materially different topologies, hunk partitioning or published rewrites require a decision; pipeline returns the residual. Explicit intent authorizes safe whole-file local construction, not published history rewrites.

Reuse existing commit boundaries and create a JJ bookmark at each planned tip. For uncommitted groups use explicit whole-file `jj split <paths>` and verify resulting revisions and immediate parents. Read commit-and-push.md fully and apply its runtime full-guide/history composition rules to EACH layer. Use `jj describe -r <layer> -m "<message composed from the standards above>"`, with no fixed subject or suffix. Keep recovery refs until the top contains the complete original change set minus exclusions. Never overwrite ignored/untracked/excluded work to change parents. Named parents determine the bottom base; never substitute the repository default or stale remote for authoritative unpublished local parent work.

## Step 5 only: submit

Apply the Project publishing gate to every exact layer. Requested archival without a manager-aware route blocks before submission rather than silently disabling archival. Require a proven JJ-compatible manager submission route; unavailable support is a compatibility blocker. Do not invoke Git-backed gh stack operations or silently replace required stack intent with unrelated PRs.

The compatible route must publish only verified layer bookmarks, preserve topology and existing draft states, avoid interactive prompts, and return explicit PR URL/head mappings. Never open existing drafts without authority. Draft-only submission is a residual before default babysit, not successful review-ready shipment.

For each NEW PR compose from its explicit URL and exact immediate parent/head and apply through ordinary Step 5. Existing descriptions remain unchanged absent explicit rewrite intent or authorized factual maintenance. Pipeline defaults to no optional rewrite. Step 5 alone submits and hands off the bottom open non-draft PR with posture:stack-ready, or posture:stack-land only on explicit land intent. Final merge is a separate authorized manager action owned by ce-babysit-pr, never an ordinary per-PR merge.

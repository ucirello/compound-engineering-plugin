# PR Description Writing

## Core principle

The diff is already visible on GitHub. Explain what the diff cannot: the newly possible behavior, the corrected behavior, the reason for the change, important design choices, and review risk. Remove sentences that merely inventory files or restate visible edits.

For user-facing defects, establish the observable before-and-after behavior before discussing implementation. Include mechanism only when it helps a reviewer understand correctness or risk.

## Step Pre-A: Resolve the range and base

Two modes exist:

- **Current-stack mode** describes the current JJ feature stack against its resolved base.
- **PR mode** describes a supplied open PR.

For PR mode, fetch metadata first:

```bash
GIT_DIR="$(jj git root)" gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If the PR is not open, report and stop. Use its base and head metadata rather than inferring names.

For current-stack mode, resolve `<base>` in this order: caller-supplied `base:<ref>`, the default returned by `gh repo view --json defaultBranchRef`, then a unique plausible default remote bookmark from `jj bookmark list --all-remotes`. Ask if none or several remain. Resolve `<head>` to the selected feature bookmark when one exists, otherwise to the completed feature tip or `@` while composing before Step 3.

Use `jj git remote list` to resolve remotes. For a same-repository PR, use the remote matching the GitHub repository. For a fork, match the base owner and repository to a configured remote. If no remote matches, use the `gh` fallback rather than comparing against an unrelated remote.

Fetch only at the interoperability boundary, then inspect with JJ:

```bash
jj git fetch --remote <base-remote>
jj log -r '<base>@<base-remote>..<head>'
jj log -r '<base>@<base-remote>..<head>' --no-graph
jj diff --from 'fork_point(<base>@<base-remote> | <head>)' --to '<head>'
```

The second log must expose full descriptions using the repository's configured output or an appropriate JJ template when related-reference discovery needs them. If the range contains no revisions, report that there is nothing to describe and stop.

Use `gh pr diff <ref>` and `gh pr view <ref> --json commits` when local JJ state cannot reach a PR's revisions, including an unmatched fork or server restrictions. Do not invoke a raw Git fetch as a fallback. Mention API fallback use in the summary.

## Step A: Choose detail by review need

Scale the description to behavioral breadth, design novelty, risk, and validation burden. Simple changes may need only a concise explanation; complex changes should emphasize consequential decisions rather than enumerate mechanisms. Performance claims require the available measurements. Keep the shortest body that gives a reviewer the context the diff cannot.

## Step B: Compose the title

Repository-local title syntax from the project's active instructions and conventions and from `git log` ALWAYS wins. Use only a title shape already established in the repository; do not impose a type, scope, casing, length, punctuation, or release marker convention. Describe the change by intent and user or system effect rather than by file operation. Ask before introducing syntax that can trigger release automation.

## Step B1: Resolve related work references

Gather candidate work-item references from the user prompt, caller handoff, bookmark name, full change descriptions, existing PR body, repository PR configuration under `.github/` or `.gitlab/`, plan or debug notes, and visible URLs or IDs already in context. Preserve existing references during rewrites unless the user asks to remove them.

Classify each candidate semantically:

- A closing reference is appropriate only when the PR fully resolves the item and the repository or tracker documents the closing syntax.
- A non-closing reference is appropriate for related, partial, investigative, follow-up, or validation-only work.
- An uncertain reference requires a user question; in non-interactive mode, link neutrally or omit rather than claiming closure.

Repository-local tracker syntax always wins. Do not invent magic words, labels, or placement. Keep non-closing references separate from prose that could imply resolution, and do not repeat an identifier throughout the summary. Use closing automation only when its target-branch and completion semantics are actually satisfied.

## Step B2: Judge new concepts

Run this step only when the gate in `SKILL.md` is on. A concept is teachable only when the PR introduces it to this codebase and it transfers beyond this one implementation.

Gather at most two candidates from the diff. Check each against the base revision, not the working copy, so the new implementation does not count as prior establishment:

```bash
jj file search -r '<base>@<base-remote>' '<candidate term>'
```

Routine use of established patterns, ordinary refactors, renames, dependency maintenance, and project-internal plumbing are not teachable concepts. With API fallback and no local base revision, judge conservatively from the diff.

When a concept qualifies, explain it in plain language, why it fits here, how this change exercises it, and when it would not fit. Choose prose, a Mermaid diagram, a code excerpt, or a comparison table according to the material rather than a fixed template. Keep the section compact and subordinate to the PR's actual review needs.

When rewriting, preserve existing teaching content and archived-document links unless the user's requested focus includes refreshing them. Description-only and description-update modes never archive files.

## Step C: Assemble the body

Use a repository PR template when one exists. Otherwise order content by reviewer need: lead with behavior and motivation, then consequential decisions, related work, validation, teaching content, and supplied evidence as applicable. Omit empty sections and do not impose fixed headings or a universal body structure.

Preserve user-authored evidence blocks unless the requested rewrite includes refreshing them. Include only supplied artifacts and accurately reported validation. Diagrams and tables are useful when they communicate relationships, state transitions, sequences, tradeoffs, or measurements faster than prose; omit them when prose is clearer.

Respect GitHub rendering and automation behavior. Keep issue references unambiguous, and preserve `.github/`, `.gitlab/`, and `.gitignore` names exactly when referring to repository configuration.

End when the review-relevant content ends; append no generated identity footer.

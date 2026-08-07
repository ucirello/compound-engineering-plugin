# PR Description Writing

## Core principle

The GitHub diff already shows file-level mechanics. Explain the outcome, prior limitation, reason for the approach, reviewer-relevant risk, and evidence that the diff cannot establish. Remove narration that merely repeats changed paths or operations.

Use short, direct sentences and one stable term per concept. Preserve technical terms, identifiers, protocols, and error text when they are the review target. Shorten framing rather than removing necessary content.

## Project PR contract

Resolve PR requirements from the project's active instructions and conventions already in context, standard PR-template locations, and contribution guidance those templates reference. Required headings, fields, order, checklists, title rules, disclosure sections, and boilerplate are authoritative. Treat a template as a minimum unless the project requires exact/template-only content or forbids additions.

Project instructions and runtime repository evidence always override this reference. Never add creator, model, harness, generated-by, or similar attribution to user-facing output. If a required project contract demands such attribution, stop and report the conflict rather than inventing or emitting it.

## Pre-A: Resolve range and base

Two modes:

- **Current-bookmark mode:** describe the intended feature bookmark against `trunk()`.
- **PR mode:** describe the explicit PR supplied by the caller.

For PR mode, fetch metadata:

```bash
gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

Stop if the PR is not open. Use its base and head identity rather than the current workspace state.

For current-bookmark mode, resolve the base through `trunk()` and the feature head through its bookmark. If `trunk()` cannot resolve, ask the user after trying `gh repo view --json defaultBranchRef`.

Fetch through Jujutsu and inspect the complete range:

```bash
jj git fetch --remote <base-remote>
jj log -r '<base-bookmark>@<base-remote>..<head-revision>'
jj diff --from '<base-bookmark>@<base-remote>' --to '<head-revision>'
```

For same-repository PRs, `<head-revision>` may be the fetched head bookmark. For forks, match a local remote to the PR's base and head repositories. If the necessary revisions are not locally reachable, use `gh pr diff <ref>` and `gh pr view <ref> --json commits`; note that fallback in the result. If the range has no changes, report that there is nothing to describe and stop.

## Step A: Scope the description

Size content by reviewer decision cost, not changed lines or file types. Build an internal scope map from the complete change list and final base-to-head diff. Use change descriptions for range coverage and the final diff to merge overlap, discard intermediate repair work, and correct stale wording. Classify files by runtime purpose.

The scope map must identify:

- one umbrella outcome;
- each material outcome cluster;
- claims the diff cannot establish;
- decisions, risks, and evidence that affect review.

For a PR inside a known series, also identify the program outcome, this PR's contribution, and known preceding or residual work. Lead at program altitude only when that context is already available from the prompt, plan, existing body, change descriptions, or known sibling work. Never invent a series or scan all open PRs solely to find one.

Use the shortest body that preserves the context, evidence, residual uncertainty, and project-required structure a reviewer needs. A small high-risk change may need more explanation than a large mechanical one. Large changes require selectivity, not a mechanism-by-mechanism transcript. Use a table for measurements or a dense set of comparable decisions when that is clearer than prose.

## Step B: Compose the title

Follow the repository's title rules from project instructions, PR templates, contribution guidance, and observed accepted titles. The title must represent the umbrella outcome rather than one implementation detail. When the PR belongs to a series, represent this PR's contribution without claiming the entire program is complete.

Do not supply a default prefix, type, scope, capitalization, grammatical mood, punctuation rule, or fixed length. Apply only rules supported by the repository. Never add release-impact markers without explicit user confirmation.

## Step B1: Resolve related work

Gather candidate work-item references from the user prompt, caller handoff, bookmark name, complete change descriptions, existing PR body, PR template, plans already in hand, and visible URLs or IDs. Preserve existing references during a rewrite unless removal was requested.

Classify each candidate as closing, non-closing, or uncertain:

- A closing reference is allowed only when this PR fully resolves the item and the tracker/project closing syntax is known.
- A non-closing reference links partial, investigative, follow-up, or otherwise related work without triggering closure.
- An uncertain reference needs a question in interactive mode. In non-interactive mode, use a known neutral link form or omit it; never invent closure.

Use the project's tracker convention when documented. For GitHub Issues, closing keywords trigger workflow actions and should target the default branch only when the PR truly resolves the issue; owner-qualify cross-repository references. For Linear and other trackers, use only syntax known from project instructions or tracker documentation. Put non-closing references in a distinct related sentence or section so prose does not imply closure accidentally.

## Step B2: Judge new concepts

Skip this step when the caller's teaching gate is off. Otherwise identify at most two patterns, techniques, libraries, or domain ideas first introduced by this PR and plausibly unfamiliar to repository readers. Most PRs have none.

Check candidates against the base revision, not the working copy. Use `jj file list -r <base-revision>` to identify relevant base files and `jj file show -r <base-revision> <path>` with the native content-search capability to determine whether the concept is established. Do not use shell pipelines. When local base content is unavailable, judge conservatively from PR diff context.

Teach only concepts that are both new and transferable. Exclude routine refactors, renames, dependency bumps, established patterns, and project-internal plumbing. Explain what each taught concept is, why it fits here, where this PR uses it, and when not to use it. Place that teaching under the repository's project-defined concept section when one exists; otherwise choose a descriptive heading consistent with accepted PRs. Choose prose, a small table, a short code block, or Mermaid according to the material; do not force a fixed heading or mini-template.

Preserve existing concept-teaching content and explainer links on rewrite unless refresh was requested. Description-only and description-update modes never write repository files.

## Step C: Assemble the body

Use the project's required headings and order. When no contract exists, include only material earned by reviewer needs: outcome framing, decisions or risk, related work, validation, known program placement, concept teaching, and supplied evidence. Choose structure from the content and observed accepted PRs rather than imposing a fixed body template or example.

Apply product branding only when the caller's branding gate is on. Preserve existing branding on rewrite unless the user requested its removal, but do not add, remove, or rewrite branding by inference. Branding-only differences do not authorize an API edit.

If a plan already in hand contains session-settled decisions, preserve relevant provenance in the project-permitted location. Do not search for a plan solely to add provenance, and do not turn it into an outstanding-items ledger.

Preserve existing evidence sections unless refresh was requested. Distinguish demonstrated results from assumptions and limitations. Never label test output as a demo or screenshot. Use diagrams or tables only when they reduce decision cost.

Do not add badges, promotional links, creator statements, sign-offs, or other attribution. If a required repository field conflicts with this boundary, report the conflict instead of emitting attribution.

## Step D: Pre-apply coverage audit

Before returning the title and body, verify:

- The title represents the umbrella outcome and follows repository title rules.
- Every material outcome is represented or intentionally omitted as supporting detail.
- Claims not established by the diff are explained, while diff-visible mechanics are not narrated needlessly.
- Known series context is accurate and absent series context was not invented.
- Terms are stable and jargon is retained only where it carries the claim.
- Evidence states an outcome and separates demonstrated facts from assumptions or limitations.
- Closing and non-closing work-item references have the intended tracker effect.
- Every non-required sentence or section changes reviewer understanding or confidence; remove it otherwise.
- No unsolicited attribution or promotional content remains.

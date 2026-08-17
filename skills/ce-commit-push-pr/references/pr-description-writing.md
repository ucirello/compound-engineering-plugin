# PR Description Writing

## Core Principle

The GitHub diff already shows file-level mechanics. Explain the outcome, prior limitation, reason for the approach, reviewer-relevant risk, and evidence that the diff cannot establish. Remove narration that merely repeats changed paths or operations.

Use short, direct sentences and one stable term per concept. Preserve technical terms, identifiers, protocols, and error text when they are the review target. Shorten framing rather than removing necessary content.

## Project PR Contract

Resolve title and body requirements from the project's active instructions and conventions already in context, standard PR-template locations, contribution guidance those templates reference, and accepted PRs visible at runtime. Required headings, fields, order, checklists, title rules, disclosure sections, and boilerplate are authoritative. Treat a template as a minimum unless the project requires exact/template-only content or forbids additions.

Project instructions and runtime repository evidence override this reference. This skill adds no promotional badge, creator statement, generated-by line, model statement, harness statement, sign-off, or other attribution of its own. Fill a project-required field when higher-priority project instructions require it; do not infer one from this skill.

## Pre-A: Resolve Range and Base

Two modes:

- **Current-bookmark mode:** Describe the intended feature bookmark against `trunk()`.
- **PR mode:** Describe the explicit PR supplied by the caller.

For PR mode, fetch metadata with `gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner,headRepository`. Stop if the PR is not open. Use its base and head identity rather than the current workspace state.

For current-bookmark mode, resolve the base through `trunk()` and the feature head through its bookmark. If `trunk()` cannot resolve, ask after trying `gh repo view --json defaultBranchRef` against the explicit repository.

Match the PR base and head repositories to Jujutsu Git remotes. Fetch through `jj git fetch --remote <remote>`. GitHub's PR comparison starts at the merge base, so require `exactly(fork_point(<base-revision>|<head-revision>),1)` to resolve one common ancestor and inspect the complete range with:

```bash
jj log -r 'exactly(fork_point(<base-revision>|<head-revision>),1)..<head-revision>'
jj diff --from 'exactly(fork_point(<base-revision>|<head-revision>),1)' --to '<head-revision>'
```

For same-repository PRs, `<head-revision>` may be the fetched head bookmark. For forks, fetch the head bookmark from its matched remote and verify its Git commit ID against `headRefOid`. If either revision is not locally reachable or the fork point is not exactly one change, use `gh pr diff <ref>` and `gh pr view <ref> --json commits`; disclose that fallback in the result. If the range has no changes, report that there is nothing to describe and stop.

## Step A: Scope and Size the Description

Size content by reviewer decision cost, not changed lines or file types. Build an internal scope map from the complete change list and final base-to-head diff. Use change descriptions for range coverage and the final diff to merge overlap, discard intermediate repair work, and correct stale wording. Classify files by runtime purpose.

The scope map identifies one umbrella outcome, each material outcome cluster, claims the diff cannot establish, and decisions, risks, or evidence that affect review. Derive it from the full range, never only the latest change, tracker title, bookmark name, or original request.

For a PR inside a known series, also identify the program outcome, this PR's contribution, and known preceding or residual work. Use only context already available from the prompt, a plan in hand, the existing body, complete change descriptions, or known sibling work. Never invent a series or scan all open PRs solely to find one.

Use the shortest body that preserves reviewer-needed context, evidence, residual uncertainty, and project-required structure. A small high-risk change may need more explanation than a large mechanical one. Large changes require selectivity rather than a mechanism transcript. Use a table for measurements or dense comparable decisions when clearer than prose.

For medium and large changes, make the body progressively scannable. The opening is one or two sentences carrying one idea: what is now different and the gap or failure it replaces. Put known program placement in a short block immediately after the opening rather than overloading it. Each later section must answer one remaining reviewer question. State deliberately deferred scope once. A reader who stops after the opening must still understand this PR's outcome.

## Step B: Compose the Title

Derive title syntax at runtime from project instructions, PR templates, contribution guidance, and accepted recent PR titles. The title represents the umbrella outcome rather than one implementation detail. For a series, represent this PR's contribution without claiming the entire program is complete.

Do not supply a default prefix, type, scope, capitalization, mood, punctuation rule, or fixed length. Apply only repository-supported rules. Never add release-impact markers without explicit user confirmation.

## Step B1: Resolve Related Work

Gather candidate work-item references from the prompt, caller handoff, bookmark name, complete change descriptions, existing PR body, PR template, plans already in hand, and visible URLs or IDs. Preserve existing references during a rewrite unless removal was requested.

Classify each candidate as closing, non-closing, or uncertain. A closing reference is allowed only when this PR fully resolves the item and the tracker/project closing syntax is known. A non-closing reference links partial, investigative, follow-up, or otherwise related work without triggering closure. An uncertain reference needs a question in interactive mode; in non-interactive mode, use a known neutral link form or omit it. Never invent closure.

Use only tracker syntax established by project instructions, accepted PRs, or official tracker documentation. Keep non-closing references distinct from prose that could imply closure accidentally. Preserve an existing related-work form when rewriting unless it conflicts with current project rules or the user requests a change.

## Step B2: Judge New Concepts

Skip this step when the caller's teaching gate is off. Otherwise identify at most two patterns, techniques, libraries, or domain ideas first introduced by this PR and plausibly unfamiliar to repository readers. Most PRs have none.

Check candidates against the base revision, not the working copy. Use `jj file list -r <base-revision>` to identify relevant base files and `jj file show -r <base-revision> <path>` with the native content-search capability. When local base content is unavailable, judge conservatively from PR diff context.

Teach only concepts that are both new and transferable. Exclude routine refactors, renames, dependency bumps, established patterns, and project-internal plumbing. Explain what each taught concept is, why it fits here, where this PR uses it, and when not to use it. Place teaching under a project-defined concept section when one exists; otherwise choose a descriptive heading consistent with accepted PRs. Choose prose, a small table, a short code block, or Mermaid according to the material; do not force a fixed mini-template.

Preserve existing concept-teaching content and explainer links on rewrite unless refresh was requested. Description-only and description-update modes never write repository files.

## Step C: Assemble the Body

Use the project's required headings and order. When no contract exists, include only material earned by reviewer needs: outcome framing, decisions or risk, related work, validation, known program placement, concept teaching, and supplied evidence. Choose structure from the content and accepted PRs rather than imposing a fixed body template or example.

Place the opening in the project-prescribed section. Without a prescribed structure, use a bare paragraph when there are no sections, or put the opening under a runtime-appropriate summary heading when sections are needed. Do not leave an orphaned opening above the first heading.

If a plan already in hand contains session-settled decisions, preserve relevant provenance in the project-permitted location. Do not search for a plan solely to add provenance, and do not turn it into an outstanding-items ledger.

Preserve existing evidence sections unless refresh was requested. Distinguish demonstrated results from assumptions and limitations. Never label test output as a demo or screenshot. Use diagrams, tables, or navigation hints only when they reduce reviewer decision cost; never substitute a changed-file list for review guidance.

## Step D: Pre-apply Coverage Audit

Before returning the title and body, verify:

- The title represents the umbrella outcome and follows runtime-derived repository title rules.
- The opening carries one idea in one or two sentences and lets a reader understand the outcome without continuing.
- Every material outcome is represented or intentionally omitted as supporting detail.
- Claims not established by the diff are explained, while diff-visible mechanics are not narrated needlessly.
- Known series context is accurate and absent series context was not invented.
- Terms are stable and jargon is retained only where it carries the claim.
- Evidence states an outcome and separates demonstrated facts from assumptions or limitations.
- Closing and non-closing work-item references have the intended tracker effect.
- Every non-required sentence or section changes reviewer understanding or confidence; remove it otherwise.
- No skill-added promotional or attribution content remains.

# PR Description Writing

Read this reference in full for every PR-title or PR-body composition and update. It owns range resolution, sizing, title derivation, related references, concept teaching, body assembly, and the pre-apply audit.

## Core principle

The diff is already visible on GitHub. Explain what the diff cannot show: what became possible, what was fixed, what risk changed, and why a design choice matters. Remove sentences a reviewer can reconstruct directly from the diff.

Lead with user or system effect rather than file operations. For user-facing bugs, establish the observable before and after before explaining mechanism. Mention technical cause only when it helps a reviewer assess correctness or risk.

## Pre-A: Resolve range and base

Two modes are supported:

- **Current-bookmark mode:** describe the explicit head bookmark against the repository's default base bookmark.
- **PR mode:** describe a specific open PR supplied by the caller.

For PR mode, fetch metadata first:

```bash
gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop. Use `baseRefName` as `<base>`, `headRefName` as `<head-bookmark>`, and `headRefOid` to verify the exact head commit.

For current-bookmark mode, resolve `<base>` in this order: caller-supplied `base:<ref>`, `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, then an explicit user answer. Do not guess among common bookmark names. Resolve `<head-revision>` from the explicit head bookmark chosen by `SKILL.md`, not from an assumed current branch.

Use `jj git remote list` to identify the base remote. For fork PRs, match the PR base repository to a configured remote. If none matches, use the `gh` fallback instead of diffing against the fork's push remote.

Fetch and verify local range inputs:

```bash
jj git fetch --remote <base-remote>
jj bookmark list --all-remotes
jj log -r '<base>@<base-remote>..<head-revision>' --no-graph
jj log -r '<base>@<base-remote>..<head-revision>' --no-graph -T 'description ++ "\n"'
jj diff --from '<base>@<base-remote>' --to '<head-revision>'
```

Use the detailed log output for related-reference discovery. Verify the resolved head's commit ID equals `headRefOid` in PR mode. If the change list is empty, report that there are no changes to describe and stop.

Use `gh pr diff <ref>` and `gh pr view <ref> --json commits` when the base or head is unavailable locally, including fork PRs without a matching remote, shallow history, or unrelated local history. Note when this fallback supplied the evidence.

## Step A: Size by decision cost

Size the description by what a reviewer cannot determine from the diff, not line count, extension, or visual surface. First identify the material claims: new capability, repaired behavior, changed risk, migration effect, or design decision. Include only claims the diff cannot establish unaided.

Classify changed files by runtime purpose. Markdown, YAML, and configuration may be executable instructions or production behavior rather than inert documentation.

Reviewer uncertainty may increase coverage, but not justify an essay. Fold risk and residual uncertainty into the narrative unless the PR is large enough to need separate sections. Prefer the shortest description that still lets a reviewer decide with the necessary context and evidence.

Evidence can include tests, benchmarks, API captures, migration or rollback exercises, logs, compatibility checks, security analysis, evaluations, manual probes, and rollout results. Include a result only when it changes confidence in a material claim. Exclude fix-up-only changes from sizing; large PRs need more selectivity, not more narration.

| Change profile | Description approach |
|---|---|
| Simple, low-decision-cost change | One concise value-led paragraph; no headings |
| Focused behavioral correction | Observable before/after, cause when useful, and validation |
| Multi-part feature or refactor | Narrative frame plus the design decisions reviewers must assess |
| Architecturally significant change | Narrative frame, selective decision callouts, and concise validation summary |
| Measured performance change | Include verified before/after measurements in a table |

These are coverage shapes, not fixed sentence counts or length templates.

## Step B: Compose the title dynamically

Derive title syntax from the project's active local instructions and conventions, then from the syntax visible in `git log` and existing repository PRs. Those local sources always win. Do not impose a predetermined prefix, scope, capitalization pattern, punctuation pattern, or fixed length.

The title must accurately identify the shipped value or corrected behavior, remain distinguishable in review lists and release history, and avoid implementation-only wording when behavior is the meaningful change. Classify intent from behavior rather than file extension when the local syntax includes an intent marker.

Never add a release-major marker or equivalent breaking-change signal without explicit user confirmation because such syntax can trigger automation.

If composing or recommending a JJ change description while reconciling the title with history, apply this exact instruction:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active local instructions and conventions win first, and syntax visible in `git log` wins next; compatible Go guidance is only a quality backstop. Use a neutral repository-derived description, never a fixed message form or example.

## Step B1: Resolve related work

Gather candidate work-item references from the user prompt, caller handoff, head bookmark, full change descriptions, existing PR body, PR template, planning or debugging notes, and visible URLs or IDs.

Preserve existing related references when rewriting unless the user asks to remove them. Classify each candidate:

- **Closing:** the PR fully resolves the item and the tracker's closing syntax is known.
- **Non-closing:** related, partial, investigative, follow-up, or validation-only work.
- **Uncertain:** an item clearly exists but its identifier or close intent is missing.

Ask for uncertain references in interactive mode. In non-interactive mode, use a known neutral non-closing form or omit the reference rather than triggering closure. Never invent automation keywords. Keep non-closing references separate from prose that implies resolution, and follow the project's tracker convention when it exists.

For GitHub Issues, use GitHub's documented closing syntax only when the PR targets the default branch and fully resolves the issue; otherwise use a neutral related reference. For Linear or another tracker, use only syntax confirmed by project conventions or current tracker documentation. Mixed closing and non-closing items must remain visibly distinct.

## Step B2: Judge new concepts

Skip this step when the concept-teaching gate in `SKILL.md` is off.

Gather at most two candidates from the resolved diff: a newly introduced transferable pattern, technique, library use, or domain idea. Most PRs have none. Check each candidate against the base revision, not the working copy, because the working copy contains the new concept.

Use JJ's revision-aware file search where available:

```bash
jj file search -r '<base>@<base-remote>' '<candidate-term>'
```

If that command is unavailable, enumerate candidate files with `jj file list -r '<base>@<base-remote>'`, inspect likely files with `jj file show -r '<base>@<base-remote>' <path>`, and search the returned content with the available read/search capability. Do not materialize an OS-global temporary checkout.

A concept is teachable only when it is new to this codebase in this PR and transferable beyond this change. Do not teach established patterns, routine refactors, renames, dependency-only updates, or internal plumbing without a reusable idea. In API-fallback mode, judge from diff context and omit unless novelty is clear.

For each qualifying concept, explain:

1. What it is in plain language.
2. Why it fits here over the obvious alternative.
3. How this PR exercises it.
4. When not to use it.

Use `## New concepts`. Prefer a Mermaid diagram for architecture or flow, a fenced code excerpt for mechanics, and a table for tradeoffs. Lead with the point, then mechanism, then boundary. Preserve an existing concept section and explainer links verbatim during rewrites unless the requested focus requires refreshing them.

When archival is enabled in full workflow, `SKILL.md` writes and publishes the teaching material; description-only and description-update modes never write repository files.

## Step C: Assemble the body

Order the body as follows:

1. Opening value or before/after outcome.
2. Body sections that materially aid a decision.
3. Related references when they need a separate block.
4. Validation when the method or result is not obvious.
5. New concepts when Step B2 produced them.
6. Supplied evidence blocks.

Use `## Summary` only when other second-level headings exist; otherwise use a bare opening paragraph. Do not leave prose orphaned above the first heading.

Preserve existing `## Demo` and `## Screenshots` blocks verbatim unless the user asks to refresh them. Add newly supplied visual evidence under a heading appropriate to its actual type. Never label test output as a demo or screenshot.

Use diagrams or tables when they communicate relationships, state transitions, sequences, tradeoffs, or measured comparisons faster than prose. Prose remains authoritative if a visual and prose disagree. End after the last substantive content or evidence section.

GitHub auto-links issue-like tokens. Use actual work-item syntax only for intentional references and keep unrelated numbered list items free of accidental issue notation.

## Step D: Pre-apply coverage audit

Before returning or applying the body, revise until all answers are satisfactory:

- Are all material claims the diff cannot establish present?
- Did the opening communicate changed capability or behavior rather than file operations?
- For user-visible bugs, is the before/after explicit?
- Are evidence results distinguished from assumptions, unavailable checks, and mixed outcomes?
- Are existing issue references, evidence blocks, concept sections, and user-authored context preserved where required?
- Is every closing action intentional and supported by known tracker semantics?
- Can any sentence or section be removed without lowering reviewer confidence?
- Does the body end after its last substantive content or evidence section?

The finished body is the shortest one that preserves reviewer decision context, verified evidence, related-work semantics, and residual uncertainty.

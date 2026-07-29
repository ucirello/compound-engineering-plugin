# PR Description Writing

## Core principle

The diff is visible on GitHub. Explain what it cannot show: what became possible, what was fixed, what behavior changed, and which decisions or risks matter. Remove sentences a reviewer can reconstruct directly from the diff.

For user-facing bugs, state what users observed before and what they observe now before discussing mechanism. Mention implementation details only when they help reviewers assess risk.

## Project PR-body contract

Resolve requirements from the project's active instructions and conventions, standard repository PR-template locations, and referenced contribution guidance. Required headings, fields, order, checklists, syntax, and boilerplate define the structural contract. Repository-local requirements and recent message style always override compatible general guidance.

Treat a template as a minimum unless the project requires an exact body or forbids additions. If a required identity field cannot be omitted, use `ai:assistant` for protocol data or `AI Assistant` for display text. Add no optional identity metadata.

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-bookmark mode** - describe the current stack against the repository's default base.
- **PR mode** - describe a specific open PR passed by the caller.

For PR mode, fetch metadata first:

```bash
gh pr view -R <repo> <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop. Use `baseRefName` as `<base>`, `headRefName` as `<head-bookmark>`, and `headRefOid` as the exact `<head>` revision.

For current-bookmark mode, resolve `<base>` in this order: caller-supplied `base:<ref>`, `gh repo view -R <repo> --json defaultBranchRef --jq '.defaultBranchRef.name'`, then one unambiguous tracked remote default from `jj bookmark list --all-remotes`. Ask if none resolves. Resolve `<head>` from the feature bookmark at the publishable head; do not substitute an unrelated bookmark.

Use the caller's writable publication `<remote>` for every fetch and remote bookmark reference. In description-only or description-update mode where the caller has not already resolved it, resolve one remote dynamically from `jj git remote list`: the remote matching the PR head repository in PR mode, otherwise the intended writable publication repository. Do not assume its name. For fork PRs, if that remote cannot supply the base bookmark, use the `gh` fallback rather than substituting another remote or diffing against the wrong base.

```bash
jj git fetch --remote <remote>
jj log -r '<base>@<remote>..<head>'
jj log -r '<base>@<remote>..<head>' --no-graph -T 'description ++ "\n"'
jj diff --from '<base>@<remote>' --to '<head>'
```

If no revisions exist in the range, report "No changes to describe" and stop. For a fork, unavailable bookmark, shallow history, or unrelated ancestry, use `gh pr diff -R <repo> <ref>` and `gh pr view -R <repo> <ref> --json commits`; note the fallback in the user-facing summary.

---

## Step A: Size the description

Size by reviewer decision cost, not changed-line count, extension, or visual surface. Build an internal scope map from the complete revision list and final base-to-head diff. Use descriptions for range coverage and the diff to merge overlaps, discard fix-up-only work, and correct stale descriptions. Group material outcomes, identify one umbrella outcome, and list claims the diff alone cannot establish.

Classify files by runtime purpose. Instruction, configuration, generated product content, policy, and deployment files can carry behavioral claims regardless of extension.

Prefer the shortest description that lets a reviewer decide while carrying context, evidence, and residual uncertainty absent from the diff. Project templates set the structural floor.

| Change profile | Description approach |
| --- | --- |
| Small and simple | One or two sentences, without optional headings |
| Small but behaviorally meaningful | A short before/after narrative with only decision-relevant evidence |
| Medium feature or refactor | Narrative frame plus material decisions and risks |
| Large or architecturally significant | Narrative frame, selective decision callouts, and concise validation |
| Performance improvement | Before/after measurements in a markdown table |

Evidence includes benchmarks, API captures, migration or rollback exercises, logs, compatibility checks, security analysis, evaluations, manual probes, and rollout results. Include only evidence that changes confidence in a material claim.

---

## Step B: Compose the title

Derive the title from the scope map's umbrella outcome. Preserve repository-required syntax and limits, but impose no default prefix, type, scope, template, capitalization, punctuation, or fixed format. The project's active instructions and recent local style win over compatible general guidance. Do not add release-triggering markers or automation syntax without explicit user intent.

---

## Step B1: Resolve related work references

Gather candidate work-item references from the user prompt, caller handoff, bookmark name, full change descriptions, existing PR body, PR template, known plan or debug notes, and visible URLs or IDs. Preserve existing references during rewrites unless the user requests removal.

Classify each candidate:

- **Closing** - the PR fully resolves the item and the project's closing syntax is known.
- **Non-closing** - the PR is related, partial, investigative, follow-up, or validation-only, or tracker semantics are unknown.
- **Uncertain** - tracked work is evident but the exact reference or close intent is missing. Ask interactively; in non-interactive flows, omit or use repository-approved non-closing syntax.

Do not invent closing keywords or place a non-closing reference beside language that implies resolution. Keep tracker IDs out of unrelated summary prose. Follow the project's documented tracker syntax; when none exists, use a neutral full URL or identifier without automation words.

---

## Step B2: Judge new concepts

Skip this step when the teaching gate is off. Otherwise inspect the diff for at most two concept-shaped candidates: a newly used library, transferable technique, or domain idea encoded by this change. Most PRs have none.

Check candidates against the base revision, never the working copy:

```bash
jj file search -r '<base>@<remote>' '<term>'
```

A concept is teachable only when it is new to this codebase in this PR and transferable beyond it. Omit established patterns, routine refactors, renames, dependency updates, and project-internal plumbing. In API fallback mode, teach only unmistakably new concepts.

Compose `## New concepts` for at most two concepts. For each, explain what it is, why it fits here, one example from the PR, and when not to use it. Use Mermaid for relationships, code for behavior, and a table for material comparisons. Preserve an existing concept section and explainer links verbatim during rewrites unless the user's focus requests a refresh.

---

## Step C: Assemble the body

Follow the project PR-body contract. When it does not define structure, order content as: opening, earned body sections, related references, non-obvious validation, known session-settled decision provenance, new concepts, then supplied evidence.

Place the opening inside the project's summary location or, when no contract exists, under `## Summary` if any headings are used. Do not leave an orphan paragraph above the first heading.

When a known plan contains `session-settled:` decisions, include one concise sentence naming those decisions and classes. Add conflict context only when the caller flagged it. Do not search for a plan, create an outstanding-items ledger, or update this provenance after opening the PR.

Preserve existing user-supplied evidence sections unless the user requests refresh. Use diagrams or tables only when they convey relationships, state, sequence, trade-offs, or measurements faster than prose. Prose remains authoritative.

Add no optional identity metadata. Use `ai:assistant` or `AI Assistant` only when a required field cannot be omitted.

---

## Step D: Pre-apply coverage audit

Before returning or applying the title and body, revise them until all answers are satisfactory:

- Does the title express the umbrella outcome rather than one implementation detail?
- Is every material outcome represented or intentionally omitted as supporting-only?
- Are claims absent from the diff explained without restating what the diff already proves?
- Is decision-changing evidence reported as an observed result and kept distinct from assumptions or negative outcomes?
- Are required issue references, semantic scope, and repository syntax preserved?
- Can any optional sentence or section be removed without lowering reviewer confidence?
- Is optional identity metadata absent, with the neutral identity used only when a mandatory field required it?

# PR description writing

## Outcome

Explain what the diff cannot: the outcome now possible, the failure now removed, the important design decision, evidence that changes confidence, and known residual scope. Do not narrate file operations a reviewer can read from the diff.

Use short direct sentences and one stable term per concept. Keep technical names when they are the claim or review target. State user-visible before and after before implementation cause when that is what reviewers must assess.

## Project contract

Resolve required PR headings, fields, order, checklists, and boilerplate from the project's active instructions and standard PR-template or contribution locations. That contract wins. Treat it as a minimum unless it explicitly requires exact/template-only content or forbids additions.

Do not add creator identity. For a required neutral actor field use `ai:assistant` as a machine value or `AI Assistant` as prose. Keep any explicitly required model/provider/harness disclosure according to the runtime project contract.

## Resolve range and evidence

PR mode starts with:

```bash
gh pr view <ref> --json baseRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

Require an open PR. Fetch the base bookmark from the named Git remote that represents the PR base, then inspect the exact PR head when it is available in JJ:

```bash
jj git fetch --remote <base-remote> --branch <base>
jj log -r '<base>@<base-remote>..<head>'
jj diff --from '<base>@<base-remote>' --to '<head>'
```

For current-workspace mode, resolve the provider default branch through `gh repo view`, select the matching JJ remote bookmark, and use the feature bookmark target as `<head>`. Never use Git `HEAD` as the JJ head.

For a fork, match the base repository to a named remote URL. If the PR head commit is not present after normal remote fetch, use `gh pr diff <ref>` and `gh pr view <ref> --json commits`; do not diff against a wrong remote. Report API fallback use. If the range contains no changes, report that and stop.

## Build the scope map

Write a compact internal map before composition: umbrella outcome; material outcome clusters and claims; program placement or `none`. Derive it from the complete range log and final diff, not only the latest change, bookmark name, request, or tracker title. Classify files by runtime purpose rather than extension.

When known context places this PR in a larger series, add the program outcome, this PR's contribution, and known prior or residual work. Do not scan unrelated PRs solely to invent series context. The opening states this PR's umbrella outcome; a separate short block may place it in the larger program without repeating the opening.

Size content by reviewer decision cost. Simple work may need one value-led sentence. Higher uncertainty adds only the design choices, evidence, and residual risk needed to decide. Large diffs require more selection, not diff narration. Use a table, diagram, or navigation hint only when it resolves a reviewer question faster than prose.

## Compose the title

Derive title structure from runtime project instructions and recent repository history. Use the scope map's umbrella outcome, keep peer outcomes at parity, and satisfy the host's title limits. Do not impose a fixed prefix, type, scope, capitalization, mood, subject form, or example. Never add release-triggering syntax without explicit user confirmation.

## Related work

Gather candidate work-item references from supplied context, the complete change descriptions, existing body, template, and visible plans or URLs. Preserve existing references on rewrite unless asked to remove them.

Use a closing reference only when the PR fully resolves the item and the tracker's documented closing syntax is known. Otherwise use the project's neutral related-reference convention or a plain full URL. Unknown close semantics never become a guessed workflow action. Keep a non-closing identifier out of outcome prose so it cannot imply closure.

## New concepts

When the teaching gate is on, derive at most two candidate concepts from the diff. A concept qualifies only when it is new relative to the base and transferable beyond this patch. Check the base with JJ's file search or a fileset-scoped repository search; do not inspect the working-copy version as proof of prior presence. Omit established patterns, ordinary refactors, internal plumbing, and uncertain candidates.

For each qualifying concept, explain what it is, why it fits here, how this change uses it, and when not to use it. Preserve an existing `## New concepts` section and explainer links on rewrite unless the requested focus changes them. Description-only and update modes never write repository files.

## Assemble and audit

Honor the project template's structure. Otherwise use an opening, then only sections that answer remaining reviewer questions, related references, validation when useful, supplied planning provenance when already in hand, new concepts, and evidence. Do not append creator identity or product-marketing material.

Before returning, verify that the title and opening express the scope map's umbrella outcome; every material claim is represented or intentionally supporting-only; program context is accurate; evidence states results and limitations; related references have the right semantics; and no sentence merely restates the diff. Remove optional content that does not improve reviewer confidence, while retaining project-required fields.

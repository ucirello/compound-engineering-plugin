# PR Description Writing

## The core principle

The diff is already visible on GitHub. The description exists to explain what the diff cannot show: the newly possible behavior, the corrected behavior, the reason for the change, and the risk reviewers should understand. Remove statements that merely enumerate touched files or restate hunks.

For user-facing bugs, run a before/after pass before describing the mechanism: state what users observed before and what they observe now. Mention technical cause or implementation only when it helps reviewers assess the decision or risk.

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-line mode** - describe the intended feature bookmark or working-copy stack against the repository's default base.
- **PR mode** - describe a specific open PR passed by the caller.

For PR mode, fetch metadata first:

```bash
GIT_DIR="$(jj git root)" gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop. Save `baseRefName` as `<base>` and `headRefName` as `<head-bookmark>`.

For current-line mode, resolve `<base>` in priority order: caller-supplied `base:<ref>`, then `GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, then ask. Never guess a default bookmark. Resolve `<head>` from the exact feature bookmark selected by `SKILL.md`; if it does not exist yet, use the final intended local revision. Do not equate `@` with a current bookmark because JJ has no such concept.

**Remote resolution:** derive repository identities from GitHub URLs and normalize the configured URLs from `jj git remote list`. Require exactly one matching base remote. For a fork PR, independently match the head repository to a configured remote. Zero or multiple matches are ambiguous; use the `gh` fallback rather than diffing against the wrong remote.

```bash
jj git fetch --remote <base-remote> --branch <base>
jj git fetch --remote <head-remote> --branch <head-bookmark>
jj log -r '<base>@<base-remote>..<head>'
jj log -r '<base>@<base-remote>..<head>' --no-graph -T 'commit_id ++ " " ++ description ++ "\n"'
jj diff --from '<base>@<base-remote>' --to '<head>'
```

For a same-repository PR, one fetch can provide both bookmarks. Verify the resolved head commit ID against `headRefOid`. Resolve revsets to exactly one base and head before diffing. If the range is empty, report "No changes to describe" and stop.

**Fallback:** use `GIT_DIR="$(jj git root)" gh pr diff <ref>` and `GIT_DIR="$(jj git root)" gh pr view <ref> --json commits` when no correctly matched local remote can provide the refs, the repository is shallow, the operation is offline, or the histories have no usable local fork point. Keep all remote transport in `jj git`; do not inspect backing-store files or invoke another VCS CLI. Note when the API fallback was used.

---

## Step A: Size the description

Match weight to weight. When in doubt, shorter wins. Discount review-only cleanup and mechanical follow-ups when sizing because they are not separate reader-facing outcomes. Large PRs require greater selectivity, not a larger inventory of implementation details.

| Change profile | Description approach |
|---|---|
| Small and simple | 1-2 sentences, no headings, under about 300 characters. |
| Small but behaviorally meaningful | 3-5 sentences with a user-visible before/after lead and any material risk; no headings unless there are two distinct concerns. |
| Medium change | Narrative frame, then the important decisions and reasons. |
| Large or architectural change | Narrative frame, 3-5 selective decision callouts, and a concise validation summary. Target about 100 lines and cap at 150; use a summary table rather than one H3 per mechanism. |
| Measured improvement | Include the relevant before/after measurements in a markdown table. |

---

## Step B: Compose the title

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At composition time, inspect the repository-local instructions and run `git log`. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. `jj log` may provide supplemental context but never replaces `git log`. Derive the title syntax dynamically. Do not impose a type, scope, prefix, grammatical mood, capitalization rule, fixed length, punctuation rule, template, or example. The title must accurately summarize the user-visible or architectural outcome and remain concise enough to scan. Use `<title>` as the command placeholder.

Never introduce release-signaling syntax unless repository conventions require it and the user explicitly confirms the release effect.

---

## Step B1: Resolve related work references

Before writing the body, gather candidate work-item references from the user prompt, caller handoff, bookmark name, full change descriptions, existing PR body, PR template, plan/debug notes, and visible URLs or IDs already in context. Preserve existing related references when rewriting unless the user asks to remove them.

Classify each candidate as:

- **closing reference** - the PR fully resolves the item and the tracker's closing syntax is known.
- **non-closing reference** - the PR is related, partial, investigative, follow-up, validation-only, or the tracker semantics are unknown.
- **uncertain** - the change clearly came from tracked work but the exact reference or close-vs-link intent is missing. Ask; in non-interactive flows, use known non-closing syntax or omit rather than pretending to close it.

Magic words are workflow actions. Follow the project's documented tracker conventions when present. For GitHub Issues, use GitHub's documented closing syntax only when the PR targets the default bookmark and fully resolves the issue; otherwise use a neutral related reference. For other trackers, never invent closing syntax. Keep a non-closing ID out of prose that could imply resolution.

Do not put a non-closing reference next to close/fix/resolve/address/report wording. State partial behavioral scope separately, then use the exact non-closing form below unless project conventions override it. A non-closing ID appears only in that related-reference sentence or block, never scattered through the opening or summary.

| Tracker | Closing reference | Non-closing reference | Notes |
|---|---|---|---|
| GitHub Issues | `Fixes #123`; cross-repo: `Fixes owner/repo#123` | `Related: #123`; cross-repo: `Related: owner/repo#123` | Closing keywords include close, fix, and resolve variants. Use them only for a PR targeting the default bookmark that fully resolves the issue; repeat the keyword for multiple closing issues. |
| Linear | `Fixes ENG-123` | `Related to ENG-123` | Put magic words in the PR body, not a comment. Multiple issues with the same intent may follow one magic word. |
| Other trackers | Use the project's documented closing syntax only when known. | Prefer a full URL or tracker ID under `Related`. | Follow the documented integration semantics; otherwise never guess a closing action. |

Closing references may live in a tiny opening paragraph. Non-closing references get their own sentence or related-work section before validation and evidence. Separate mixed closing and non-closing items so automation intent is unambiguous.

---

## Step B2: Judge new concepts

Decide whether the change introduces a transferable pattern, technique, library, or domain idea that a reader of this repository would plausibly not know. Skip this step when the concept teaching gate is off.

Gather candidates from the resolved diff first. Most PRs have none. Check each candidate against the base revision, never the working-copy revision, because the latter contains the PR's own changes:

```bash
jj file search -r '<base>@<base-remote>' --pattern '<term>' '<candidate-fileset>'
```

Use an explicit fileset broad enough to test establishment but narrow enough to avoid generated/vendor content. Cap candidates at two. A candidate is teachable only when it is new to this codebase in this PR and transferable beyond it. Omit routine established patterns, ordinary refactors, renames, dependency-only updates, and internal plumbing. In API-fallback mode, judge from diff context and remain conservative.

Compose `## New concepts` for at most two concepts; if more qualify, teach the most load-bearing and name the rest in one sentence. Give each concept about 10-25 lines covering:

1. What it is in plain language.
2. Why it fits here better than the relevant alternative.
3. How this PR exercises it.
4. When not to use it.

Use Mermaid for relationships, a focused code block with a one-line why comment for mechanics, and a pipe-delimited table plus prose verdict for comparisons when those forms communicate faster than prose. Lead with the point, then the mechanism, then the caveat. Never hand-draw box diagrams. The section is additive to Step A's size bounds: a small PR that introduces a load-bearing concept still gets the section. Preserve an existing concepts section and explainer links verbatim on rewrite unless the user's focus asks to refresh them. Description-only and description-update modes never write repository files.

---

## Step C: Assemble the body

Order content by reviewer value: opening, necessary decision/risk sections, related work, non-obvious validation or test plan, concepts when present, then evidence. Add headings only when the body needs sections; when any H2 exists, place the opening under `## Summary` rather than leaving an orphan paragraph above the first heading.

Preserve existing `## Demo`, `## Screenshots`, or `## Evidence` blocks verbatim unless the user asks to refresh them. Put freshly supplied artifacts under the matching heading after concepts and validation. Never label test output as `Demo` or `Screenshots`.

Use diagrams or tables only when they convey relationships, flows, states, sequences, trade-offs, or measured comparisons faster than prose. Skip them for prose-clear changes. Add no attribution, badges, product branding, identity metadata, or model metadata.

**GitHub gotcha:** do not accidentally format ordinary list items as issue references. Use the repository-qualified issue form or full URL when ambiguity exists.

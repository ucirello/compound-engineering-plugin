# PR Description Writing

## The core principle

The diff is already visible on GitHub. The description exists to explain what the diff cannot show: what was impossible before and is now possible, what was broken and is now fixed, what shape changed. Cut any sentence a reader could reconstruct from the diff itself.

- Weak: a file-by-file inventory that merely restates the diff.
- Strong: the user-visible capability or correction, plus the boundary that matters to reviewers.

If the lead sentence describes what was moved, renamed, or added rather than what's now possible or fixed, rewrite it. This applies to every section, not just the opening — restating the diff is the failure mode this skill exists to prevent.

For user-facing bugs, run an extra before/after pass before writing the mechanism: name what the user would have seen before and what they now see instead. Only then mention the technical cause or fix, and only if it helps the reviewer understand risk. A lead like "Playback hooks now ignore late async responses" is still too mechanical if the visible bug was "old videos, thumbnails, or errors could appear after switching selections."

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-bookmark mode** (default) — describe the feature bookmark vs the repo's default base.
- **PR mode** — describe a specific PR. Triggered when the caller passes a PR ref.

For PR mode, fetch metadata first:

```bash
gh pr view <ref> --json baseRefName,headRefName,url,body,state,isCrossRepository,headRepository
```

If `state` is not `OPEN`, report and stop — do not invent a description. Use `baseRefName` as `<base>` and `headRefName` as `<head>`.

For selected-bookmark mode, resolve `<base>` from a caller-supplied `base:<ref>` or `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If neither resolves, ask the user. Resolve `<head>` to the feature bookmark selected by the caller; JJ has no active bookmark, so never infer it from a checked-out branch.

**Remotes:** use `origin` for the base. In selected-bookmark mode, `<head-revision>` is the local `<head>` bookmark. In same-repository PR mode, fetch the head from `origin` and set `<head-revision>` to `<head>@origin`. For fork PRs, match `headRepository` against `jj git remote list`, fetch the head from that remote, and set `<head-revision>` to `<head>@<head-remote>`. If no local remote matches, skip to the `gh` fallback; do not diff against the wrong remote.

```bash
jj git fetch --remote <base-remote> --branch <base>
jj git fetch --remote <head-remote> --branch <head>  # PR mode only
jj log -r '<base>@<base-remote>..<head-revision>'
jj diff --from 'fork_point(<base>@<base-remote> | <head-revision>)' --to '<head-revision>'
```

If the change list is empty, report "No changes to describe" and stop.

**Fallback** — use `gh pr diff <ref>` and `gh pr view <ref> --json commits` when JJ cannot reach the refs, including a fork PR with no matching remote, an offline workspace, or unrelated histories.

Note in the user-facing summary when the API fallback was used.

---

## Step A: Size the description

Match weight to weight. When in doubt, shorter wins. Subtract fix-up changes (review fixes, lint, rebase resolutions) when sizing — they're invisible to the reader. Large PRs need more selectivity, not more content.

| Change profile | Description approach |
|---|---|
| Small + simple (typo, config, dep bump) | 1-2 sentences, no headers. Under ~300 characters. |
| Small + non-trivial (bugfix, behavioral change) | 3-5 sentences. No headers unless two distinct concerns. |
| Medium feature or refactor | Narrative frame, then what changed and why. Call out design decisions. |
| Large or architecturally significant | Narrative frame + 3-5 design-decision callouts + brief test summary. Target ~100 lines, cap ~150. For PRs with many mechanisms, use a Summary table; do not create an H3 per mechanism. |
| Performance improvement | Include before/after measurements as a markdown table. |

For small + simple PRs, the value-led sentence is the entire description.
For small + non-trivial bugfixes, the 3-5 sentence target still needs a user-visible before/after lead when the bug affected UI, CLI output, workflow output, or any other user-observable behavior. Concision is not a reason to skip the visible symptom.

---

## Step B: Compose the title

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Inspect the actual history with `git log -n 10 --format=full`. For every PR-title composition, edit, validation, or recommendation, the project's active repository-local instructions and message syntax observed in actual `git log` output take precedence; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed syntax, prefixes, types, scopes, subjects, bodies, layouts, templates, or examples; use the neutral `<title-composed-from-runtime-conventions>` placeholder when discussing variable content.

---

## Step B1: Resolve related work references

Before writing the body, make an explicit related-reference pass. Gather candidate work-item references from the user prompt, caller handoff, bookmark name, full JJ change descriptions, existing PR body, PR template, plan/debug notes, and visible URLs or IDs already in context. Preserve existing related references when rewriting a PR unless the user asks to remove them.

Classify each candidate as:

- **closing reference** — the PR fully resolves the item and the tracker's closing syntax is known.
- **non-closing reference** — the PR is related, partial, investigative, follow-up, validation-only, or the tracker semantics are unknown.
- **uncertain** — the change clearly came from a tracked bug, incident, performance investigation, alert, or log trace, but the exact ID/link or close-vs-link intent is missing. Ask the user for the reference or intent; in non-interactive flows, use a non-closing reference or omit rather than pretending to close it.

Do not invent a closing keyword. Magic words are workflow actions, not decoration. If the candidate is ambiguous, put a neutral related reference in the related-reference sentence/block or omit it; do not scatter the ID through the summary.

Do not put a non-closing reference next to close/fix/resolve/address/report wording in prose. For partial or related work, write the behavioral scope in one sentence and put the tracker ID separately. Use the table's non-closing reference labels exactly; do not substitute synonyms like `Refs`, `References`, or `Toward` unless the project's documented tracker convention requires one of those labels. For a non-closing reference, the tracker ID appears only in that related-reference sentence or block, never in the summary/opening/body prose. This avoids both accidental automation and reviewer confusion.

- Weak: mixing a non-closing work-item reference into prose that implies closure.
- Strong: state the behavioral boundary separately, then use the project's neutral related-reference syntax.

Common syntax examples:

| Tracker | Closing reference | Non-closing reference | Notes |
|---|---|---|---|
| GitHub Issues | `Fixes #123`; cross-repo: `Fixes owner/repo#123` | `Related: #123`; cross-repo: `Related: owner/repo#123` | Closing keywords are `close(s/d)`, `fix(es/ed)`, and `resolve(s/d)`. Use closing syntax only when the PR targets the default branch and truly resolves the issue; otherwise use a non-closing reference. Repeat the keyword for multiple closing issues. |
| Linear | `Fixes ENG-123` | `Related to ENG-123` | Linear supports closing and non-closing magic words. Put magic words in the PR description, not a PR comment. Multiple issues can follow one magic word when they share the same intent, e.g. `Fixes ENG-123, DES-5 and ENG-256`. |
| Other trackers | Use the project's documented closing keyword only when known. | Prefer a full URL or tracker ID under `Related`. | Some trackers parse commit messages, PR descriptions, or both. Follow project docs or tracker integration docs when present; otherwise never guess a closing action. |

Closing references can live in the opening paragraph when the body is tiny. Non-closing references always get their own sentence or `## Related` block before validation/evidence. For one item that truly closes, a single line like `Fixes ENG-123.` can be enough; for mixed items, separate closing and non-closing bullets.

---

## Step B2: Judge new concepts

Decide whether the change introduces a concept — a pattern, technique, library, or domain idea — that a reader of this repo would plausibly not know. Skip this step entirely when the skill's concept teaching gate is off (SKILL.md Step 4).

**Gather candidates from the diff first.** Read the Pre-A diff for concept-shaped novelty: a dependency put to first real use, a technique the diff visibly introduces (debouncing, optimistic locking, infinite scroll, a state machine), or a domain idea the code now encodes. Most PRs surface no candidate — stop here and compose no section; absence is the common case, and this path costs zero extra tool calls.

**Check each candidate against the base ref, never the working copy.** The working copy contains this PR's own code, so searching it finds the concept you just added and wrongly concludes it is already established. Check the base instead (Pre-A already resolved it):

```bash
jj file search -r '<base>@<base-remote>' '<term>'
```

Run one call per candidate — candidates cap at two, so the cost is trivial — and read establishment from the output: empty output means the concept is absent from the base.

A candidate is teachable only when it is both new to this codebase in this PR and transferable beyond it. Never teach: routine use of an already-established repo pattern, ordinary refactors, renames, dependency bumps, or project-internal plumbing with no transferable idea. When in doubt, omit — a missing section costs little; a patronizing one trains readers to skip the feature.

In the `gh`-fallback path (fork PR, no local base refs), judge from diff context alone and lean conservative: compose the section only when the concept is unmistakably new.

- Bad: teaching "dependency injection" because a PR added one constructor argument in a codebase full of DI.
- Good: teaching infinite scroll on the PR that replaces pagination with it for the first time.

**Compose the section** under the heading `## New concepts` (Step C places it) for at most 2 concepts — when more qualify, teach the most load-bearing and name the rest in one sentence. Per concept, ~10-25 lines covering:

1. **What it is** — the concept in plain words, no jargon dependency.
2. **Why here** — why it was chosen over the obvious alternative this PR could have used.
3. **One example from this PR** — how the shipped behavior exercises the concept.
4. **When not to use it** — one sentence on the boundary.

Format by material:

| Material | Show |
|----------|------|
| Architecture, relationships, boundaries | Fenced `mermaid` block (`flowchart TB`) |
| Code behavior, a diff's mechanics | Fenced code block with a one-line *why* comment above |
| A comparison or trade-off | Pipe-delimited table, prose verdict underneath |

Lead with the point, then the mechanism, then the caveat. Dense is good; long is not. Never hand-draw box-drawing/ASCII diagrams — mermaid or prose. The section is additive to Step A's sizing: a small PR that introduces a heavy concept still gets the section, and the section never counts against the base description's size rows.

**Rewrite preservation:** when rewriting an existing PR body, preserve an existing `## New concepts` section and any explainer-doc link verbatim (same rule as `## Demo`) unless the user's focus asks to refresh the concepts. Description-only and description-update runs never write repo files.

**Archival hook:** when the skill's Step 5 confirms the apply and `pr_teaching_archive` is on (full workflow only), the teaching content is also written to `docs/explainers/` and linked from the section — the describe-and-push transition and doc frontmatter live in SKILL.md Step 5.

---

## Step C: Assemble the body

In order: opening → body sections that earn their keep → related references when they need their own block → test plan if non-obvious → New concepts section when Step B2 produced one → evidence block if one exists.

The opening goes under `## Summary` if the body uses any `##` headings; bare paragraph otherwise. No orphaned opening paragraphs above the first heading.

**Evidence handling:** preserve any existing `## Demo` or `## Screenshots` block verbatim unless the user's focus asks to refresh it. If the caller passed a freshly captured URL or path, splice as `## Demo`. Otherwise omit. Never label test output as "Demo" or "Screenshots."

**Visual aids:** reach for a diagram or table when it conveys the change faster than prose — relationships, flows, state transitions, sequences, trade-offs, before/after data, or any structure prose would have to enumerate. Mermaid and markdown tables cover most shapes; don't be limited to a particular type if a different one fits the change better. Place inline at the point of relevance. Skip for simple, prose-clear, or rename/dep-bump changes. Prose is authoritative when it conflicts with a visual.

**GitHub gotchas:** never prefix list items with `#` (GitHub auto-links `#1` as an issue ref). Use `org/repo#123` or full URL for actual references.

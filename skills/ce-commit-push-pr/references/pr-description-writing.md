# PR Description Writing

## The core principle

The diff is already visible on GitHub. The description exists to explain what the diff cannot show: what was impossible before and is now possible, what was broken and is now fixed, what shape changed. Cut any sentence a reader could reconstruct from the diff itself.

- Bad: "Adds a helper, updates the workflow to call it, and changes two test files."
- Good: "Evidence capture now decides automatically whether a change has observable behavior. CLI tools and libraries are now eligible alongside web UIs."

If the lead sentence describes what was moved, renamed, or added rather than what's now possible or fixed, rewrite it. This applies to every section, not just the opening — restating the diff is the failure mode this skill exists to prevent.

For user-facing bugs, run an extra before/after pass before writing the mechanism: name what the user would have seen before and what they now see instead. Only then mention the technical cause or fix, and only if it helps the reviewer understand risk. A lead like "Playback hooks now ignore late async responses" is still too mechanical if the visible bug was "old videos, thumbnails, or errors could appear after switching selections."

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-bookmark mode** (default) — describe `@` vs the repo's default base.
- **PR mode** — describe a specific PR. Triggered when the caller passes a PR ref.

For PR mode, fetch metadata first:

```bash
gh pr view <ref> --json baseRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop — do not invent a description. Use `baseRefName` as `<base>` and `headRefOid` as `<head>`.

For current-bookmark mode, resolve `<base>` in priority order: caller-supplied (`base:<ref>`) → `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` → exact `main`/`master`/`develop` remote bookmarks visible in `jj bookmark list --remote origin`. If none resolve, ask the user. `<head>` is `@`.

**Base remote:** `origin` for current-bookmark mode and same-repo PRs. For fork PRs, match the PR's base owner/repo against `jj git remote list`. If no local remote matches, skip to the `gh` fallback — do not diff against `origin` (wrong base).

```bash
jj git fetch --remote <base-remote>
jj log -r '<base>@<base-remote>..<head>' --no-graph
jj log -r '<base>@<base-remote>..<head>' --no-graph -T 'description ++ "\n"'   # full descriptions for related-reference discovery
jj diff -r '<base>@<base-remote>..<head>'
```

If the revision list is empty, report "No revisions to describe" and stop.

**Fallback** — use `gh pr diff <ref>` and `gh pr view <ref> --json commits` when JJ cannot reach the refs (fork PR with no matching remote, shallow clone, offline, or unrelated histories).

Note in the user-facing summary when the API fallback was used.

---

## Step A: Size the description

Match weight to weight. When in doubt, shorter wins. Subtract fix-up commits (review fixes, lint, rebase resolutions) when sizing — they're invisible to the reader. Large PRs need more selectivity, not more content.

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

At runtime, inspect the repository's active local instructions and conventions, including scoped instructions governing the changed files, then run the repository-preferred `git log` command and inspect its recent messages. If no invocation is prescribed, inspect at least the 10 most recent messages with `git log`. Those sources win; apply the remaining Go guidance only where compatible.

Treat the PR title as the commit-message first line: make it a short summary of the change. When repository convention permits, prefix it with the primary affected package or component followed by a colon; after the colon, use a lowercase verb phrase that completes "this change modifies the project to ...", with no trailing period. Keep it as short as practical and preferably under 72 characters. The PR body is Markdown and is not the commit-message body, so commit-body wrapping and Markdown restrictions do not apply to it. Follow the project's known tracker convention and never guess closing semantics. Do not add `Signed-off-by` or attribution lines. Validate the completed title against these rules and the repository evidence. Do not use or prescribe fixed messages, prefixes, types, scopes, subjects, bodies, templates, placeholders, or examples, including Conventional Commit examples. Never add release-triggering syntax without explicit user confirmation.

---

## Step B1: Resolve related work references

Before writing the body, make an explicit related-reference pass. Gather candidate work-item references from the user prompt, caller handoff, bookmark name, full change descriptions, existing PR body, PR template, plan/debug notes, and visible URLs or IDs already in context. Preserve existing related references when rewriting a PR unless the user asks to remove them.

Classify each candidate as:

- **closing reference** — the PR fully resolves the item and the tracker's closing syntax is known.
- **non-closing reference** — the PR is related, partial, investigative, follow-up, validation-only, or the tracker semantics are unknown.
- **uncertain** — the change clearly came from a tracked bug, incident, performance investigation, alert, or log trace, but the exact ID/link or close-vs-link intent is missing. Ask the user for the reference or intent; in non-interactive flows, use a non-closing reference or omit rather than pretending to close it.

Do not invent a closing keyword. Magic words are workflow actions, not decoration. If the candidate is ambiguous, put a neutral related reference in the related-reference sentence/block or omit it; do not scatter the ID through the summary.

Do not put a non-closing reference next to close/fix/resolve/address/report wording in prose. For partial or related work, write the behavioral scope in one sentence and put the tracker ID separately. Use the table's non-closing reference labels exactly; do not substitute synonyms like `Refs`, `References`, or `Toward` unless the project's documented tracker convention requires one of those labels. For a non-closing reference, the tracker ID appears only in that related-reference sentence or block, never in the summary/opening/body prose. This avoids both accidental automation and reviewer confusion.

- Bad: "closing one corruption path from #123"
- Bad: "partial fix for #123"
- Bad: "This addresses the retry-related corruption path reported in #123."
- Good: "This covers the duplicate-row retry path; concurrent cancellation remains follow-up work."
- Good: "Related: #123"

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
jj file search -r '<base>@<base-remote>' --pattern '<term>'
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

**Rewrite preservation:** when rewriting an existing PR body, preserve existing third-party content, an existing `## New concepts` section, and any explainer-doc link verbatim (same rule as `## Demo`) unless the user's focus asks to refresh that content. Description-only and description-update runs never write repo files. Never generate model, harness, agent, or other attribution.

**Archival hook:** when the skill's Step 5 confirms the apply and `pr_teaching_archive` is on (full workflow only), the teaching content is also written to `docs/explainers/` and linked from the section — the commit-and-push transition and doc frontmatter live in SKILL.md Step 5.

---

## Step C: Assemble the body

In order: opening → body sections that earn their keep → related references when they need their own block → test plan if non-obvious → New concepts section when Step B2 produced one → evidence block if one exists.

The opening goes under `## Summary` if the body uses any `##` headings; bare paragraph otherwise. No orphaned opening paragraphs above the first heading.

**Evidence handling:** preserve any existing `## Demo` or `## Screenshots` block verbatim unless the user's focus asks to refresh it. If the caller passed a freshly captured URL or path, splice as `## Demo`. Otherwise omit. Never label test output as "Demo" or "Screenshots."

**Visual aids:** reach for a diagram or table when it conveys the change faster than prose — relationships, flows, state transitions, sequences, trade-offs, before/after data, or any structure prose would have to enumerate. Mermaid and markdown tables cover most shapes; don't be limited to a particular type if a different one fits the change better. Place inline at the point of relevance. Skip for simple, prose-clear, or rename/dep-bump changes. Prose is authoritative when it conflicts with a visual.

**GitHub gotchas:** never prefix list items with `#` (GitHub auto-links `#1` as an issue ref). Use `org/repo#123` or full URL for actual references.

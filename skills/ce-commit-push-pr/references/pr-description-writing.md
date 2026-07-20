# PR Description Writing

## The core principle

The diff is already visible on GitHub. Explain what it cannot show: what was impossible before and is now possible, what was broken and is now fixed, and what behavior or contract changed. Cut sentences a reader can reconstruct from the diff.

For user-facing bugs, state the visible before/after before explaining mechanism. Mention technical cause only when it helps reviewers understand risk.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-stack mode** - describe the intended feature bookmark or stack head against the repository's default remote bookmark.
- **PR mode** - describe a specific PR passed by the caller.

For PR mode:

```bash
gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop. Use `baseRefName` as `<base>`, `headRefName` as `<bookmark>`, and `headRefOid` only to verify the fetched head.

For current-stack mode, resolve `<base>` from caller input, project-local instructions, or `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. Resolve `<head>` from the intended feature bookmark; if it does not yet exist in a description-only flow, use the explicit stack head selected from `jj log`. Ask rather than guessing when either side is ambiguous.

Resolve `<base-remote>` and `<head-remote>` from `jj git remote list`, project-local remote conventions, and PR ownership. Same-repository PRs commonly use one remote; fork PRs may not. Fetch with JJ:

```bash
jj git fetch --remote <base-remote>
jj git fetch --remote <head-remote>
jj bookmark list --all-remotes <base> <bookmark>
```

If `<head>` resolves locally, inspect the PR range and merge-base diff:

```bash
jj log --no-graph -r '<base>@<base-remote>..<head>'
jj log --no-graph -r '<base>@<base-remote>..<head>' -T 'description ++ "\n"'
jj diff --from 'fork_point(<base>@<base-remote> | <head>)' --to '<head>'
```

If the range is empty, report "No changes to describe" and stop. If a fork head, commit ID, shallow import, or unrelated history cannot be resolved in JJ, use `gh pr diff <ref>` and `gh pr view <ref> --json commits`. Note the API fallback in the summary.

---

## Step A: Size the description

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

Match weight to weight and prefer the shortest description that preserves the review-relevant behavior, motivation, risk, and validation. Discount review corrections and mechanical cleanup when sizing. Simple changes may need only the outcome; behavioral changes need the visible before/after; architectural changes need the decisions and reasons that affect review; performance claims need measured comparison. Derive length and organization from the change and runtime project conventions rather than prescribed counts or sections.

---

## Step B: Compose the title

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example. The title must communicate the outcome or corrected behavior and use release-signaling syntax only when the user confirms it and the repository uses it for that purpose.

## Step B1: Resolve related work references

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

Gather candidate references from the user prompt, caller handoff, bookmark name, full JJ change descriptions, existing PR body, PR template, plan/debug notes, and visible URLs or IDs. Preserve existing references when rewriting unless asked to remove them.

Classify each candidate:

- **Closing reference** - the PR fully resolves the item and the tracker's closing syntax is known.
- **Non-closing reference** - related, partial, investigative, follow-up, or validation-only work.
- **Uncertain** - tracked work is evident but the exact reference or intent is missing. Ask; non-interactively, use a non-closing reference or omit it.

Do not invent closing keywords. Keep non-closing IDs out of summary prose and place them in a separate related sentence or block.

| Tracker | Closing reference | Non-closing reference | Notes |
|---|---|---|---|
| GitHub Issues | `Fixes #123` | `Related: #123` | Close only when targeting the default bookmark and fully resolving the issue. |
| Linear | `Fixes ENG-123` | `Related to ENG-123` | Put recognized automation syntax in the PR body, not a comment. |
| Other trackers | Use documented project syntax only. | Prefer a full URL or ID under `Related`. | Never guess automation semantics. |

## Step B2: Judge new concepts

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

Skip entirely when the teaching gate is off. Gather at most two concept candidates from the diff: a newly used technique, dependency, pattern, or domain idea. Most PRs have none.

Check candidates against the base revision, not the working copy:

```bash
jj file list -r '<base>@<base-remote>'
jj file show -r '<base>@<base-remote>' . | rg -n --fixed-strings -- '<term>'
```

A concept is teachable only when new to this codebase in this PR and transferable beyond it. Do not teach routine local patterns, renames, dependency bumps, ordinary refactors, or internal plumbing. In API-fallback mode, judge from diff context and be conservative.

Compose `## New concepts` for at most two concepts. Explain what each concept is, why it fits here, how this PR applies it, and when not to use it. Use Mermaid for relationships, a fenced snippet for mechanics, or a table for trade-offs only when that medium improves understanding. Preserve an existing concept section and explainer link verbatim unless asked to refresh them. Description-only and description-update modes never write repository files.

---

## Step C: Assemble the body

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

Include an outcome-led opening, only body sections that earn their keep, related references, non-obvious validation, New concepts when present, and supplied evidence. Arrange them according to active project instructions, runtime conventions, and the needs of the change. Add no generated-by footer or execution metadata. Preserve human and research attribution when it is substantively relevant and already supplied.

Preserve existing `## Demo` and `## Screenshots` blocks unless asked to refresh them. Never label test output as a demo or screenshot.

Use diagrams or tables only when they communicate relationships, flow, state, sequence, trade-offs, or measurements faster than prose. Prose remains authoritative. Never prefix ordinary list items with `#`, which GitHub may interpret as issue references.

## Step D: Validate

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example. Validate that the title communicates the outcome, the body leads with outcome or visible before/after, diff narration is omitted, required references and meaningful human/research attribution are preserved, generated-by metadata is absent, and validation claims reflect work actually performed.

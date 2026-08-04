# PR Description Writing

## Core principle

The diff is already visible on GitHub. Explain what it cannot show: what was impossible before and is now possible, what was broken and is now fixed, and what behavior or contract changed. Remove sentences a reviewer can reconstruct from the diff.

For user-facing defects, state the visible before and after before explaining mechanism. Mention technical cause only when it helps reviewers understand risk.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and message conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-stack mode** - describe the intended feature bookmark or explicit stack head against the default remote bookmark.
- **PR mode** - describe the PR ref supplied by the caller.

For PR mode, fetch metadata first:

```bash
gh pr view <ref> --json baseRefName,headRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop. Use `baseRefName` as `<base>`, `headRefName` as `<bookmark>`, and `headRefOid` only to verify the fetched head.

For current-stack mode, resolve `<base>` from caller input, the project's active instructions and conventions, or `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. Resolve `<head>` from the intended feature bookmark; in a description-only flow with no bookmark, select an explicit stack head from `jj log`. Ask rather than guessing when either side is ambiguous.

Resolve `<base-remote>` and `<head-remote>` from project conventions, `jj git remote list`, and PR ownership. A fork may require different remotes. Fetch each required remote with JJ, avoiding duplicate calls when they are the same:

```bash
jj git fetch --remote <base-remote>
jj git fetch --remote <head-remote>
jj bookmark list --all-remotes <base> <bookmark>
```

Resolve `<head>` to the local feature bookmark or the appropriate `<bookmark>@<head-remote>`, verified against `headRefOid` in PR mode. Inspect the range, full descriptions, and merge-base diff:

```bash
jj log --no-graph -r '<base>@<base-remote>..<head>'
jj log --no-graph -r '<base>@<base-remote>..<head>' -T 'description ++ "\n"'
jj diff --from 'fork_point(<base>@<base-remote> | <head>)' --to '<head>'
```

If the range is empty, report "No changes to describe" and stop. If a fork head, commit ID, shallow import, or unrelated history cannot be resolved in JJ, use `gh pr diff <ref>` and `gh pr view <ref> --json commits`. Note this API fallback in the user-facing summary.

---

## Step A: Size and organize the description

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and message conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Match detail to review needs and prefer the shortest description that preserves behavior, motivation, risk, and validation. Discount review corrections and mechanical cleanup. Simple changes may need only the outcome; observable defects need visible before and after; architectural changes need consequential decisions and reasons; performance claims need measured comparisons.

## Step B: Compose the title

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and PR-title conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Communicate the outcome or corrected behavior. Use release-signaling syntax only when the user confirms it and the repository uses it for that purpose.

## Step B1: Resolve related work references

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and reference conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

Gather candidate references from the user prompt, caller handoff, bookmark name, full JJ descriptions, existing PR body, PR template, planning or debugging notes, and visible URLs or IDs. Preserve existing references when rewriting unless asked to remove them.

Classify each candidate:

- **Closing reference** - the PR fully resolves the item and the tracker's closing syntax is known.
- **Non-closing reference** - the work is related, partial, investigative, follow-up, or validation-only.
- **Uncertain** - tracked work is evident but the exact reference or intent is missing. Ask; non-interactively, use a non-closing reference or omit it.

Do not invent automation keywords. Keep non-closing IDs out of outcome prose and place them in a separate related sentence or section. Follow documented project or tracker syntax. For GitHub Issues, use a closing reference only when the PR targets the default bookmark and fully resolves the issue. Preserve mixed closing and non-closing intent explicitly.

## Step B2: Judge new concepts

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and body conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

Skip this step when the teaching gate is off. Gather at most two candidates from the diff: a newly used technique, dependency, pattern, or domain idea. Most PRs have none.

Check each candidate against the base revision, never the working copy:

```bash
jj file search -r '<base>@<base-remote>' -p 'substring:<term>'
```

A concept is teachable only when it is new to this codebase in this PR and transferable beyond it. Do not teach routine local patterns, renames, dependency bumps, ordinary refactors, or internal plumbing. In API-fallback mode, judge from diff context and be conservative.

When concepts qualify, compose `## New concepts` for at most two. Explain what each is, why it fits here, how this PR applies it, and when not to use it. Use Mermaid for relationships, a fenced snippet for mechanics, or a table for trade-offs only when that medium improves understanding. Preserve an existing concept section and explainer link verbatim unless asked to refresh them. Description-only and description-update modes never write repository files.

## Step C: Assemble the body

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and body conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Preserve the semantic requirements to communicate the outcome, related references, non-obvious validation, new concepts when present, and supplied evidence while adapting syntax to runtime conventions. Add no promotional footer, execution metadata, or standalone product decoration.

Preserve existing demo and screenshot sections unless asked to refresh them. Never label test output as a demo or screenshot. Use diagrams or tables only when they communicate relationships, flow, state, sequence, trade-offs, or measurements faster than prose. Prose remains authoritative. Never prefix ordinary list items with `#`, which GitHub may interpret as issue references.

## Step D: Validate

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and message conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Validate the semantic requirements: the title communicates outcome, the body communicates outcome or visible before and after, diff narration is absent, references preserve their intended automation semantics, evidence and validation claims reflect work actually performed, and promotional or execution metadata is absent.

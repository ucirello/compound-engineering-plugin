---
name: ce-commit-push-pr
description: Commit with JJ, push through `jj git` interoperability, and open or update a GitHub PR. Use when asked to ship/open a PR or only write, rewrite, or apply a PR description.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

Produce a pushed JJ change stack and the correct GitHub PR, or only a PR description when requested. Preserve existing PR state, avoid duplicate PRs, and leave every mutation tied to an explicit bookmark.

**Asking the user:** Use the harness's blocking-question capability. Fall back to chat only when no blocking capability exists or it errors. Never silently skip a required question.

## Mode

- **Description-only**: compose and print only the title and body. If a PR ref was supplied, use it to resolve the comparison range. Apply nothing unless asked.
- **Description update**: require a confirmed open PR, compose against that PR, preview, and apply with `gh pr edit`. Exit-zero `[]` means no open PR; a non-zero query means unknown and requires resolving authentication or connectivity.
- **Full workflow**: run Steps 1-5.

`mode:pipeline` suppresses blocking questions. It does not rewrite an existing PR unless description-update mode itself requested that mutation. If base, head, or PR identity remains ambiguous, stop rather than guess.

## Context

Run each command as its own shell tool call, in order. Do not join commands with shell operators, pipes, substitutions, or redirects. Non-zero status is state to interpret.

| Command | Purpose | Failure meaning |
| --- | --- | --- |
| `jj workspace root` | Repository root | Not a JJ repository; report and stop |
| `jj status` | Working-copy and conflict state | Repository cannot be read |
| `jj diff` | Current content changes | No output means no current content change |
| `jj bookmark list --all-remotes` | Local and remote bookmark state | Bookmark state unavailable |
| `jj log -r 'remote_bookmarks()..@' --no-graph` | Local stack not represented remotely | Empty output may mean nothing to push |
| `jj log -r '::@' --limit 10 --no-graph` | Recent local descriptions | No prior JJ history |
| `git log -10 --format=%B` | Repository commit and PR-title syntax | No compatible history |
| `jj git remote list` | Interoperability remotes and URLs | No configured remote |
| `gh repo view --json nameWithOwner,defaultBranchRef,url` | Base repository and default bookmark | Authentication, connectivity, or forge resolution failed |

The `git log` call is read-only interoperability required for local message conventions; all VCS mutation uses JJ. Determine the candidate head bookmark from an explicit argument, the existing PR, or bookmarks pointing to the pushed stack head. Never infer a current bookmark: JJ bookmarks do not follow the working copy automatically.

When a candidate bookmark is known, query:

```bash
gh pr list --head <bookmark> --state open --json number,url,title,body,state,headRefName,headRepositoryOwner
```

Pass the bookmark name only. On forks, target the base repository explicitly when default resolution points at the fork. Exit-zero `[]` means no open PR; non-zero means unknown. If multiple forks use the same bookmark name, match both head owner and `headRefName`; stop on unresolved ambiguity.

## Step 1: Resolve base, head bookmark, and PR state

**You MUST read `references/bookmark-creation.md` in full for every full workflow.** Apply its decision flow when the work starts from the default bookmark or must be based on a freshly fetched default remote bookmark; otherwise use its bookmark-safety rules to verify the already selected head. The reference determines or validates `<base-revision>` and `<head-bookmark>`; do not substitute an improvised workflow.

Use the default bookmark reported by `gh`; confirm its remote counterpart exists in `jj bookmark list --all-remotes`. Do not silently fall back to a guessed default.

JJ has no active-branch requirement. Route by bookmark state:

- **Existing open PR**: use its exact head bookmark and owner. Confirm the corresponding local or remote bookmark identifies the intended stack head.
- **New PR with work**: derive a non-conflicting bookmark name from the change's purpose, but do not create it until the stack head is known after Step 3.
- **Default bookmark only with no work beyond it**: report that there is no feature work and stop.
- **Ambiguous bookmark or fork ownership**: ask in interactive mode; stop in pipeline mode.

If `jj status` reports conflicts, resolve them before committing or pushing. Jujutsu records conflicts as first-class state: use `jj resolve` or edit materialized conflicts, then verify `jj status`. Never push unresolved conflicts to a GitHub PR.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active local instructions and conventions win first; syntax and style visible in `git log` win next; compatible Go guidance is only a quality backstop. Do not impose fixed prefixes, type lists, scopes, capitalization, punctuation, or body templates without local evidence. Derive PR-title style from the same local sources and existing PRs where available.

## Step 3: Commit and push

Run `jj git fetch` for the relevant remotes before deciding stack ancestry. If the working copy is based on stale local state, compare it with the default remote bookmark. Do not rewrite or discard local changes. When ancestry must be updated, use a JJ operation appropriate to the repository's policy and inspect resulting first-class conflicts before continuing; stop for a semantic conflict that requires product intent.

Scan changed paths for clearly independent file-level concerns. Keep one change when separation is ambiguous. Do not use interactive splitting unless explicitly requested.

At every JJ change-description composition or edit in this step, apply:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Project-local instructions and `git log` syntax win over compatible Go guidance. Use neutral repository-derived descriptions, not a fixed message form. Finish each group with `jj commit`, using filesets for file-level groups and `--message-file <workspace-local-message-file>` when a multiline message is needed. Store that file under `$(jj workspace root)/.tmp/ce-commit-push-pr/`; if no JJ repository exists, use the local fallback `.tmp/ce-commit-push-pr/`.

Validate each completed change before pushing:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Inspect `jj show -r <revision>` and correct an inaccurate or nonconforming description with `jj describe -r <revision>`; project-local instructions and `git log` syntax remain authoritative.

Set the head bookmark to the actual stack head, normally `@-` after the final `jj commit`:

```bash
jj bookmark set <head-bookmark> -r <stack-head-revision>
```

For an existing tracked bookmark, push it explicitly. For a new bookmark, explicitly allow creation on the intended push remote. Use the repository-configured push remote when present; otherwise resolve the correct fork or remote from `jj git remote list` rather than assuming.

```bash
jj git push --remote <push-remote> --bookmark exact:<head-bookmark>
```

Selecting the exact new bookmark explicitly authorizes publishing that bookmark without sweeping in others. Re-read bookmark and remote state immediately before pushing. Never push a stale remembered name, an unresolved bookmark conflict, or unrelated bookmarks.

If no local content or stack change exists and the bookmark is already synchronized, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md` in full** and follow its range resolution, sizing, title derivation, related-reference, concept-teaching, preservation, assembly, and coverage-audit rules. This reference is required in every mode that composes or updates a PR title or body; do not use a fallback summary workflow.

**Evidence decision:** Treat evidence as supplied context or validation prose. Incorporate supplied artifacts without inventing or uploading them. If evidence was explicitly requested but not supplied, ask for it. For behavior a reviewer must verify, include what was actually exercised and the result; state plainly when credentials, infrastructure, hardware, or setup prevented a run. Do not block PR creation solely because no visual artifact exists.

**Concept teaching gate:** Read the repository-local plugin configuration when present. Only active, non-commented keys count. `pr_teaching_section: false` disables concept handling; missing or other values keep it on. `pr_teaching_archive: true` enables archival; otherwise archival is off. `archive:on|off` overrides this run. Preserve any concept-section mechanics available in the installed reference.

Audit the composed title and body against the actual resolved range, existing PR body, issue references, evidence, and local PR conventions before returning or applying it.

## Step 5: Apply and report

- **Description-only**: print the title and body; stop unless application was requested.
- **New PR**: immediately rerun the exact open-PR query for the head bookmark. Resolve non-zero status before proceeding. If a matching PR appeared, switch to the existing-PR path; otherwise create with `gh pr create` and report its URL.
- **Existing PR in full workflow**: report the URL and ask whether to rewrite the description. Pipeline mode defaults to no rewrite.
- **Description update or confirmed rewrite**: preview title, opening summary, and body length. Apply with `gh pr edit` after confirmation; description-update pipeline mode applies directly.

**Explainer archival:** Only in full workflow when archival is enabled, a concept section exists, and PR-body application is confirmed. Resolve paths from the repository root. Check whether each target path is ignored using JJ's tracked-file and status view; if policy cannot be established without a non-JJ ignore query, skip archival with a warning rather than forcing the file. Write one file per concept under `docs/explainers/`, then finish those files as one JJ change.

At the archival change-description composition and validation site, apply:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Project-local instructions and `git log` syntax win over compatible Go guidance. Compose a neutral repository-derived description that accurately identifies the archived material, finish only those files with `jj commit`, validate with `jj show -r @-`, move the head bookmark to `@-`, and push it with `jj git push --bookmark exact:<head-bookmark> --remote <push-remote>`. If nothing changed, retain the existing link. Build host-correct links with `gh browse`; never hardcode a public host. If writing, committing, or pushing archival fails, warn and continue without the link.

When a body applied by this run contains a concept section, report the concept names. In interactive full workflow, offer the functional `ce-explain` route.

**Babysit handoff, default on:** After a new PR or newly pushed changes to an existing PR in interactive full workflow, invoke `ce-babysit-pr` automatically unless `babysit:off` was passed or active `auto_babysit: false` appears in the repository-local plugin configuration. Explicit `babysit:continuous` or `babysit:checkpoint` selects the mode. Do not auto-invoke for pipeline, description-only, description-update, no applied PR change, a non-GitHub forge, or a head bookmark the user cannot push. Fork PRs remain eligible when the user controls the fork head.

## Applying via gh

Write the body under the repository-local temp namespace and pass it with `--body-file`; never depend on stdin or an OS-global temp path. Create `$(jj workspace root)/.tmp/ce-commit-push-pr/` with the available file capability and write the composed body verbatim to a unique file there. If no JJ repository exists, use the local fallback `.tmp/ce-commit-push-pr/`.

```bash
gh pr create --title "<composed-title>" --body-file <workspace-local-body-file>
gh pr edit <pr-ref> --title "<composed-title>" --body-file <workspace-local-body-file>
```

Remove the repository-local body file after the `gh` call succeeds or fails. Preserve the directory for concurrent runs.

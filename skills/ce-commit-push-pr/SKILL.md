---
name: ce-commit-push-pr
description: Describe changes, create or update a JJ bookmark, push it, and open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

**Asking the user:** When this skill says "ask the user", use the provider's blocking question capability. Fall back to chat only when no blocking capability exists or the call errors. Never silently skip the question.

## Mode

- **Description-only** - the user wants only a description, including when they paste a PR URL or number alone. Run Step 4 and print the result. Apply only if asked. Pass a supplied PR ref to Step 4.
- **Description update** - the user wants to rewrite an existing PR description without changing or pushing revisions. If no open PR exists, report and stop. Otherwise run Step 4 in PR mode, then Step 5 to preview, confirm, and apply with `gh pr edit`.
- **Full workflow** - otherwise run Steps 1-5 in order.

**`mode:pipeline` modifier** - run the resolved mode non-interactively and suppress blocking questions. Do not rewrite an existing PR in full-workflow mode unless explicitly requested. In description-update mode, apply directly. For other suppressed decisions, preserve the current stack; if a base, remote, or push bookmark cannot be resolved safely, stop and report rather than guessing.

## JJ semantics

- Most JJ commands snapshot working-copy files into `@` before evaluating repository state.
- A bookmark is a named pointer and is not automatically attached to the working copy. Determine attachment from revisions and bookmarks; never infer a current bookmark.
- Filesets select content from the working-copy change. Unselected content remains in a new working-copy change.
- `jj commit` describes the selected content and creates a new empty change on top. The completed change is commonly `@-`, but always verify it.
- Use JJ for working-copy, history, workspace, bookmark, and remote state. Keep `gh` for GitHub metadata and PR operations. If `gh` cannot discover a non-colocated repository, pass `--repo <owner/name>` resolved from the selected JJ remote URL.

## Context

Gather context at runtime with separate tool calls so expected failures remain visible and portable:

```bash
jj status
jj diff
jj bookmark list -r '@ | @-'
jj log --no-graph -n 10
jj git root
git --git-dir <resolved-git-root> log -n 10 --format=full
jj git remote list
jj workspace root
```

Treat a failed `jj workspace root` as no JJ repository and stop every mode that requires repository state; description-only PR mode may continue through the GitHub API.

---

## Step 1: Resolve bookmark, remote, base, and PR state

If the caller supplied a PR ref, resolve it first with `gh pr view <ref> --json url,title,body,state,headRefName,baseRefName,headRepository,headRepositoryOwner,isCrossRepository`. Otherwise, do not ask `gh` to infer a head from backing-repository state. After identifying a candidate feature bookmark from JJ, resolve the GitHub base repository from the base remote and the head owner from the publication remote, then discover its open PR with `gh pr list --repo <base-owner/base-repo> --head <head-owner>:<bookmark> --state open --json url,title,body,state,headRefName,baseRefName,headRepository,headRepositoryOwner,isCrossRepository --limit 1`. If multiple candidate bookmarks or ownership-matched remotes exist, inspect each or ask which is intended. An empty result means no open PR was discovered; a non-zero result means PR state is unknown and must be resolved before creating a PR.

Resolve the publication remote from the project's active instructions and conventions, JJ configuration, `jj git remote list`, and GitHub head ownership. Do not assume `origin` when another publication remote is configured. Resolve the base remote and GitHub base repository separately from the publication remote; a fork PR uses the upstream repository as the base and the fork owner as the head owner. Resolve the default base bookmark from active project conventions, a resolved PR's `baseRefName`, or `gh repo view --repo <base-owner/base-repo> --json defaultBranchRef --jq '.defaultBranchRef.name'`. Confirm `<base>@<base-remote>` with `jj bookmark list --all-remotes <base>`. Ask if a required value or ownership-matched writable remote remains ambiguous; in pipeline mode, stop and report.

Inspect local bookmark attachment with `jj bookmark list -r '@ | @-'`, inspect the relevant named remote bookmarks with `jj bookmark list --all-remotes <base> <bookmark>`, and inspect `jj log -r '<base>@<base-remote>..@'`:

- **No feature work** - `@` has no diff and the range contains no change intended for a PR. Report and stop.
- **Existing feature bookmark** - a non-base local bookmark identifies the intended stack head, or an open PR supplies `headRefName`. Keep it.
- **No feature bookmark** - derive a non-conflicting bookmark name from the change, but create it only after Step 3 identifies the final stack head.
- **Working copy based on or pointed to by the default bookmark** - never move or publish the default bookmark. Read `references/branch-creation.md` and follow its bookmark-separation flow.

Record an open PR's URL, bookmark, base, and body. Step 4 uses them as range and preservation context; Step 5 routes between create and edit.

## Step 2: Determine description conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and message conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Infer change-description and PR-title conventions independently.

## Step 3: Describe changes, place a bookmark, and push

If the working copy is based directly on the default bookmark, or the local and remote default bookmarks differ, read `references/branch-creation.md` before continuing.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and change-description conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Describe why the change exists and its user or system effect when that context is not evident from the diff.

Scan `jj diff` for naturally distinct concerns. If they clearly form separate logical changes, create at most 2-3 changes. Select file-level groups with JJ filesets such as explicit paths or `glob:"path/**"`. Use `jj split` for line-level separation only when it materially improves reviewability. Prefer one change when separation is ambiguous.

JJ snapshots new non-ignored files under its configured policy. Before recording content, inspect `jj status`; exclude secrets, generated output, and unrelated files from filesets. If an intended file is absent because snapshot configuration leaves it untracked, use `jj file track <fileset>` deliberately.

Record each selected group with the description composed from runtime conventions:

```bash
jj commit -m "<runtime-derived-description>" <fileset>...
```

For an already-separated revision whose description alone needs correction:

```bash
jj describe -m "<runtime-derived-description>" <revision>
```

After each operation, inspect `jj status`, `jj diff`, and the relevant stack with `jj log`. Do not record an empty working-copy change. Resolve the final non-empty stack head explicitly.

Create a new feature bookmark at that head, or move the existing feature bookmark there. Use only the command matching observed state:

```bash
jj bookmark create <bookmark> -r <stack-head>
jj bookmark move <bookmark> --to <stack-head>
```

Never move the default bookmark. Fetch immediately before publication so the remote-bookmark lease is current, inspect conflicts, and push only the intended bookmark:

```bash
jj git fetch --remote <remote>
jj git push --remote <remote> --bookmark <bookmark>
```

If publication reports remote movement or bookmark conflict, fetch again and show `jj status`, `jj bookmark list --all-remotes <bookmark>`, and the relevant `jj log`; then stop for explicit resolution. Never force or broaden the push. The first successful push establishes remote tracking. If the working-copy change is empty and the local and remote bookmark targets already match, this step is a no-op.

## Step 4: Compose the PR title and body

**Read `references/pr-description-writing.md` in full.** Pass any PR ref identified during mode dispatch. When rewriting an open PR, pass its URL so PR mode preserves existing related references and evidence.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.

Repository-local instructions and message conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

Before composition, decide evidence handling:

1. If the user supplied a URL, markdown embed, or local artifact path for inclusion, incorporate it under a heading appropriate to the artifact. Do not invent or upload evidence.
2. If the user requested evidence but supplied none, ask for the URL, markdown, or path, or ask them to return after using their provider's capture flow. Do not dispatch another `ce-*` skill.
3. If you authored the changes and know they are non-observable, skip evidence handling without asking.

For observable behavior, include a concise validation note stating what was actually exercised and observed. If validation was blocked by credentials, services, deployment-only infrastructure, hardware, or local setup, say so plainly. Do not block a PR solely because no visual artifact exists, and never label test output as a demo or screenshot.

Resolve the workspace root with `jj workspace root` and read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file reader. Only active, non-commented keys count. `pr_teaching_section:` is off only when exactly `false`; missing data and other values mean on. `pr_teaching_archive:` is on only when exactly `true`. A per-run `archive:on|off` token overrides archival for this invocation.

- Gate **on** - judge novelty and compose per Step B2 of the reference.
- Gate **off** - skip concept judgment, section, trailer, offer, and archival.

Continue through all composition and validation steps in the reference.

## Step 5: Apply and report

- **Description-only** - print the title and body. Stop unless asked to apply.
- **New PR** - immediately re-check for an ownership-matched open PR, then create against the resolved base repository with `gh pr create --repo <base-owner/base-repo> --head <head-owner>:<bookmark>` so a fork's ownership and the pushed JJ bookmark are explicit. If the re-check fails, resolve authentication or connectivity before creating. Report the URL.
- **Existing PR in full workflow** - the published bookmark updates the PR. Report the URL, then ask whether to rewrite the description. If yes, run Step 4 if needed, preview, and apply.
- **Description update or confirmed rewrite** - preview the title and a concise body summary. Ask whether to apply. If declined, accept focus text for regeneration. If confirmed, use `gh pr edit` and report the URL.

**Explainer archival** runs only in full workflow when archival is on, the body contains `## New concepts`, and application is confirmed. Resolve every path from the JJ workspace root. With two concepts, write one file per concept and record both in one JJ change immediately before the `gh` call:

1. Resolve the configured artifact root from `docs_root` in `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; the first non-empty value wins, and unset means `docs`. Require a repo-relative directory whose resolved path remains inside the workspace and is neither the workspace root nor under its backing metadata directory.
2. Write each file under `<root>/explainers/` with the project's expected frontmatter and the teaching content. Overwrite a file from a prior run.
3. Run `jj file track <root>/explainers/YYYY-MM-DD-<concept-slug>.md`. If JJ rejects an ignored path, remove only the just-written archival file, warn, and skip archival. Never include ignored files forcibly.
4. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
5. Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions.
6. Repository-local instructions and change-description conventions inferred from `git log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.
7. Record only the explainer files with `jj commit -m "<runtime-derived-description>" <root>/explainers/<file>...`, move the feature bookmark to the resulting non-empty head, and publish only that bookmark with `jj git push --remote <remote> --bookmark <bookmark>`. If there is no diff, keep the existing link and continue.
8. Add a head-bookmark blob URL for each document to `## New concepts` before applying the PR body.

If writing, tracking, recording, moving the bookmark, or publishing fails, warn and continue to PR creation without the link. Do not strand the flow between a successful publication and PR creation.

**User-runnable invocation rendering:** default to `/ce-explain <name>` and use `$ce-explain <name>` only when the active provider explicitly documents dollar-prefixed skill invocation. Render one form only.

When a body applied by this run contains `## New concepts`, print `New concepts: <name>[, <name>]` after the PR URL. In interactive full-workflow runs, follow with one rendered `ce-explain` invocation for each concept. Print no trailer if this run applied no body or no PR exists.

**Babysit handoff:** in interactive full workflow, after creating a non-draft PR or publishing new changes to an existing non-draft PR whose head bookmark is writable, invoke `ce-babysit-pr` on that PR through the active provider's skill mechanism. `babysit:off` skips it; `babysit:continuous` and `babysit:checkpoint` force the corresponding watch mode, including for a draft. An active `auto_babysit: false` in `<workspace-root>/.rocketclaw/config.local.yaml` is a standing opt-out unless a force token is present. Do not invoke it in pipeline, description-only, or description-update mode, when no PR changed, or when the head is not writable. Do not reproduce babysitting mechanics locally.

---

## Applying via gh

Write the body to a collision-safe file under `$(jj workspace root)/.tmp`; if there is no JJ repository, use local `./.tmp`. Never use a system or global temporary directory, stdin, a heredoc directly into `gh`, or command substitution for the body content.

```bash
WORKSPACE_ROOT=$(jj workspace root 2>/dev/null)
BODY_DIR="${WORKSPACE_ROOT:+$WORKSPACE_ROOT/}.tmp"
mkdir -p "$BODY_DIR"
while :; do
  BODY_FILE="$BODY_DIR/pr-body.$(date +%Y%m%d%H%M%S).$$.$RANDOM.md"
  (set -C; : > "$BODY_FILE") 2>/dev/null && break
done
cat >> "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel prevents expansion. Substitute the title with shell-safe quoting. Remove the body file whether `gh` succeeds or fails.

```bash
gh pr create --repo <base-owner/base-repo> --head <head-owner>:<bookmark> --title "<title>" --body-file "$BODY_FILE"
gh pr edit <pr-ref> --title "<title>" --body-file "$BODY_FILE"
rm -f "$BODY_FILE"
```

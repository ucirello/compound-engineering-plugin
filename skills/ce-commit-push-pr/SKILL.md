---
name: ce-commit-push-pr
description: Describe changes, create or update a JJ bookmark, push it, and open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# JJ Commit, Push, and PR

**Required actor:** `ai:assistant` (AI Assistant). Preserve provider, human, and research attribution supplied by the project or user. Add no generated-by footer or execution metadata.

**Asking the user:** When this skill says "ask the user", use the provider's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the provider or the call errors (e.g., Codex edit modes). Never silently skip the question.

## Mode

- **Description-only** - user wants just a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** - user wants to refresh/rewrite an existing PR's description with no commit/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** - otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** - set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current stack; if Pre-A cannot resolve a base or push bookmark, stop and report rather than guess).

## JJ semantics

- JJ snapshots working-copy changes into `@` at the start of nearly every command.
- A bookmark is a named pointer. Determine attachment from revisions and bookmarks; never infer a current bookmark.
- Use filesets to select paths for a change. Unselected paths remain in the working-copy change.
- A normal `jj commit` describes the selected content and creates a new empty working-copy change on top. After that, the committed head is usually `@-`; verify rather than assuming.
- Use JJ for repository state and Git interoperability. Retain `gh` only for GitHub metadata and PR operations. In a non-colocated repo, run `gh` with `GIT_DIR="$(jj git root)"` if it cannot discover the backing repository.

## Context

**On platforms without pre-populated command sections**, run the Context fallback below. **Where the labeled sections are pre-populated**, use them directly.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Bookmarks at the working copy and parent:**
!`jj bookmark list --all-remotes -r '@ | @-'`

**Recent changes:**
!`jj log --no-graph -n 10`

**Remotes:**
!`jj git remote list`

**Existing PR check:**
!`gh pr view --json url,title,body,state,headRefName,baseRefName 2>/dev/null || echo 'NO_OPEN_PR'`

**Workspace root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

Run these as separate commands so failures remain visible:

```bash
jj status
jj diff
jj bookmark list --all-remotes -r '@ | @-'
jj log --no-graph -n 10
jj git remote list
gh pr view --json url,title,body,state,headRefName,baseRefName 2>/dev/null || echo 'NO_OPEN_PR'
jj workspace root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark, remote, base, and PR state

Resolve the Git push remote from project-local instructions, then JJ configuration and `jj git remote list`. Do not assume `origin` when the repository names another push remote. Resolve the default base bookmark from project-local instructions, an existing PR's `baseRefName`, or `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. Confirm that `<base>@<remote>` exists with `jj bookmark list --all-remotes <base>`. If any required value remains ambiguous, ask; in pipeline mode, stop and report.

Inspect `jj bookmark list --all-remotes -r '@ | @-'` and `jj log -r '<base>@<remote>..@'`:

- **No feature work** - `@` has no diff and the range contains no change intended for a PR. Report and stop.
- **Existing feature bookmark** - a non-base local bookmark identifies the intended stack head or an open PR supplies `headRefName`. Keep that bookmark and continue.
- **No feature bookmark** - continue without creating one yet. Derive a non-conflicting bookmark name from the change, but create it only after Step 3 has identified the final stack head.
- **Working copy directly bookmarked as the default base** - do not rewrite or push the default bookmark. Read `references/branch-creation.md` and follow its separation flow before continuing.

Note an open PR's URL and body. Step 5 routes between create and edit; Step 4 uses the existing body as preservation context.

## Step 2: Determine description conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example. Infer PR-title and change-description conventions independently at runtime.

## Step 3: Describe changes, create or move a bookmark, and push

If the working copy is based directly on the default bookmark, or local and remote default bookmarks differ, read `references/branch-creation.md` before continuing.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

Scan the working-copy diff for naturally distinct concerns. If they clearly group into separate logical changes, create 2-3 changes at most. Use filesets, including `file1 file2` or `glob:"path/**"`, to select each group. When lines in one file belong to different concerns, use `jj split` only when that separation materially improves reviewability. When ambiguous, one change is fine.

JJ auto-tracks new non-ignored files under its configured snapshot policy. Before committing, inspect `jj status` and exclude secrets, generated output, and unrelated files from the filesets. If a needed new file is not tracked because of repository snapshot configuration, use `jj file track <fileset>` deliberately.

Describe and finish each selected group with a neutral message placeholder:

```bash
jj commit -m "<description-composed-from-runtime-conventions>" <fileset>...
```

For an already-separated change that only lacks or needs a corrected description:

```bash
jj describe -m "<description-composed-from-runtime-conventions>" <revision>
```

After each operation, re-read `jj status`, `jj diff`, and the relevant stack with `jj log`. Do not accidentally commit the empty working-copy change. Resolve the final non-empty stack head explicitly; it is commonly `@-` after `jj commit`, but may be `@` after `jj describe`.

Create the derived bookmark at the final head, or move the existing feature bookmark there:

```bash
jj bookmark create <bookmark> -r <stack-head>
jj bookmark move <bookmark> --to <stack-head>
```

Use only the command matching the observed state. Never move the default bookmark as part of this workflow. Fetch immediately before pushing so JJ's remote-bookmark lease is current, inspect any bookmark conflict, then push only the intended bookmark:

```bash
jj git fetch --remote <remote>
jj git push --remote <remote> --bookmark <bookmark>
```

If the push reports a remote movement or bookmark conflict, fetch again, show `jj status`, `jj bookmark list --all-remotes <bookmark>`, and the relevant `jj log`, then stop for an explicit resolution. Do not force or broaden the push. A successful first push automatically establishes remote tracking. If the working-copy change is empty and the bookmark already matches `<bookmark>@<remote>`, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md` in full.** The core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch. If Step 1 found an existing PR, pass its URL when rewriting so PR mode fetches the existing body and preserves related references.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.

**Evidence decision** before composition. Evidence is user-supplied context or validation prose, not a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) - incorporate it as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User asks to include evidence but has not supplied it** - ask for the URL/markdown/path, or tell them to use their provider's capture flow and return with the artifact. Do not launch another ce-* skill.
3. **Agent judgment on authored changes** - if you authored the changes and know they are non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the stack diff changes observable behavior, include a concise validation note describing what was exercised and how it behaved. If no real run was possible, say why plainly. Do not block PR creation solely because no visual artifact exists, and do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved workspace root (if empty or literal, resolve it with `jj workspace root`) and read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only an active, non-commented `pr_teaching_section:` key counts. The gate is off only when its active value is exactly `false`; missing data or any other value means on. `pr_teaching_archive:` is on only when exactly `true`; a per-run `archive:on|off` token overrides it.

- Gate **on** - judge concept novelty and compose the section per Step B2 of the reference.
- Gate **off** - skip concept judgment, section, trailer, offer, and archival.

Continue through Steps A-D of the reference.

## Step 5: Apply and report

**Description-only mode** - print the title and body. Stop unless the user asks to apply.

**New PR** - apply via `gh pr create` as described below and report the URL. Pass `--head <bookmark>` when `gh` cannot infer JJ's pushed bookmark.

**Existing PR in full workflow** - the pushed bookmark updates the PR. Report the URL, then ask whether to rewrite the description. If no, stop. If yes, run Step 4 if needed, then preview and apply.

**Description update, or confirmed rewrite** - preview: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, accept focus text for regeneration and do not apply. If confirmed, use `gh pr edit` and report the URL.

**Explainer archival** runs only in full workflow, with archival on, a composed `## New concepts` section, and apply confirmed. All paths resolve from the workspace root, never an incidental CWD. With two concepts, write one file per concept and include both in one JJ change immediately before the `gh` call:

1. Write the file with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If it exists from a prior run, overwrite it.
2. Run `jj file track docs/explainers/YYYY-MM-DD-<concept-slug>.md`. If JJ rejects the path as ignored, remove the just-written file, warn, and skip archival entirely. Never use `--include-ignored`.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
4. Active project instructions and syntax inferred at runtime from `jj log` always take precedence. Apply compatible Go guidance only to improve quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, capitalization, punctuation, layout, template, or example.
5. Commit only those files with `jj commit -m "<description-composed-from-runtime-conventions>" docs/explainers/<file>...`, move the feature bookmark to the resulting non-empty head, and `jj git push --remote <remote> --bookmark <bookmark>`. If there is no diff, the docs are already recorded; keep the link and continue.
6. Splice a head-bookmark blob URL per doc into `## New concepts` before applying.

If writing, committing, moving the bookmark, or pushing fails, warn and continue to PR creation without the link. Never leave the workflow stopped between a successful push and PR creation.

**Concept trailer** - when a body applied by this run contains `## New concepts`, print `New concepts: <name>[, <name>]` after the PR URL. In interactive full-workflow runs follow it with `Run /ce-explain <name> to go deeper.` per concept. Preserve ce-* routing. Print no trailer when this run applied no body or no PR exists.

---

## Applying via gh

Write the body to a collision-safe file under `<workspace-root>/.tmp` and pass `--body-file <path>`. If the workspace root cannot be resolved or its `.tmp` cannot be created, use `./.tmp`. Never use a system temporary directory, stdin, a heredoc directly into `gh`, or command substitution for the body.

```bash
WORKSPACE_ROOT=$(jj workspace root 2>/dev/null || pwd -P)
BODY_DIR="$WORKSPACE_ROOT/.tmp"
mkdir -p "$BODY_DIR" 2>/dev/null || { BODY_DIR="./.tmp"; mkdir -p "$BODY_DIR"; }
while :; do
  BODY_FILE="$BODY_DIR/pr-body.$(date +%Y%m%d%H%M%S).$$.$RANDOM.md"
  (set -C; : > "$BODY_FILE") 2>/dev/null && break
done
cat >> "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel prevents expansion. Remove the body file after the `gh` command succeeds or fails. Substitute the title verbatim with shell-safe quoting.

```bash
gh pr create --head <bookmark> --title "<title>" --body-file "$BODY_FILE"
gh pr edit <pr-ref> --title "<title>" --body-file "$BODY_FILE"
rm -f "$BODY_FILE"
```

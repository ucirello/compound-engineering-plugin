---
name: ce-commit-push-pr
description: Commit with JJ, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# JJ Commit, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema is not loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists or the call errors (for example, Codex edit modes), not because schema loading is required. Never silently skip the question.

## Mode

- **Description-only** - user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** - user wants to refresh/rewrite an existing PR's description with no commit/push intent. Run Step 1's bookmark and explicit PR-resolution portion without resolving a push remote. If no unique relevant bookmark and no explicit PR ref was supplied, ask for the PR number; never use argumentless/current-branch discovery. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** - otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** - set by orchestrated callers. Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current line of work; if Pre-A cannot resolve a base, stop and report rather than guess).

## Context

Use the labeled sections when they contain pre-populated data. Otherwise run the Context fallback below.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff -r @`

**Bookmarks at the working-copy revision:**
!`jj bookmark list -r @`

**Closest ancestor bookmarks:**
!`jj bookmark list -r 'heads(::@ & bookmarks())'`

**Recent commit messages:**
!`git log`

**Remote default bookmark:**
!`GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**GitHub repository URL:**
!`GIT_DIR="$(jj git root)" gh repo view --json url --jq '.url' 2>/dev/null || echo 'REPOSITORY_URL_UNRESOLVED'`

**Configured JJ remotes:**
!`jj git remote list 2>/dev/null || true`

**Workspace root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

```bash
jj status
jj diff -r @
jj bookmark list -r @
jj bookmark list -r 'heads(::@ & bookmarks())'
git log
GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || true
GIT_DIR="$(jj git root)" gh repo view --json url --jq '.url' 2>/dev/null || true
jj git remote list 2>/dev/null || true
jj workspace root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark and PR state

Run every `gh` command with `GIT_DIR="$(jj git root)"` so it also works in a non-colocated JJ workspace. Resolve `<base>` and the repository URL from `gh repo view`. If either is unresolved, ask the user; do not guess a default bookmark or repository. Resolve the configured remote whose normalized URL matches the base GitHub repository URL and save it as `<base-remote>`; do not assume a remote name. Zero or multiple matches from `jj git remote list` are blockers.

JJ has no current bookmark. Inspect bookmarks at `@` and the closest ancestor bookmarks instead:

- **Feature bookmark identifies the current line** - continue with that exact bookmark. If multiple feature bookmarks are plausible, ask which one to publish.
- **Only the default bookmark identifies the current line and work exists** - derive a non-conflicting feature bookmark name from the change content and continue at Step 3. Do not move or push the default bookmark.
- **No bookmark identifies the current line and work exists** - derive a non-conflicting feature bookmark name. The bookmark is created at the final intended change in Step 3; do not create a named pointer to an empty working-copy child.
- **No feature work** - if the revset from `<base>@<base-remote>` through `@` has no intended unpublished changes and `jj diff -r @ --summary` is empty, report and stop.

After selecting the exact feature bookmark, query only that explicit ref: `GIT_DIR="$(jj git root)" gh pr view <head-bookmark> --json url,title,body,state,headRefName,baseRefName,isCrossRepository,headRepository 2>/dev/null`. Never use argumentless/current-branch PR discovery. If bookmark selection is ambiguous, ask which bookmark to publish before calling `gh`; if the user identifies an existing PR by number or URL, pass that explicit ref instead and verify its `headRefName` is the selected bookmark before continuing.

Resolve and retain a writable `<push-remote>` before any push. For an existing PR, derive the head repository URL from `headRepository.nameWithOwner` (use `gh api` for the explicit PR if needed); for a new PR, use the resolved current GitHub repository URL. Normalize SSH and HTTPS forms and match that head repository against configured URLs from `jj git remote list`. Require exactly one writable configured match; zero or multiple matches are blockers. Do not substitute `<base-remote>` unless it is the unique head-repository match. Keep `<push-remote>` unchanged for every push and resolve `--repo` from its matched GitHub repository.

Note the existing PR URL, body, head bookmark, and base bookmark if `state: OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting. Never infer that a bookmark points at `@`; verify it with `jj bookmark list`.

## Step 2: Determine description conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At composition time, inspect the repository-local instructions and run `git log`. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. `jj log` may provide supplemental context but never replaces `git log`. Derive the message syntax dynamically. Do not impose fixed types, scopes, prefixes, subjects, templates, or examples. Add no attribution, badges, product branding, identity metadata, or model metadata. Use `<message>` wherever a command requires a change description.

Apply the same precedence to the PR title.

## Step 3: Commit and push

If the current line is based directly on the default bookmark, read `references/bookmark-creation.md` and follow its decision flow before continuing.

`@` contains the snapshotted working-copy changes. Inspect `jj diff -r @ --summary` and scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create 2-3 changes maximum with explicit filesets. When ambiguous, one change is fine.

Finish one concern while leaving other paths in the new working-copy change:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At composition time, inspect the repository-local instructions and run `git log`. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. `jj log` may provide supplemental context but never replaces `git log`.

Derive the message syntax dynamically; do not impose a fixed syntax, prefix, type, scope, template, or example.

```bash
jj commit <filesets> -m <message>
```

Finish all changes in `@`:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At composition time, inspect the repository-local instructions and run `git log`. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. `jj log` may provide supplemental context but never replaces `git log`.

Derive the message syntax dynamically; do not impose a fixed syntax, prefix, type, scope, template, or example.

```bash
jj commit -m <message>
```

After each commit, verify the finished change with `jj show -r @-` and inspect the remaining working-copy changes with `jj status`. When validating its description, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not validate against fixed message syntax, templates, or examples. Do not use broad filesets when unrelated or sensitive paths are present. If an explicit fileset names an untracked path, run `jj file track <fileset>` only after confirming it is intentional; never force ignored files into a change.

Resolve the final intended non-empty change exactly. A successful `jj commit` leaves it at `@-` and creates a new empty `@`; an already-committed stack may have a different shape, so inspect `jj log -r '<base>@<base-remote>..@'` instead of assuming. Create or advance only the feature bookmark:

```bash
jj bookmark set <head-bookmark> -r <final-intended-revision>
jj status
jj git push --remote <push-remote> --bookmark 'exact:<head-bookmark>'
```

Use `--allow-backwards` only after explicit user confirmation that a remote-backed bookmark should move backwards or sideways. Stop on working-copy conflicts, bookmark conflicts, empty descriptions, private revisions, or a push safety rejection; fetch and reconcile rather than overriding the remote. When validating whether a description is acceptable, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not validate against fixed message syntax, templates, or examples. If `jj status` is clean and the exact feature bookmark already matches its tracked remote bookmark, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full - the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch. If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve related and closing references already present there.

**Evidence decision** before composition. Modern harnesses provide browser, screenshot, terminal recording, and artifact capture tools. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) - incorporate it as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** - ask for the URL/markdown/path, or tell them to use the current harness's capture flow and return with the artifact. Do not launch another skill.
3. **Agent judgment on authored changes** - if you authored the changes and know they are non-observable (internal plumbing, type-only work, backend refactors without user-facing effects, docs/markdown/changelog/CI/test-only changes, or pure refactors), skip evidence handling without asking.

Otherwise, if the PR diff changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, or workflow output), include a concise validation note describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say why plainly in the validation section. Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are valid evidence, but never label them `Demo` or `Screenshots`.

**Concept teaching gate** before composition. Use the pre-resolved workspace root from Context (if it is empty or literal, resolve it with `jj workspace root`). Follow the project's active instructions when they identify the repository-local skill configuration; otherwise locate a unique repository-local `config.local.yaml` containing an active `pr_teaching_section:` or `pr_teaching_archive:` key. Multiple matches are a blocker; no match means the defaults below apply. Only an active, non-commented `pr_teaching_section:` key counts; commented template examples do not. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default is on. In the same read, resolve `pr_teaching_archive:`: it is on only when the active value is exactly `true`, otherwise off. A per-run `archive:on|off` token overrides the archive key.

- Gate **on** - judge concept novelty and compose the section per Step B2 of the reference. When off, also skip the Step 5 trailer, deeper-learning offer, and archival.
- Gate **off** - compose the description without concept handling.

Then continue through the reference to compose the title and body.

## Step 5: Apply and report

**Description-only mode** - print the title and body. Stop unless the user asks to apply.

**New PR** - apply per "Applying via gh" below using `gh pr create` with explicit `--repo`, `--head <head-bookmark>`, and `--base <base>`. Resolve `--repo` from the GitHub repository URL associated with `<push-remote>` so a non-colocated JJ workspace works correctly. Report the URL.

**Existing PR** - the pushed bookmark updates the PR. Report the PR URL, then ask whether to rewrite the description.

- **No** - done.
- **Yes** - run Step 4 if needed, then preview and apply.

**Description update mode, or existing-PR rewrite confirmed** - preview before applying. Show the title, its character count, the first two summary sentences, and total body line count, then ask whether to apply. If declined, accept focus text for regeneration; do not apply. If confirmed, use `gh pr edit` and report the URL.

**Explainer archival** - run only in full workflow when archival is on, a concepts section was composed, and applying the PR body is confirmed. A declined rewrite skips archival. Resolve all paths from the workspace root. With two concepts, write one file per concept and finish both in one JJ change immediately before the `gh` call:

1. Prepare each document in `<workspace-root>/.tmp/`; if `jj workspace root` cannot resolve, use a local `.tmp/`. Create the directory if needed. This is the only temporary-storage location.
2. Before replacing an existing destination, verify it is tracked with `jj file list 'root-file:"docs/explainers/YYYY-MM-DD-<concept-slug>.md"'`; do not overwrite an untracked or ignored existing file.
3. Move each prepared document to its destination, then run `jj file track 'root-file:"docs/explainers/YYYY-MM-DD-<concept-slug>.md"'`. If JJ reports that a new path is ignored, remove only the newly created destination, warn, and skip archival; never force-track it.
4. Write YAML frontmatter with `title`, `date`, `input_shape: concept`, and `subject`, followed by the teaching content. Add no attribution, badges, product branding, identity metadata, or model metadata.
5. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. At composition time, inspect the repository-local instructions and run `git log`. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. `jj log` may provide supplemental context but never replaces `git log`. Derive the message syntax dynamically; do not impose a fixed syntax, prefix, type, scope, template, or example. The description must identify the taught concept or concepts being archived. Finish only the explainer files with `jj commit <explainer-fileset> -m <message>`, verify with `jj show -r @-`, set `<head-bookmark>` to `@-`, and push with `jj git push --remote <push-remote> --bookmark 'exact:<head-bookmark>'`. If nothing changed, retain the existing link.
6. Build host-correct head-bookmark blob URLs with `GIT_DIR="$(jj git root)" gh browse`; never hardcode a public host. Splice the links into the concepts section before applying.

If writing, committing, or pushing archival fails, warn and continue without the link. Never strand the PR flow.

**Concept trailer** - when a body applied by this run contains a `## New concepts` section, print `New concepts: <name>[, <name>]` after the PR URL. In interactive full-workflow runs, follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` Print no trailer when this run applied no body (including a declined or pipeline-skipped rewrite), no PR exists, or the teaching gate is off.

---

## Applying via gh

The body must be written under `$(jj workspace root)/.tmp`; if `jj workspace root` cannot resolve, use local `.tmp`. Pass the file via `--body-file <path>`. Never use OS temp storage, `--body-file -`, stdin pipes, heredoc-to-stdin, or command substitution for the body.

```bash
WORKSPACE_ROOT=$(jj workspace root 2>/dev/null || pwd)
mkdir -p "$WORKSPACE_ROOT/.tmp"
BODY_FILE="$WORKSPACE_ROOT/.tmp/pr-body.md"
cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps variables, backticks, and sentinel-like body text from being expanded. Substitute the title verbatim and quote it safely.

```bash
GIT_DIR="$(jj git root)" gh pr create --repo <repository> --head <head-bookmark> --base <base> --title <title> --body-file "$BODY_FILE"
GIT_DIR="$(jj git root)" gh pr edit <PR-ref> --title <title> --body-file "$BODY_FILE"
```

---
name: ce-commit-push-pr
description: Describe changes, create or update a JJ bookmark, push it, and open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# Describe, Push, and Open a PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) - not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** - user wants only a description. Run Step 4 and print the result. Apply only if the user asks. Pass a supplied PR URL or number to Step 4.
- **Description update** - user wants to refresh an existing PR's description without changing or pushing revisions. If no open PR exists, report and stop. Otherwise run Step 4 in PR mode, then Step 5 to preview, confirm, and apply with `gh pr edit`.
- **Full workflow** - otherwise run Steps 1-5 in order.

**`mode:pipeline` modifier** - run the resolved mode non-interactively and suppress blocking asks. An existing-PR rewrite defaults to no; a description-update invocation applies directly; any other suppressed choice takes its documented conservative path. If a base or bookmark cannot be resolved safely, stop rather than guess.

## Context

JJ snapshots the working copy at the start of ordinary commands. Run the fallback on platforms that do not populate the labeled sections; otherwise use the populated values directly.

**JJ status:**
!`jj status`

**Working-copy change:**
!`jj diff -r @`

**Bookmarks near the working copy:**
!`jj bookmark list -r '@ | @-' --all-remotes`

**Recent history:**
!`jj log -r 'ancestors(@, 10)' --no-graph`

**Configured Git remotes:**
!`jj git remote list`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**Existing PR check:**
!`GIT_DIR="$(jj git root 2>/dev/null)" gh pr view --json url,title,body,state,headRefName 2>/dev/null || echo 'NO_OPEN_PR'`

**Workspace root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

```bash
jj status
jj diff -r @
jj bookmark list -r '@ | @-' --all-remotes
jj log -r 'ancestors(@, 10)' --no-graph
jj git remote list
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
GIT_DIR="$(jj git root)" gh pr view --json url,title,body,state,headRefName
jj workspace root
```

---

## Step 1: Resolve bookmark and PR state

Resolve the default bookmark with `gh repo view`. If that fails, inspect `jj bookmark list --all-remotes` and ask when more than one plausible default exists; do not assume a fixed default name.

JJ has no current branch and anonymous working-copy changes are normal. Determine `<feature-bookmark>` from an open PR's `headRefName`, or from a unique non-default local bookmark at `@` or `@-`. If neither exists but there is work to ship, derive a non-conflicting bookmark name from the change's meaning; create it only after Step 3 has finalized the stack. If multiple plausible feature bookmarks exist, ask which one to push.

Routing:

- **No work beyond the default remote bookmark** - report that there is no feature work and stop.
- **Work based directly on, or currently named by, the default bookmark** - read `references/branch-creation.md` before Step 3.
- **Feature stack or feature bookmark** - continue without relocating the working copy.

After resolving the feature bookmark, query `GIT_DIR="$(jj git root)" gh pr list --head <feature-bookmark> --state open --json url,title,body,state,headRefName`. Record a unique open PR's URL and body; ask if the query is ambiguous. Step 5 uses the URL to distinguish creation from update, and Step 4 uses the existing body as preservation context.

## Step 2: Determine description conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from the project's active instructions and conventions and from `git log` ALWAYS wins. Apply only compatible Go guidance: describe the change's purpose and effect clearly, and include rationale when it matters. Do not impose a type, scope, capitalization, subject shape, body layout, or other convention absent from the repository.

## Step 3: Finalize the change stack and push

If the work is based on the default bookmark, follow `references/branch-creation.md` first. Run `jj status` and `jj diff -r @` again so the current working copy is snapshotted and reviewed before rewriting it.

Scan the working-copy change for naturally distinct concerns. Keep one change when the separation is ambiguous. When multiple logical changes are clear, use `jj split` with explicit workspace-relative filesets; do not emulate a staging area and do not select unrelated paths. Filesets can combine neutral path placeholders such as `root:"<path>" | root:"<other-path>"`. Repeat the split only while a remaining change is independently meaningful.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For each resulting revision, compose its description under Step 2's precedence rule, then apply it with `jj describe -r <revision> -m "<description>"`. Review the result with `jj log` and `jj diff -r <revision>`. A revision must contain one coherent change, have a non-empty repository-conforming description, and exclude secrets, generated output, and unrelated files. Fix an incorrect grouping with another fileset-based `jj split`; fix only a description with `jj describe`.

After the last described revision, run `jj new` to leave an empty working-copy change above the completed stack. Point the feature bookmark at the completed tip with `jj bookmark set <feature-bookmark> -r @-`. Verify the bookmark and outgoing range with `jj bookmark list <feature-bookmark> --all-remotes` and `jj log -r '<feature-bookmark>@<push-remote>..<feature-bookmark>'`; if the remote bookmark does not yet exist, inspect the stack from the resolved base instead.

Push only the selected bookmark through Git remote interop:

```bash
jj git push --remote <push-remote> --bookmark <feature-bookmark>
```

If push reports stale remote state, run `jj git fetch --remote <push-remote>`, inspect `jj status`, `jj bookmark list <feature-bookmark> --all-remotes`, and the divergent revisions, resolve deliberately, then retry. Never move a conflicted bookmark by guessing. If the stack is already described, the bookmark already targets its tip, and the remote bookmark is synchronized, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md` in full.** Pass any PR ref identified by mode dispatch. When rewriting an existing PR, pass its URL so PR mode can preserve existing work-item references and user-authored evidence.

Treat evidence as user-supplied context or validation prose. Do not invent or upload evidence.

- Incorporate supplied evidence according to its artifact type and the repository's PR conventions.
- If evidence was explicitly requested but not supplied, ask for the URL, markdown, or path, or ask the user to return after using the harness's capture flow.
- For changes known to be non-observable, skip visual-evidence handling without asking.
- For observable behavior, state what was actually exercised and observed. If validation could not run because required access or infrastructure was unavailable, say so plainly.

Do not block PR creation solely because no visual artifact exists, and do not present test output as visual evidence.

**Concept teaching gate:** Use the pre-resolved workspace root. If it is unavailable, resolve it with `jj workspace root`. Read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only active, non-commented keys count. `pr_teaching_section` is off only when its active value is exactly `false`; otherwise it defaults on. `pr_teaching_archive` is on only when its active value is exactly `true`; otherwise it defaults off. A per-run `archive:on|off` token overrides archival for this invocation.

- Gate **on** - run the reference's concept judgment and composition rules.
- Gate **off** - omit concept handling, its trailer and offer, and archival.

## Step 5: Apply and report

**Description-only mode** - print the title and body, then stop unless the user asks to apply.

**New PR** - apply with `gh pr create` as described below and report the URL.

**Existing PR in full workflow** - report the URL, then ask whether to rewrite the description. If yes, run Step 4 if needed, preview, and apply. If no, stop.

**Description update or confirmed rewrite** - preview the proposed title and a concise body summary without imposing a fixed preview template. Ask whether to apply unless pipeline mode already supplies apply intent. If declined, accept focus text for regeneration and do not apply.

**Explainer archival** runs only in full workflow when archival is on, a concepts section was composed, and body application is confirmed. Description-only and declined rewrites never write repository files. Resolve every path from the workspace root.

1. Check the proposed `docs/explainers/<date>-<concept-slug>.md` path against the applicable `.gitignore` rules before writing. If ignored, warn and skip archival without forcing the path.
2. Write each explainer with the repository's established metadata and the composed teaching content. If an existing file is intentionally being refreshed, update it in place.
3. Snapshot with `jj status`, inspect only the explainer paths with `jj diff`, and isolate them from any other working-copy content with an explicit fileset-based `jj split` when necessary.
4. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply Step 2's precedence: repository-local instructions and syntax observed in `git log` take precedence, and Go guidance applies only when compatible.
5. Describe the explainer revision with `jj describe`, run `jj new`, move the feature bookmark to the new completed tip, and push that bookmark with `jj git push --remote <push-remote> --bookmark <feature-bookmark>`. If no content changed, retain the existing link and do not create an empty described revision.
6. Add a head-bookmark blob URL for each archived document to the concepts section before applying the PR body.

If archival writing, description, or push fails, warn and continue to PR creation without the link. Do not leave the workflow between archival and PR application.

When an applied body contains a concepts section, report the concept names after the PR URL. In interactive full-workflow runs, mention the functional `/ce-explain <concept>` command for deeper study. Omit this report when no body was applied or no PR exists.

---

## Applying via gh

Write the body beneath the workspace in `.tmp/rocketclaw/`; if `jj workspace root` is unavailable, use the current directory's `.tmp/rocketclaw/`. Do not use an OS-wide scratch location or API. `.context/` is reserved for repository-bound, user-curated or branch-inseparable state, not transient command input. Ensure `.tmp/` is ignored before creating the file so a later JJ snapshot cannot track it.

```bash
ROOT="$(jj workspace root 2>/dev/null || pwd)"
BODY_DIR="$ROOT/.tmp/rocketclaw"
mkdir -p "$BODY_DIR"
BODY_FILE="$BODY_DIR/pr-body-$$.md"
cat > "$BODY_FILE" <<'__PR_BODY_END__'
<composed PR body>
__PR_BODY_END__
```

The quoted sentinel prevents shell expansion inside the body. Pass the title verbatim with shell-safe quoting.

```bash
GIT_DIR="$(jj git root)" gh pr create --base "<base>" --head "<feature-bookmark>" --title "<composed PR title>" --body-file "$BODY_FILE"
GIT_DIR="$(jj git root)" gh pr edit "<PR ref or URL>" --title "<composed PR title>" --body-file "$BODY_FILE"
rm -f "$BODY_FILE"
```

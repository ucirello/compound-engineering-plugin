---
name: ce-commit-push-pr
description: Describe changes, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [remote:<name>] [archive:on|off]"
---

# JJ Change, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no change/push intent. Resolve an explicit PR ref from the argument or resolve the feature bookmark and run `gh pr view <bookmark>` as in Step 1; never infer from Git HEAD. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the captured PR URL), then Step 5 to preview, confirm, and apply via `gh pr edit <captured-PR-URL-or-number>`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess).

**`remote:<name>` modifier** — accepted only with `mode:pipeline` from an orchestrator that already matched the expected GitHub repository identity to exactly one JJ remote. Verify that the named remote exists in `jj git remote list`, retain it as `<head-remote>`, and do not independently select a different remote. Without `mode:pipeline`, reject this modifier rather than trusting caller-supplied routing.

## Context

**On platforms other than Claude Code**, run the Context fallback below. **In Claude Code**, the labeled sections contain pre-populated data — use them directly.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Current bookmarks:**
!`jj bookmark list -r 'heads(::@ & bookmarks())'`

**Recent JJ changes:**
!`jj log -n 10`

**Past commit messages:**
!`git log -n 10 --format=full`

**Remote default bookmark:**
!`GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**Workspace root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list -r 'heads(::@ & bookmarks())'; printf '\n=== JJ CHANGES ===\n'; jj log -n 10; printf '\n=== PAST COMMIT MESSAGES ===\n'; git log -n 10 --format=full; printf '\n=== DEFAULT_BOOKMARK ===\n'; GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'; printf '\n=== WORKSPACE_ROOT ===\n'; jj workspace root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark and PR state

Use the remote default bookmark returned by GitHub. If it returned `DEFAULT_BOOKMARK_UNRESOLVED`, resolve an unambiguous tracked default bookmark or a single non-root `trunk() & ~root()` revision; otherwise stop and report the ambiguity. Never guess a bookmark name.

Bookmark routing:

- **No feature bookmark** — this is normal in JJ. Derive a feature bookmark name from the change content and continue at Step 3, which creates it at the completed change before pushing. Do not ask whether to create it; invoking the full workflow already confirms that the work should become bookmark-backed. If the name exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **Default bookmark is the closest bookmark with work to do** (a non-empty working-copy change, unpublished ancestors, or no tracked remote bookmark) — derive a feature bookmark name and continue at Step 3. Pushing the default bookmark directly is not supported.
- **Default bookmark with no work** — report no feature work and stop.
- **Feature bookmark** — continue and retain its name for the explicit move before pushing.

After resolving the feature bookmark name, detect its PR explicitly; never rely on Git HEAD or an implicit current branch:

```bash
GIT_DIR="$(jj git root)" gh pr view <bookmark> --json number,url,title,body,state,headRefName,headRepository,headRepositoryOwner
```

If this returns an open PR, capture its number and URL. Step 5 uses that captured identifier to route between new-PR and existing-PR application, and Step 4 uses the existing body as preservation context when rewriting.

Resolve a writable `<head-remote>` before any push. When a validated `remote:<name>` pipeline modifier is present, use that retained remote. Otherwise, for an existing PR, the expected repository is its head repository from the metadata above; for a new PR, get the expected repository with `GIT_DIR="$(jj git root)" gh repo view --json nameWithOwner,sshUrl,url`. Compare that `owner/repo` identity against every URL from `jj git remote list`, normalizing GitHub HTTPS and SSH forms and an optional `.git` suffix. Select `origin` only when its normalized identity is the expected repository; otherwise select the matching configured remote. If zero or multiple remotes match, stop and report the ambiguity rather than guessing. A remote merely named `origin` is not evidence that it is writable or points at the PR head repository. Retain `<head-remote>` for every push in Steps 3 and 5.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For JJ change descriptions, determine repository-local syntax at runtime from active project instructions and actual `git log`; those sources always win over compatible quality guidance from the linked Go guidance. Keep `jj log` for revision/history workflow only. If ownership history is needed to understand the convention around a changed file, use `jj file annotate <path>`. Match PR titles to repository conventions independently.

## Step 3: Describe changes and push

If the default bookmark is the closest bookmark, bookmark creation needs to handle a stale local `<base>`, unpublished changes on local `<base>`, and working-copy changes that conflict with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing, passing the configured remote that matches the GitHub base repository as `<base-remote>`; do not assume `origin`.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate JJ changes (2-3 max). Group at file level only. When ambiguous, one change is fine. JJ snapshots the working copy automatically; there is no staging step.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For each group, repository-local syntax from active project instructions and actual `git log` wins; use only compatible quality guidance from the linked Go guidance. Describe and finish each selected file group directly, leaving other paths in the working-copy change:

```bash
CHANGE_DESCRIPTION='<message composed from the standards above>'
jj commit <selected-paths> -m "$CHANGE_DESCRIPTION"
```

Create a new feature bookmark at `@-`, or move the existing feature bookmark there, then push that bookmark:

```bash
jj bookmark create <bookmark> -r @-
jj git push --bookmark <bookmark> --remote <head-remote>
```

For an existing feature bookmark, use `jj bookmark set <bookmark> -r @-` instead of creating it. If the working-copy change is empty, the bookmark already targets the intended head, and the remote bookmark is current, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. This skill does not own a dedicated capture workflow; modern harnesses provide their own browser, screenshot, terminal recording, and artifact capture tools. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use the current harness's capture flow and return with the artifact. Do not launch another capture skill.
3. **Agent judgment on authored changes** — if you authored the changes and know the change is non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the bookmark diff changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved workspace root from Context (if it is empty or shows a literal command string, resolve it at runtime with `jj workspace root`) and read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments, and the shipped template documents keys as commented examples; matching those would silently flip the gate. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default: **on**. The same read resolves `pr_teaching_archive:` — on only when the active value is exactly `true`, otherwise **off** — and a per-run `archive:on|off` token overrides the archive key for this invocation.

- Gate **on** — judge concept novelty and compose the section per **Step B2** of the reference. The gate is single: when it is off, skip judgment, the section, the Step 5 trailer and offer, and archival entirely.
- Gate **off** — compose the description without any concept handling.

Then continue with the rest of the reference (Steps A through C, including the Step B2 concept judgment when the gate is on) to compose the title and body.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — the new changes are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. Ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply per "Applying via gh" below using `gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked doc change is left behind. All paths resolve from the pre-resolved workspace root in Context, never the CWD. With two taught concepts, write one file per concept and include both in one JJ change. Execute as explicit transitions immediately before the `gh` call:

1. Check the candidate path against the repository's `.gitignore`. If it is ignored, print a one-line warning and skip archival entirely, writing nothing; do not override ignore rules.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it. Confirm the path appears in `jj file list <path>`; if it does not, remove the new file, warn, and skip archival.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
4. Populate `CHANGE_DESCRIPTION` with the message composed under step 3, run `jj commit <paths> -m "$CHANGE_DESCRIPTION"`, move the feature bookmark to `@-`, and run `jj git push --bookmark <bookmark> --remote <head-remote>`. Repository-local syntax from active project instructions and actual `git log` wins; use only compatible quality guidance from the linked Go guidance. If there is no change to describe, the doc is already present from a prior run — keep the link and continue.
5. Splice a head-bookmark blob URL per doc into the `## New concepts` section before applying.

If the doc write, describe, or push fails, warn and continue to PR creation without the link — never strand the flow between the JJ change and PR.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

---

## Applying via gh

The body **must** be written under `$(jj workspace root)/.tmp/rocketclaw/` and passed via `--body-file <path>`. If there is no JJ workspace, use `./.tmp/rocketclaw/`. Never use OS-global scratch storage, `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd)" && BODY_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw" && mkdir -p "$BODY_DIR" && BODY_FILE="$BODY_DIR/pr-body-$$.md" && cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
PR_URL=$(GIT_DIR="$(jj git root)" gh pr create --head <bookmark> --title "<TITLE>" --body-file "$BODY_FILE")   # new PR; capture the returned URL
GIT_DIR="$(jj git root)" gh pr edit <captured-PR-URL-or-number> --title "<TITLE>" --body-file "$BODY_FILE"       # existing PR
```

Remove `$BODY_FILE` after the `gh` command completes. The PR body has no producer identity.

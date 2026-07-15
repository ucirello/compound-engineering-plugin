---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# JJ Commit, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no commit/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess).

## Context

**On platforms other than Claude Code**, run the Context fallback below. **In Claude Code**, the labeled sections contain pre-populated data — use them directly.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Current bookmarks at the working-copy revision:**
!`jj bookmark list -r @ -T 'name ++ "\n"'`

**Recent commits:**
!`jj log -r '::@' -n 10 --no-graph -T 'description.first_line() ++ "\n"'`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**Existing PR check:**
!`gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'`

**Repo root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS_AT_WORKING_COPY ===\n'; jj bookmark list -r @ -T 'name ++ "\n"'; printf '\n=== LOG ===\n'; jj log -r '::@' -n 10 --no-graph -T 'description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'; printf '\n=== PR_CHECK ===\n'; gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'; printf '\n=== REPO_ROOT ===\n'; jj workspace root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark and PR state

If the default bookmark returned `DEFAULT_BOOKMARK_UNRESOLVED`, inspect remote bookmarks with `jj bookmark list --remote origin` and try exact `main`, `master`, then `develop`. If none resolve, ask the user; in `mode:pipeline`, stop rather than guess.

Bookmark routing:

- **No local bookmark at `@`** — derive a feature-bookmark name from the change content and reserve it for Step 3. JJ working-copy revisions need no special recovery step. If the derived name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **Default bookmark at `@` with work to do** (working-copy changes, local-only revisions, or no tracked remote bookmark) — derive a feature-bookmark name and continue at Step 3, which handles bookmark creation safely. Do not ask whether to create it; pushing the default directly is not supported.
- **Default bookmark at `@` with no work** — report no feature-bookmark work and stop.
- **Feature bookmark at `@`** — continue with that bookmark. If multiple feature bookmarks point at `@`, ask which to push; in `mode:pipeline`, stop rather than guess.

Note the existing PR URL and body from the PR check if `state: OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At runtime, inspect the repository's active local instructions and conventions, including scoped instructions governing the changed files, then run the repository-preferred `git log` command and inspect its recent messages. If no invocation is prescribed, inspect at least the 10 most recent messages with `git log`. Those sources win; apply the remaining Go guidance only where compatible.

For each message, make the first line a short summary of the change. When repository convention permits, prefix it with the primary affected package or component followed by a colon; after the colon, use a lowercase verb phrase that completes "this change modifies the project to ...", with no trailing period. Keep it as short as practical and preferably under 72 characters. Add a body only when it supplies useful motivation, behavior, risks, or context; separate it from the first line with a blank line, write prose rather than Markdown, and wrap ordinary text near 72 characters while leaving long links, tables, or other content intact when wrapping would hurt clarity. Put tracker references after the body with a separating blank line and follow the project's known tracker convention; never guess closing semantics. Do not add `Signed-off-by` or attribution lines. Validate the completed message against these rules and the repository evidence before committing. Do not use or prescribe fixed messages, prefixes, types, scopes, subjects, bodies, templates, placeholders, or examples, including Conventional Commit examples.

## Step 3: Commit and push

If the default bookmark points at `@`, bookmark creation needs to handle stale local `<base>` and local-only revisions. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate changes (2-3 max). Group at file level only; do not use interactive hunk selection. When ambiguous, one change is fine.

JJ has no staging area. Commit each explicit file group so unrelated, ignored, generated, or secret files are not swept in.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Reinspect the applicable repository-local instructions and repository-preferred `git log` output when the file group changes. Those sources win; apply the remaining Go guidance only where compatible. For each message, make the first line a short summary of the change. When repository convention permits, prefix it with the primary affected package or component followed by a colon; after the colon, use a lowercase verb phrase that completes "this change modifies the project to ...", with no trailing period. Keep it as short as practical and preferably under 72 characters. Add a body only when it supplies useful motivation, behavior, risks, or context; separate it from the first line with a blank line, write prose rather than Markdown, and wrap ordinary text near 72 characters while leaving long links, tables, or other content intact when wrapping would hurt clarity. Put tracker references after the body with a separating blank line and follow the project's known tracker convention; never guess closing semantics. Do not add `Signed-off-by` or attribution lines. Validate the completed message against these rules and the repository evidence before committing, then supply the runtime-composed description without a fixed message, prefix, type, scope, subject, body, command template, placeholder, or example, including Conventional Commit examples.

After the final `jj commit`, the completed head is `@-`. Create or advance the feature bookmark to it, then push that bookmark:

```bash
jj bookmark set <feature-bookmark> -r @-
jj git push --bookmark <feature-bookmark> --remote origin
```

If `@` is empty and the feature bookmark is already synchronized with its remote bookmark, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. This skill does not own a dedicated capture workflow; modern harnesses provide their own browser, screenshot, terminal recording, and artifact capture tools. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use the current harness's capture flow and return with the artifact. Do not launch another skill.
3. **Agent judgment on authored changes** — if you authored the commits and know the change is non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the feature-line diff changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved repo root from Context (if it is empty or shows a literal command string, resolve it at runtime with `jj workspace root`) and read `<repo-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments, and the shipped template documents keys as commented examples; matching those would silently flip the gate. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default: **on**. The same read resolves `pr_teaching_archive:` — on only when the active value is exactly `true`, otherwise **off** — and a per-run `archive:on|off` token overrides the archive key for this invocation.

- Gate **on** — judge concept novelty and compose the section per **Step B2** of the reference. The gate is single: when it is off, skip judgment, the section, the Step 5 trailer and offer, and archival entirely.
- Gate **off** — compose the description without any concept handling.

Then continue with the rest of the reference, including the Step B2 concept judgment when the gate is on, to compose the title and body.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — the new commits are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. Ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply per "Applying via gh" below using `gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked doc commit is left behind. All paths resolve from the pre-resolved repo root in Context, never the CWD. With two taught concepts, write one file per concept and commit both in the single change. Execute as explicit transitions immediately before the `gh` call:

1. Create the directory if needed and record whether each path exists. Before changing any pre-existing file, run `jj file track` for that path without `--include-ignored`. For a new path, create an empty file exclusively, run `jj file track`, and only then write it. If JJ reports that a path is ignored or otherwise cannot be tracked, print a one-line warning and skip archival entirely; remove only an empty file created by this run. Never overwrite a pre-existing file before this check, remove it, or force-track it.
2. After every path passes the check, write YAML frontmatter containing the title, date, concept input shape, subject, and the teaching content. A trackable pre-existing file may then be overwritten.
3. Commit only those file(s), advance the feature bookmark, and push. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Inspect repository-local instructions and run the repository-preferred `git log` at runtime; those sources win, and the remaining Go guidance applies only where compatible. Make the first line a short summary of the change. When repository convention permits, prefix it with the primary affected package or component followed by a colon; after the colon, use a lowercase verb phrase that completes "this change modifies the project to ...", with no trailing period. Keep it as short as practical and preferably under 72 characters. Add a body only when it supplies useful motivation, behavior, risks, or context; separate it from the first line with a blank line, write prose rather than Markdown, and wrap ordinary text near 72 characters while leaving long links, tables, or other content intact when wrapping would hurt clarity. Put tracker references after the body with a separating blank line and follow the project's known tracker convention; never guess closing semantics. Do not add `Signed-off-by` or attribution lines. Validate the completed message against these rules and the repository evidence before committing. Do not use or prescribe a fixed message, prefix, type, scope, subject, body, template, placeholder, or example, including Conventional Commit examples. If the change is empty, the doc is already committed from a prior run — keep the link and continue.
4. Splice a head-branch blob URL per doc into the `## New concepts` section before applying.

If the doc write, commit, or push fails, warn and continue to PR creation without the link — never strand the flow between commit and PR.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

---

## Applying via gh

The body **must** be written beneath `$(jj workspace root)/.tmp/rocketclaw`, falling back to local `.tmp/rocketclaw` when no JJ workspace exists, and passed via `--body-file <path>`. Never use OS-global temp storage, `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

Before either create or edit, validate the title as a commit-message first line. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Reinspect the repository's active instructions and repository-preferred `git log` output; those sources win, and the remaining Go guidance applies only where compatible. The title must be a short summary of the change. When repository convention permits, prefix it with the primary affected package or component followed by a colon; after the colon, use a lowercase verb phrase that completes "this change modifies the project to ...", with no trailing period. Keep it as short as practical and preferably under 72 characters. The PR body is Markdown and is not a commit-message body, so commit-body wrapping and Markdown restrictions do not apply to it. Follow the project's known tracker convention and never guess closing semantics. Do not add `Signed-off-by` or attribution lines. Do not use or prescribe a fixed title, prefix, type, scope, subject, template, placeholder, or example, including Conventional Commit examples.

```bash
ROOT=$(jj workspace root 2>/dev/null || printf '.\n') && BODY_DIR="$ROOT/.tmp/rocketclaw" && mkdir -p "$BODY_DIR" && while :; do BODY_FILE="$BODY_DIR/pr-body.$(date +%s).$$.$RANDOM"; (set -o noclobber; : > "$BODY_FILE") 2>/dev/null && break; done && cat >> "$BODY_FILE" <<'__RC_PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__RC_PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```

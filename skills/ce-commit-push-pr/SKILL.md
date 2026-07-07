---
name: ce-commit-push-pr
description: Describe JJ changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
---

# JJ Change, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no change/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

## Context

**On platforms other than Claude Code**, run the Context fallback below. **In Claude Code**, the labeled sections contain pre-populated data — use them directly.

**JJ status:**
!`jj st`

**Working copy diff:**
!`jj diff`

**Current bookmark:**
!`jj log -r @ --no-graph -T 'bookmarks.join(" ") ++ "\n"' 2>/dev/null || true`

**Recent changes:**
!`jj log --limit 10 --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**Existing PR check:**
!`gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'`

### Context fallback

```bash
printf '=== STATUS ===\n'; jj st; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARK ===\n'; jj bookmark list --tracked 2>/dev/null | awk '/\*/ {print $1; exit}' || true; printf '\n=== LOG ===\n'; jj log --limit 10 --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'; printf '\n=== PR_CHECK ===\n'; gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'
```

---

## Step 1: Resolve bookmark and PR state

If the remote default bookmark returned `DEFAULT_BOOKMARK_UNRESOLVED`, try `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If both fail, fall back to `main`.

Bookmark routing:

- **No current bookmark** — automatically create a feature bookmark on the current change before continuing. Derive the bookmark name from the change content, run `jj bookmark create <bookmark-name>`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full change/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default bookmark with work to do** (undescribed, unpublished, or no upstream) — automatically create a feature bookmark (pushing the default directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to create a bookmark — working on the default bookmark is not an option here.
- **On default bookmark with no work** — report no feature bookmark work and stop.
- **Feature bookmark** — continue.

Note the existing PR URL and body from the PR check if `state: OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Match repo style for change descriptions and PR titles (project instructions in context > recent change descriptions > conventional commits as default). With conventional commits, default to `fix:` over `feat:` when ambiguous — adding code to remedy broken or missing behavior is `fix:`. Reserve `feat:` for capabilities the user could not previously accomplish. The user may override.

## Step 3: Describe changes and push

If on the default bookmark, bookmark creation needs to handle a stale local `<base>`, unpublished changes on local `<base>`, and working-copy changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate JJ changes (2-3 max). Group at file level only. JJ has no staging area; use `jj split <path>...`, path-limited `jj commit <path>...`, or `jj squash` as appropriate. When ambiguous, one change is fine.

Describe each group with path-limited JJ operations. **Do not use staging commands** — JJ has no staging area, and path-limited `jj commit` avoids sweeping in `.env`, build artifacts, and generated files:

```bash
jj commit file1 file2 file3 -m "$(cat <<'EOF'
change description here
EOF
)"
```

Then push:

```bash
jj git push --bookmark <bookmark-name>
```

If the working copy is clean and all changes are already pushed, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. CE no longer owns a dedicated capture workflow; modern harnesses provide their own browser, screenshot, terminal recording, and artifact capture tools. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use the current harness's capture flow and return with the artifact. Do not launch another CE skill.
3. **Agent judgment on authored changes** — if you authored the changes and know the change is non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the bookmark diff changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

Then continue with the rest of the reference (Steps A through G) to compose the title and body.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — the new changes are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. Ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply per "Applying via gh" below using `gh pr edit` and report the URL.

---

## Applying via gh

The body **must** be written to a temp file and passed via `--body-file <path>`. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
BODY_FILE=$(mktemp "${TMPDIR:-/tmp}/ce-pr-body.XXXXXX") && cat >> "$BODY_FILE" <<'__CE_PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__CE_PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```

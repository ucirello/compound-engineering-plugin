---
name: ce-commit-push-pr
description: Describe JJ changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# JJ Commit, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no commit/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark/change; if Pre-A cannot resolve a base, stop and report rather than guess).

## Context

**On platforms other than Claude Code**, run the Context fallback below. **In Claude Code**, the labeled sections contain pre-populated data — use them directly.

**jj status:**
!`jj status`

**Working tree diff:**
!`jj diff`

**Current bookmarks:**
!`jj bookmark list --revisions @`

**Recent changes:**
!`jj log -r 'ancestors(@, 10)' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`

**Existing PR check:**
!`gh pr view --json url,title,body,state`

**Repo root (pre-resolved):**
!`jj root`

### Context fallback

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list --revisions @; printf '\n=== LOG ===\n'; jj log -r 'ancestors(@, 10)' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'; printf '\n=== PR_CHECK ===\n'; gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'; printf '\n=== REPO_ROOT ===\n'; jj root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark and PR state

The remote default bookmark is the GitHub default bookmark name as a JJ bookmark (usually `main` or `master`). If it returned `DEFAULT_BOOKMARK_UNRESOLVED`, an error, or empty output, fall back to `main`. An error from the existing-PR check means no open PR was found (or `gh` is unavailable) — treat it as `NO_OPEN_PR`.

Bookmark routing:

- **No bookmark on `@`** — derive a meaningful bookmark name from the change content, run `jj bookmark set <bookmark-name> -r @`, re-read `jj bookmark list --revisions @`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed.
- **On default bookmark with work to do** — create a new change from the current default bookmark with `jj new <default-bookmark>@origin` when available, otherwise `jj new <default-bookmark>`, then set a derived feature bookmark on `@`. Pushing the default bookmark directly is not supported.
- **On default bookmark with no work** — report no feature bookmark work and stop.
- **Feature bookmark** — continue.

Note the existing PR URL and body from the PR check if `state: OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Match repo style for change descriptions and PR titles (project instructions in context > recent JJ descriptions > conventional commits as default). With conventional commits, default to `fix:` over `feat:` when ambiguous — adding code to remedy broken or missing behavior is `fix:`. Reserve `feat:` for capabilities the user could not previously accomplish. The user may override.

## Step 3: Describe and push

If on the default bookmark, bookmark creation needs to handle stale local `<base>`, local-only changes on `<base>`, and working-copy changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate JJ changes (2-3 max). Group at file level only — use `jj split` when a mixed current change must be separated. When ambiguous, one change is fine.

Describe each group as a logical change. JJ has no staging area; when only some paths belong in a logical change, split first:

```bash
jj split file1 file2 file3
jj describe -m "$(cat <<'EOF'
commit message here
EOF
)"
```

Then push:

```bash
jj git push --bookmark <current-bookmark>
```

If the working copy is clean and all described changes are already pushed, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. CE no longer owns a dedicated capture workflow; modern harnesses provide their own browser, screenshot, terminal recording, and artifact capture tools. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use the current harness's capture flow and return with the artifact. Do not launch another CE skill.
3. **Agent judgment on authored changes** — if you authored the commits and know the change produces no material claim a reviewer would need evidence for (internal plumbing, type-only, backend refactor without user-facing effect, inert documentation, pure refactors), skip evidence handling without asking. Classify by runtime purpose, not extension: markdown or YAML that is runtime agent instructions, configuration, generated product content, or policy code is not auto-skippable just for being markdown or YAML.

Otherwise, if the bookmark diff changes behavior a reviewer would need evidence for (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output, ranking/scoring logic, deployment or config behavior), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved repo root from Context (if it is empty or shows a literal command string, resolve it at runtime with `jj root`) and read `<repo-root>/.compound-engineering/config.local.yaml` with the native file-read tool. Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments, and the shipped template documents keys as commented examples; matching those would silently flip the gate. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default: **on**. The same read resolves `pr_teaching_archive:` — on only when the active value is exactly `true`, otherwise **off** — and a per-run `archive:on|off` token overrides the archive key for this invocation.

- Gate **on** — judge concept novelty and compose the section per **Step B2** of the reference. The gate is single: when it is off, skip judgment, the section, the Step 5 trailer and offer, and archival entirely.
- Gate **off** — compose the description without any concept handling.

Then continue with the rest of the reference (Steps A through E, including the Step B2 concept judgment when the gate is on) to compose the title and body — Step E is the pre-apply coverage audit and must run before the body is returned.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — the new changes are already on the PR bookmark from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. Ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply per "Applying via gh" below using `gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked doc commit is left behind. All paths resolve from the pre-resolved repo root in Context, never the CWD. With two taught concepts, write one file per concept and stage both in the single commit. Execute as explicit transitions immediately before the `gh` call:

1. Check the repo ignore rules for `docs/explainers/YYYY-MM-DD-<concept-slug>.md`. If the path is ignored, print a one-line warning and skip archival entirely, writing nothing.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Include only those file(s) in a JJ change, describe it with `docs(explainer): teach <concept>[, <concept>]`, and push the current bookmark. If JJ reports no changes, the doc is already recorded from a prior run — keep the link and continue.
4. Splice a head-bookmark blob URL per doc into the `## New concepts` section before applying.

If the doc write, commit, or push fails, warn and continue to PR creation without the link — never strand the flow between commit and PR.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

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

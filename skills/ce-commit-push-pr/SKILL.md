---
name: ce-commit-push-pr
description: Describe and finalize JJ changes, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# JJ Describe, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no change-finalization/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess).

## Context

**On platforms other than Claude Code**, run the Context fallback below. **In Claude Code**, the labeled sections contain pre-populated data — use them directly.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Bookmarks at the current change or its parent:**
!`jj bookmark list -r '@ | @-'`

**Recent changes:**
!`jj log -r 'ancestors(@, 10)' --limit 10`

**Remote default branch:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BRANCH_UNRESOLVED'`

**Existing PR check:**
!`gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'`

**Repo root (pre-resolved):**
!`jj workspace root 2>/dev/null || true`

### Context fallback

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list -r '@ | @-'; printf '\n=== LOG ===\n'; jj log -r 'ancestors(@, 10)' --limit 10; printf '\n=== DEFAULT_BRANCH ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BRANCH_UNRESOLVED'; printf '\n=== PR_CHECK ===\n'; gh pr view --json url,title,body,state 2>/dev/null || echo 'NO_OPEN_PR'; printf '\n=== REPO_ROOT ===\n'; jj workspace root 2>/dev/null || true
```

---

## Step 1: Resolve bookmark and PR state

If the remote default branch returned `DEFAULT_BRANCH_UNRESOLVED`, retry `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If that fails, fall back to `main`.

Bookmark routing:

- **No feature bookmark** -- derive a feature bookmark name from the change content and continue at Step 3, which creates it safely. If the name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On the default bookmark with work to do** (working-copy changes, unpushed changes, or no remote bookmark) -- derive a feature bookmark and continue at Step 3, which handles creation safely. Do not ask whether to create it -- pushing the default bookmark is not supported.
- **On the default bookmark with no work** -- report no feature-bookmark work and stop.
- **Feature bookmark** -- continue.

Note the existing PR URL and body from the PR check if `state: OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local instructions and the repository's `git log` syntax always win. Apply compatible Go quality guidance: use concise imperative wording focused on intent, with motivation or context for non-trivial changes. Derive all prefixes, types, scopes, tickets, emoji, subject forms, capitalization, punctuation, body structure, and other syntax dynamically from those sources. Apply the same discovered style to PR titles where suitable, without imposing change-description-only syntax.

## Step 3: Describe, finalize, and push

If on the default bookmark or no feature bookmark exists, bookmark creation needs to handle a stale local `<base>`, unpushed changes on local `<base>`, and working-copy changes that conflict with the fresh remote base. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, finalize separate changes (2-3 max). Group at file level only by passing explicit filesets to `jj commit`; do not split hunks. When ambiguous, one change is fine.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local instructions and the repository's `git log` syntax always win. Apply compatible Go quality guidance and the dynamic convention from Step 2 while preserving motivation, trade-off, and future-reader context in the repository's established form. Finalize explicit filesets for each group except the final one, then describe the final current change and create a new working-copy change:

```bash
jj commit <files> -m "<message composed from the standards above>"
jj describe -m "<message composed from the standards above>" && jj new
```

Then push:

```bash
jj git push --bookmark <bookmark-name> --allow-new
```

If the working copy has no changes and all finalized changes are already pushed, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. This workflow does not own a dedicated capture flow; current tools may provide browser, screenshot, terminal recording, and artifact capture capabilities. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use the available capture flow and return with the artifact. Do not launch another skill.
3. **Agent judgment on authored changes** — if you authored the changes and know the work is non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the bookmark diff changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved repo root from Context (if it is empty or shows a literal command string, resolve it at runtime with `jj workspace root`) and read `<repo-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments, and the shipped template documents keys as commented examples; matching those would silently flip the gate. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default: **on**. The same read resolves `pr_teaching_archive:` — on only when the active value is exactly `true`, otherwise **off** — and a per-run `archive:on|off` token overrides the archive key for this invocation.

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

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked doc change is left behind. All paths resolve from the pre-resolved repo root in Context, never the CWD. With two taught concepts, write one file per concept and finalize both in a single change. Execute as explicit transitions immediately before the `gh` call:

1. Inspect the repository's applicable ignore rules for `docs/explainers/YYYY-MM-DD-<concept-slug>.md` from the repo root. The orchestrator owns ignore configuration: never edit `.gitignore`. If the path is ignored or cannot be classified safely, print a one-line warning and skip archival entirely, writing nothing.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local instructions and the repository's `git log` syntax always win; apply compatible Go quality guidance and dynamically derive every prefix, type, scope, subject form, capitalization, punctuation, and body structure. Finalize only those file(s) with `jj commit <files> -m "<message composed from the standards above>"`, then run `jj git push --bookmark <bookmark-name>`. If JJ reports no changes to finalize, the doc was already finalized in a prior run -- keep the link and continue.
4. Splice a head-bookmark blob URL per doc into the `## New concepts` section before applying.

If the doc write, change finalization, or push fails, warn and continue to PR creation without the link — never strand the flow between finalization and PR creation.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

---

## Applying via gh

The body **must** be written under `$(jj workspace root)/.tmp` and passed via `--body-file <path>`. If `jj workspace root` fails because this is not a JJ repo, use the local `.tmp` directory. Create the directory, and never edit `.gitignore`; the orchestrator owns it. Never use an OS/global temp directory, `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
REPO_ROOT=$(jj workspace root 2>/dev/null || pwd) && TMP_DIR="$REPO_ROOT/.tmp" && mkdir -p "$TMP_DIR" && BODY_FILE="$TMP_DIR/pr-body-$$.md" && : > "$BODY_FILE" && cat >> "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```

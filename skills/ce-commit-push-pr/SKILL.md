---
name: ce-commit-push-pr
description: Describe changes, create or update a JJ bookmark, push it, and open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off]"
---

# Describe, Push, and Open a PR

Preserve human and research attribution supplied by the project or user. Add no generated-by footer or execution metadata.

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question in chat only when no blocking tool exists on the platform or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no commit/push intent. If no open PR, report and stop. Otherwise run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess).

## Context

Use the pre-populated data below when it resolved successfully. Otherwise run the Context fallback.

**JJ status:**
!`jj status 2>/dev/null || echo 'NO_JJ_WORKSPACE'`

**Working-copy diff:**
!`jj diff 2>/dev/null || true`

**Nearest bookmarks:**
!`jj bookmark list -r 'heads(::@ & bookmarks())' 2>/dev/null || true`

**Recent changes:**
!`jj log --no-graph -r 'latest(::@, 10)' 2>/dev/null || true`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'`

**Existing PR check:**
!`gh pr status --json currentBranch 2>/dev/null || echo 'PR_STATUS_UNRESOLVED'`

**Workspace root (pre-resolved):**
!`jj workspace root 2>/dev/null || pwd`

### Context fallback

```bash
ROOT=$(jj workspace root 2>/dev/null || pwd); printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list -r 'heads(::@ & bookmarks())'; printf '\n=== LOG ===\n'; jj log --no-graph -r 'latest(::@, 10)'; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo 'DEFAULT_BOOKMARK_UNRESOLVED'; printf '\n=== PR_STATUS ===\n'; gh pr status --json currentBranch 2>/dev/null || echo 'PR_STATUS_UNRESOLVED'; printf '\n=== WORKSPACE_ROOT ===\n%s\n' "$ROOT"
```

---

## Step 1: Resolve bookmark and PR state

If the default bookmark is unresolved, ask the user rather than guessing. Fetch it with `jj git fetch --remote origin --branch <default-bookmark>`, then use `<default-bookmark>@origin` as the fresh base.

Bookmark routing:

- **No feature bookmark** — this is normal in JJ. Derive a feature bookmark name from the change content and create it at the final change in Step 3. Do not ask whether to create it; the full workflow already supplies that intent.
- **Nearest bookmark is the default bookmark and there is work to ship** — derive a feature bookmark name and follow `references/bookmark-creation.md`; never push the default bookmark.
- **Nearest bookmark is the default bookmark and there is no work** — report no feature work and stop.
- **Feature bookmark exists in the current change stack** — retain its name and continue. If several bookmarks are plausible, ask which one identifies the PR head.

After resolving the feature bookmark, query `gh pr view <feature-bookmark> --json url,title,body,state`. Note the URL and body when `state` is `OPEN`. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For every JJ change-description or PR-title composition, edit, validation, or recommendation, the project's active runtime instructions take precedence, followed by description syntax and wording observed with `jj log`; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed syntax, prefixes, types, scopes, subjects, bodies, layouts, templates, or examples; use neutral placeholders when discussing variable content.

## Step 3: Describe changes, bookmark, and push

If the nearest bookmark is the default bookmark, the transition needs to handle stale local state and local-only changes without confusing them with the intended feature stack. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan `jj status`, `jj diff`, and the relevant `jj log` range for naturally distinct concerns. If they clearly group into separate logical changes, use `jj split` with explicit filesets to produce at most 2-3 changes. When ambiguous, one change is fine. JJ snapshots the working copy and has no staging step; verify every resulting change with `jj diff -r <change>` and `jj log -r <change>`.

Before composing or editing any JJ description, follow this instruction:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions take precedence, followed by description syntax and wording observed with `jj log`; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed syntax, prefixes, types, scopes, subjects, bodies, layouts, templates, or examples; use neutral placeholders when discussing variable content. Describe each intended change, then review the resulting stack:

```bash
jj describe -r <change> -m '<description-composed-from-runtime-conventions>'
jj log -r '<base>@origin..<head-change>'
```

Create the feature bookmark at `<head-change>`, or move the already-resolved feature bookmark there. Use `jj bookmark create <bookmark> -r <head-change>` for a new name and `jj bookmark move <bookmark> --to <head-change>` for an existing name. Then push that bookmark explicitly:

```bash
jj git push --remote origin --bookmark <bookmark>
```

If `jj status`, the relevant `jj log` range, and `jj bookmark list --all-remotes <bookmark>` show that every intended change is already described and the local and remote bookmarks agree, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — the core principle at the top governs every step. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body and can preserve `Related:` / `Fixes` references already present there.

**Evidence decision** before composition. Treat evidence as user-supplied context or as validation prose, not as a separate skill dispatch.

1. **User supplied evidence** (URL, markdown image/embed, local artifact path they want referenced) — incorporate it into the PR body as `## Demo`, `## Screenshots`, or `## Evidence`, matching the artifact type. Do not invent or upload evidence.
2. **User explicitly asks to include evidence but has not supplied it** — ask for the URL/markdown/path, or tell them to use their available capture flow and return with the artifact. Do not launch another `ce-*` skill.
3. **Agent judgment on authored changes** — if you authored the changes and know they are non-observable (internal plumbing, type-only, backend refactor without user-facing effect, docs/markdown/changelog/CI/test-only, pure refactors), skip evidence handling without asking.

Otherwise, if the bookmark range changes observable behavior (UI, CLI output, API behavior with runnable code, generated artifacts, workflow output), include a concise validation note in the PR body describing what was exercised and how it behaved. If no real run was possible because of unavailable credentials, paid services, deploy-only infrastructure, hardware, or missing local setup, say that plainly in the validation section.

Do not block PR creation solely because no visual artifact exists. Test output and manual validation notes are acceptable validation evidence, but do not label test output as "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the pre-resolved workspace root from Context (if it is empty or shows a literal command string, resolve it at runtime with `jj workspace root`, falling back to the current directory outside JJ) and read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments, and any commented examples do not count. The gate is off only when the active value is exactly `false`; a missing file, missing key, or any other value means the default: **on**. The same read resolves `pr_teaching_archive:` — on only when the active value is exactly `true`, otherwise **off** — and a per-run `archive:on|off` token overrides the archive key for this invocation.

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

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked change is left behind. All paths resolve from the pre-resolved workspace root in Context. With two taught concepts, write one file per concept in a single JJ change. Execute as explicit transitions immediately before the `gh` call:

1. Verify the intended `docs/explainers/<date>-<concept>.md` path against the project's ignore rules. If it is ignored, print a one-line warning and skip archival entirely, leaving no file behind and never forcing the path to be tracked.
2. Run `jj new <bookmark>` to create a fresh change, then write the file (create the directory if needed) with the existing explainer frontmatter fields and the teaching content. If the file already exists from a prior run, overwrite it.
3. Confirm with `jj status` and `jj diff` that only the intended explainer files entered this change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active runtime instructions take precedence, followed by description syntax and wording observed with `jj log`; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed syntax, prefixes, types, scopes, subjects, bodies, layouts, templates, or examples; use neutral placeholders when discussing variable content. Run `jj describe -m '<description-composed-from-runtime-conventions>'`, move the feature bookmark to this change, and run `jj git push --remote origin --bookmark <bookmark>`. If there is no diff, the doc is already present from a prior run; keep the link and continue.
4. Splice a head-bookmark blob URL per doc into the `## New concepts` section before applying.

If the doc write, description, bookmark move, or push fails, warn and continue to PR creation without the link — never strand the flow between the change and PR.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept: `Run /ce-explain <name> to go deeper.` No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

---

## Applying via gh

The body **must** be written under the current JJ workspace's `.tmp/rocketclaw/` directory and passed via `--body-file <path>`. Outside a JJ workspace, use `.tmp/rocketclaw/` under the current directory. Never use OS-global temporary storage, `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
ROOT=$(jj workspace root 2>/dev/null || pwd); BODY_DIR="$ROOT/.tmp/rocketclaw"; mkdir -p "$BODY_DIR"; BODY_FILE="$BODY_DIR/pr-body-<unique-id>.md"; cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```

Run the applicable `gh` command and `rm -f "$BODY_FILE"` in the same shell invocation, preserving the `gh` exit status. Do not leave the body file for a later JJ snapshot.

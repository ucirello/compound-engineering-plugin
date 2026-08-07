---
name: ce-commit-push-pr
description: Describe changes, create or update a Jujutsu bookmark, push it, and open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Change, Bookmark, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question capability. Fall back to a question in chat only when no blocking capability is available or it errors. Never silently skip the question.

## Done

The intended changes are described and published through Jujutsu, GitHub has the requested PR state without duplicate or unintended PRs, and eligible ready PRs have been handed to `ce-babysit-pr`. Description-only and description-update modes are done when the requested body is returned or applied without changing repository state.

## Mode

- **Description-only:** Write a PR description and print it. Apply it only when the user asks. Pass a supplied PR URL or number to Step 4.
- **Description update:** Refresh an existing PR without changing or pushing repository state. Compose in Step 4, then preview and apply through `gh pr edit` in Step 5. An exit-zero empty array from the existing-PR check means no open PR; a non-zero result leaves PR state unknown and must be resolved before proceeding.
- **Full workflow:** Run Steps 1-5. When user intent or a standing preference requires a PR stack, enter Stack mode instead of creating one PR.

**`mode:pipeline` modifier:** Run the selected mode without blocking questions. Keep an existing PR body unless rewriting was requested; description-update mode applies directly because that invocation supplies apply intent. Stop with a residual rather than guessing about unresolved base or topology choices. Pass stack posture to the babysit handoff when applicable.

## Stack mode (opt-in)

Enter stack mode only when user intent or a standing preference requires multiple PRs. An explicit stack request must remain a stack request rather than becoming one PR with a custom base. Do not suggest stacks proactively. When only an artificial split of one logical change is possible and stack intent is not explicit in the current request, use the single-PR path.

Load `references/stack-submit.md` before Step 3. Follow its Probe, Topology, and, when required, Retrospective construction sections there; Step 5 owns submission and post-submit metadata. `gh stack` is a soft dependency: required stack intent stops when unavailable, while soft intent reports the residual and uses one PR.

After a successful ready submit, hand the bottom open non-draft PR to `ce-babysit-pr`. Use `posture:stack-ready` unless land or merge-when-green intent is explicit, in which case use `posture:stack-land`. Draft-only submission is a residual before babysitting unless the user explicitly requested draft watching.

## Context

Run each command as its own shell tool call. Do not join commands with shell operators, pipes, substitutions, or redirects. Interpret each exit status directly. Commands and paths must remain valid in Git Bash; quote paths and do not depend on shell state persisting between calls.

| Command | Purpose | Non-zero exit or empty output |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace; use the current directory only for the local `.tmp` fallback, then report and stop the full workflow |
| `jj status` | Working-copy change and conflicts | Repository state unavailable |
| `jj diff` | Current working-copy diff | No current diff or repository state unavailable |
| `jj bookmark list -r @` | Local bookmarks targeting the current change | Empty is normal: this work is not yet named |
| `jj log -r 'trunk()..@' --limit 10` | Current unpublished lineage and repository-specific description syntax | No changes ahead of trunk or trunk unresolved |
| `jj log -r 'trunk()' --limit 1` | Resolved default remote change and bookmarks | Resolve the default name with `gh repo view` |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for the bookmark exported as a Git head | Run only when one intended feature bookmark is known; exit zero with `[]` means none, non-zero means unknown |

Use the bookmark name only for `gh pr list --head`. Never pass an owner-qualified value. In a fork, target the base repository through normal `gh` repository resolution or `-R <base-owner>/<repo>`. If more than one owner has the same head name, match `headRepositoryOwner` and `headRefName` to the remote this workflow can push; stop if ownership remains ambiguous.

Treat this context as a snapshot. Re-read the intended bookmark and PR state immediately before `jj git push` and `gh pr create`.

## Artifact root

When concept archival is enabled, write explainers under `<root>/explainers/`. Resolve `<root>` once before composing artifact paths.

Read `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml`; do not read it from `config.local.yaml`. An unset value resolves to `docs`. `.gitignore` status does not alter configuration lookup.

Validate a configured value as a workspace-relative directory whose real, symlink-resolved path remains inside the workspace and is neither the workspace root nor under `.git/` or `.jj/`. An invalid value stops archival rather than falling back. Use only the resolved root for artifacts.

## Step 1: Resolve bookmark and PR state

Use `trunk()` as the authoritative default remote change. Derive its remote bookmark name from `jj log -r 'trunk()'`; when unavailable, use `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If neither resolves a default name, ask in interactive mode or return a residual in pipeline mode.

Bookmark routing is determined by whether the intended work is ahead of `trunk()` and has one unambiguous publication identity:

- Work ahead of `trunk()` without a feature bookmark is normal in Jujutsu. Derive a name from the complete change and create it in Step 3 without another confirmation.
- Work identified only by the default bookmark must not publish that bookmark. Resolve safe feature-bookmark creation through `references/branch-creation.md`.
- No work ahead of `trunk()` means there is no feature work to ship.
- Multiple candidate bookmarks require selection by requested work, push remote, and PR identity; ask or stop when that identity remains ambiguous.

An existing-PR query returning a non-empty array is not enough by itself. Match both the head owner and head name to the push target. Step 5 uses the confirmed URL; Step 4 uses the existing body as preservation context.

## Step 2: Determine conventions and compose change descriptions

At every site in this skill and its loaded references that composes, edits, validates, or recommends a JJ change description, the project's active instructions and change-description syntax inferred at runtime from current `jj log` always win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Describe each change according to those present standards. Preserve motivation, constraints, consequences, issue references, and reviewer-relevant context when they are not evident from the diff, adapting syntax dynamically without weakening those semantic requirements. Apply compatible Go guidance only for quality, clarity, and structure. When a plan Implementation Unit ID is already in hand and belongs unambiguously to one change, preserve that association only in the form supported by project instructions or observed history; do not hunt for a plan or invent a suffix. Do not add attribution or sign-off lines. Do not impose or recommend a fixed prefix, type, scope, capitalization rule, subject, body, layout, line limit, suffix, template, or example that project instructions and observed history do not require; use `<description-composed-from-runtime-conventions>` wherever command syntax or prose would otherwise supply one.

## Step 3: Describe, bookmark, and push

If the stack reference constructed the layers, skip the ordinary path and continue to Step 4; Step 5 submits the stack.

If the work is based on the default bookmark or needs a feature bookmark, read `references/branch-creation.md` and follow its decision flow.

Inspect the complete lineage and current diff for coherent concerns. Keep one change when the work is one concern. When whole-file groups are independently coherent, use `jj split <files>` to separate them; do not force hunk-level partitioning without user direction. Files carried in `exclude:<paths>` remain outside every split, description, bookmark move, and publication action.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Describe each resulting change with `jj describe -r <change> -m <description-composed-from-runtime-conventions>`. Use `jj new <parent>` when another child change is required. Stop and report conflicts rather than resolving them without direction.

Create the feature bookmark at the final intended change, or move the confirmed existing feature bookmark there:

```bash
jj bookmark create <bookmark> -r <change>
jj bookmark set <bookmark> -r <change>
```

Run only the applicable bookmark command. Immediately before publication, verify bookmark identity, target, and remote state, then fetch and push through Jujutsu Git interop:

```bash
jj bookmark list <bookmark> --all-remotes
jj git fetch --remote <remote>
jj git push --remote <remote> --bookmark <bookmark> --allow-new
jj new <bookmark>
```

`jj git push` provides remote-state safety. Never bypass a rejected push by abandoning or overwriting unseen remote work. Reconcile after fetching with `jj rebase`, or ask when the correct destination is unclear. If the intended changes are already described, bookmarked at the correct target, and present on the remote, this step is a no-op.

## Step 4: Compose the PR title and body

Read `references/pr-description-writing.md` in full. It owns range resolution, value-first framing, sizing, program altitude, related-work preservation, concept teaching, required project fields, and the pre-apply audit. Pass any known PR URL or number. In Stack mode, Step 5 follows the post-submit route in `references/stack-submit.md`.

Use available capture capabilities or user-supplied artifacts for evidence; never invent or upload evidence. Incorporate supplied evidence in a project-permitted location. If evidence was explicitly requested but not supplied, ask for it or explain how to return it. Changes with no material observable claim need no evidence section. Otherwise state what was exercised and any real limitation without presenting test output as a demo or screenshot.

Resolve ordinary configuration keys from `<workspace-root>/.rocketclaw/config.local.yaml`, then `<workspace-root>/.rocketclaw/config.yaml`; the first active, non-commented valid scalar wins. Empty or invalid scalars continue to the next layer and then the skill default. A present list or map, including an empty one, replaces that key. Missing files are skipped, and `.gitignore` status does not alter resolution. This cascade does not apply to `docs_root`.

An active winning `pr_teaching_section: false` disables concept handling; missing or any other valid value enables it. `pr_teaching_archive` is enabled only by an active winning value of `true`, and `archive:on|off` overrides it for this run. Description-only and description-update modes never write archival files.

Product branding is off unless this invocation includes `branding:on` or the user explicitly asks for that branding in the current prompt. `branding:off` forces it off when `branding:on` is absent. Conflicting tokens are a residual rather than a guessed choice. Pass the resolved choice and whether the PR is new or existing to the reference; branding alone never supplies rewrite intent.

Continue through the reference and run its coverage audit before returning the body.

## Step 5: Apply and report

**Description-only:** Print the title and body, then stop unless asked to apply.

**New PR:** In Stack mode, use the reference's Submit section. Otherwise re-run the exact `gh pr list --head <bookmark>` check immediately before creation. Switch to the existing-PR path if a matching PR appeared. Resolve any non-zero result before creating. Apply with `gh pr create` and report the URL.

**Existing PR:** In Stack mode, submit or synchronize through the reference. Otherwise report the URL and ask whether to rewrite the description. Pipeline mode keeps the body unless rewriting was requested.

**Description update or confirmed rewrite:** Compare title and body with the existing PR. Make no API call when they are identical. Otherwise preview the proposed title, opening, and body length, then apply with `gh pr edit` only when the selected mode supplies apply intent or the user confirms.

**Explainer archival:** Run only in the full workflow when archival is enabled, concept-teaching content was composed, and body application is authorized. Resolve every path from the workspace root.

1. Use the empty child created after the feature push when it is still based directly on the feature bookmark; otherwise start a dedicated child with `jj new <bookmark>`.
2. Write one artifact per taught concept with the project's required artifact metadata and teaching content. A confirmed prior artifact for the same concept may be refreshed; do not overwrite any other pre-existing file without confirmation.
3. Run `jj file track <path>` for only files created by this run. This follows `.gitignore` in colocated repositories; never force ignored content. If ignore policy rejects a path, remove only the new file from this run, warn, and skip archival.
4. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
5. Describe the dedicated change according to the project instructions and `jj log` syntax, move the feature bookmark to it, start a fresh `jj new <bookmark>`, and publish with `jj git push --bookmark <bookmark>`.
6. Generate each link with `gh browse -n -b <bookmark> -- <path>` so GitHub Enterprise hosts work, then place it with the corresponding concept teaching before applying the PR body.

If archival description or publication fails, warn and continue without the link. Do not strand PR creation.

For concept handoffs, default to `/ce-explain <name>` and use `$ce-explain <name>` only on Codex or a host that explicitly documents dollar-prefixed skill invocation. Output one form. When a body applied by this run teaches concepts, report their names after the PR URL and, in an interactive full workflow, add one rendered invocation per concept. Print no concept trailer when no body was applied.

**Babysit handoff:** After creating a ready PR, submitting a ready stack, or publishing new changes to an existing open PR, completion requires `ce-babysit-pr` to own follow-on unless an explicit skip applies. Announce the handoff and invoke it with the PR URL without asking. For a stack, pass the bottom open non-draft PR, the derived posture, and stack-wide scope when pipeline mode requires it. Pipeline mode waits for the babysitter's structured stop result.

Report successful ownership transfer so an outer caller does not start a duplicate babysitter. Do not auto-start in `mode:pipeline` unless this run completed a stack-mode submit; that exception passes stack-wide scope and waits for the structured stop result.

Do not substitute local polling or `gh pr checks --watch`. If `ce-babysit-pr` cannot load or start, report blocked. `babysit:off` skips; `babysit:continuous` and `babysit:checkpoint` force those modes. An active winning `auto_babysit: false` from the ordinary configuration cascade is a standing opt-out.

Do not auto-start babysitting when this run did not publish a ready PR state that the current user can push: description-only/update mode, no PR change, non-GitHub hosting, a draft created or updated by this run, or an unpushable head bookmark. Fork PRs remain eligible when the head remote is pushable. Explicit draft-watch intent still invokes `ce-babysit-pr` with the requested watch mode.

## Applying via gh

Resolve the body-file root by running `jj workspace root` as its own command. On success, use `<workspace-root>/.tmp/rocketclaw/ce-commit-push-pr/`. If it fails in a description-only or description-update flow, use `.tmp/rocketclaw/ce-commit-push-pr/` under the current directory. The fallback is local `.tmp` only; never use an OS-global temporary directory.

Create the directory, reserve a unique `pr-body.XXXXXX` path with `mktemp`, and write the composed body with the native file-writing capability. Keep each path quoted so it works in Git Bash. Pass the resulting path through `--body-file`; never use stdin or command substitution for body transport.

```bash
mkdir -p "<resolved-body-directory>"
mktemp "<resolved-body-directory>/pr-body.XXXXXX"
gh pr create --title "<title>" --body-file "<body-file>"
gh pr edit <pr-ref> --title "<title>" --body-file "<body-file>"
```

Use the composed title verbatim with appropriate shell quoting. Run only the applicable `gh` command.

---
name: ce-commit-push-pr
description: Describe Jujutsu changes, publish a bookmark, and open or update a GitHub PR. Use when asked to ship/open a PR, or for PR-description-only work such as writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Change, Bookmark, Push, and PR

**Asking the user:** Use the host's blocking question capability. Ask in chat only when no blocking capability is available or it errors. Never silently skip a required question.

## Done

The intended changes are described and published through Jujutsu, GitHub has the requested PR state without duplicate or unintended PRs, and each eligible ready PR is owned by `ce-babysit-pr`. Description-only and description-update modes are done when the requested title and body are returned or applied without changing repository state.

## Mode

- **Description-only:** Write and print a PR title and body. Apply them only when the user asks. Pass a supplied PR URL or number to Step 4.
- **Description update:** Refresh an existing PR without changing or pushing repository state. Compose in Step 4, then preview and apply through `gh pr edit` in Step 5. Only an exit-zero empty array from the existing-PR check proves there is no open PR; a non-zero result leaves PR state unknown and must be resolved.
- **Full workflow:** Run Steps 1-5. When current user intent or a standing project preference requires multiple PRs, enter Stack mode instead of creating one PR.

**`mode:pipeline` modifier:** Run the selected mode without blocking questions. Keep an existing PR body unless rewriting was requested; description-update mode applies directly because that invocation supplies apply intent. Stop with a residual rather than guessing about unresolved base, publication identity, or topology choices. Pass stack posture to the babysit handoff when applicable.

## Stack Mode

Enter stack mode only when user intent or a standing preference requires multiple PRs. Preserve an explicit stack request rather than converting it to one PR with a custom base. Do not suggest stacks proactively. When only an artificial split of one logical change is possible and stack intent is not explicit in the current request, use the single-PR path.

Load `references/stack-submit.md` before Step 3. Follow its Probe, Topology, and, when required, Retrospective construction sections there; Step 5 owns submission and post-submit metadata. `gh stack` is a soft dependency: required stack intent stops when unavailable, while soft intent reports the residual and uses one PR.

After a successful ready submit, hand the bottom open non-draft PR to `ce-babysit-pr`. Use `posture:stack-ready` unless land or merge-when-green intent is explicit, in which case use `posture:stack-land`. Draft-only submission is a residual before babysitting unless the user explicitly requested draft watching.

## Context

Run each command as its own shell tool call. Do not join commands with shell operators, pipes, substitutions, or redirects. Interpret each exit status directly. Quote paths and do not depend on shell state persisting between calls.

| Command | Purpose | Non-zero exit or empty output |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace; description-only/update may use the current directory for the local `.tmp` fallback, but full workflow stops |
| `jj status` | Working-copy change, bookmarks, and conflicts | Repository state unavailable |
| `jj diff` | Current working-copy diff | Empty means the working-copy change has no content |
| `jj bookmark list -r @` | Local bookmarks at the current change | Empty is normal: the work is not named yet |
| `jj log -r 'trunk()..@' --limit 20` | Complete unpublished lineage | Empty means no work ahead of trunk; failure means `trunk()` is unresolved |
| `jj log -r 'trunk()' --limit 1` | Candidate default remote change and bookmark identity | A root-only fallback or a change without a matching default remote bookmark is unresolved; resolve it from GitHub and Jujutsu remote state |
| `jj log -r '::@' --limit 20 -T 'description ++ "\n\n"'` | Runtime message syntax and explanatory style | No described history is available; use project instructions and compatible Go guidance only |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for the bookmark exported as a Git head | Run only when one intended feature bookmark is known; exit zero with `[]` means none, non-zero means unknown |

Use the bookmark name only for `gh pr list --head`. Never pass an owner-qualified value. Derive and pass `-R <base-owner>/<repo>` when repository auto-detection is unavailable or points to a fork. If more than one owner has the same head name, match `headRepositoryOwner` and `headRefName` to the remote this workflow can push; stop if ownership remains ambiguous.

Treat this context as a snapshot. Re-read the intended bookmark and PR state immediately before `jj git push` and `gh pr create`.

## Artifact Root

When concept archival is enabled, write explainers under `<root>/explainers/`. Resolve `<root>` once before composing artifact paths.

Read `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml`; do not read it from `config.local.yaml`. An unset value resolves to `docs`. Validate a configured value as a workspace-relative directory whose real, symlink-resolved path remains inside the workspace and is neither the workspace root nor under `.git/` or `.jj/`. An invalid value stops archival rather than falling back. Use only the resolved root for artifacts.

## Step 1: Resolve Bookmark and PR State

Use `trunk()` only when it resolves exactly one non-root change with a matching default remote bookmark. Jujutsu can fall back to `root()` when no default is configured, which is not proof of a GitHub base. Otherwise use `gh repo view --json defaultBranchRef` against the explicitly resolved GitHub repository, then match that name to Jujutsu remote bookmarks. If neither resolves one base, ask in interactive mode or return a residual in pipeline mode. Never guess a fixed default name or remote.

Bookmark routing is determined by whether the intended work is ahead of `trunk()` and has one unambiguous publication identity:

- Work ahead of `trunk()` without a feature bookmark is normal. Derive a name from the complete change and create it in Step 3 without another confirmation.
- Work identified only by the default bookmark must not publish that bookmark. Resolve safe feature-bookmark creation through `references/branch-creation.md`.
- No work ahead of `trunk()` means there is no feature work to ship.
- Multiple candidate bookmarks require selection by requested work, push remote, and PR identity; ask or stop when that identity remains ambiguous.

For a non-empty PR query, match both head owner and head name to the push target. Step 5 uses the confirmed URL; Step 4 uses the existing body as preservation context.

## Step 2: Determine Conventions and Compose Change Descriptions

At every site in this skill and its loaded references that composes, edits, checks, validates, recommends, templates, or exemplifies a JJ change description, the project's active instructions and message syntax inferred at runtime from the full-description `jj log` probe win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Apply only compatible Go guidance for clarity: summarize the change and explain motivation or consequences when useful. Preserve issue references and reviewer-relevant context not evident from the diff. Do not add attribution or sign-offs. Do not impose a fixed prefix, type, scope, capitalization, mood, subject, body, layout, line limit, suffix, trailer, template, or example unless current project instructions or runtime history require it. Use `<message composed from the standards above>` in command forms.

## Step 3: Describe, Bookmark, and Push

If the stack reference constructed the layers, skip the ordinary path and continue to Step 4; Step 5 submits the stack.

If the work is based on the default bookmark or needs a feature bookmark, read `references/branch-creation.md` and follow its decision flow.

Inspect the complete lineage and current diff for coherent concerns. Keep one change when the work is one concern. When whole-file groups are independently coherent, use `jj split <files>` to separate them; do not force hunk-level partitioning without user direction. When the invocation carries `exclude:<paths>`, select only intended files into the publishable parent chain and leave excluded paths in an unbookmarked descendant working-copy change. Verify that no excluded path is in `trunk()..<feature-tip>` before moving the feature bookmark or pushing.

Before composing or checking every resulting description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Describe each resulting change with `jj describe -r <change> -m "<message composed from the standards above>"`. If another child is needed, create it with `jj new <parent>`. Stop and report conflicts rather than resolving them without direction.

Create the feature bookmark at the final intended change, or set the confirmed feature bookmark there. Run only the applicable command:

```bash
jj bookmark create <bookmark> -r <change>
jj bookmark set <bookmark> -r <change>
```

Immediately before publication, verify bookmark identity, target, conflicts, descriptions, private-change policy, and remote state. Fetch before pushing so JJ's remote-lease checks compare against current state:

```bash
jj bookmark list <bookmark> --all-remotes
jj git fetch --remote <remote>
jj git push --remote <remote> --bookmark <bookmark>
jj new <bookmark>
```

Push creates and automatically tracks a new remote bookmark. A rejected push is a stop for reconciliation, never permission to overwrite unseen remote work or bypass JJ's safety checks. Reconcile after fetching with the appropriate `jj rebase` operation, or ask when the destination is unclear. If all intended changes are already described, the bookmark targets the correct change, and that target is present on the remote, this step is a no-op. Create the fresh child only after a successful push and only when `@` is not already an empty child of the published bookmark.

## Step 4: Compose the PR Title and Body

Read `references/pr-description-writing.md` in full. It owns range resolution, value-first framing, sizing, scannability, program altitude, related-work preservation, concept teaching, project-required fields, and the pre-apply audit. Pass any known PR URL or number. In Stack mode, Step 5 follows the post-submit route in `references/stack-submit.md`.

Use available capture capabilities or user-supplied artifacts for evidence; never invent or upload evidence. Incorporate supplied evidence in a project-permitted location. If evidence was explicitly requested but not supplied, ask for it or explain how to return it. Changes with no material observable claim need no evidence section. Otherwise state what was exercised and any real limitation without presenting test output as a demo or screenshot.

Resolve ordinary configuration keys from `<workspace-root>/.rocketclaw/config.local.yaml`, then `<workspace-root>/.rocketclaw/config.yaml`; the first active, non-commented valid scalar wins. Empty or invalid scalars continue to the next layer and then the skill default. A present list or map, including an empty one, replaces that key. Missing files are skipped. This cascade does not apply to `docs_root`.

An active winning `pr_teaching_section: false` disables concept handling; missing or any other valid value enables it. `pr_teaching_archive` is enabled only by an active winning value of `true`, and `archive:on|off` overrides it for this run. Description-only and description-update modes never write archival files.

Continue through the reference and run its coverage audit before returning the title and body.

## Step 5: Apply and Report

**Description-only:** Print the title and body, then stop unless asked to apply.

**New PR:** In Stack mode, use the reference's Submit section. Otherwise re-run the exact `gh pr list --head <bookmark>` check immediately before creation. Switch to the existing-PR path if a matching PR appeared. Resolve any non-zero result before creating. Apply with `gh pr create` and report the URL.

**Existing PR:** In Stack mode, submit or synchronize through the reference. Otherwise report the URL and ask whether to rewrite the description. Pipeline mode keeps the body unless rewriting was requested.

**Description update or confirmed rewrite:** Compare title and body with the existing PR. Make no API call when they are identical. Otherwise preview the proposed title, first two opening sentences, and body line count, then apply with `gh pr edit` only when the selected mode supplies apply intent or the user confirms.

**Explainer archival:** Run only in the full workflow when archival is enabled, concept-teaching content was composed, and body application is authorized. Resolve every path from the workspace root.

1. Use the empty child created after the feature push when it is still based directly on the feature bookmark; otherwise start a dedicated child with `jj new <bookmark>`.
2. Write one artifact per taught concept with the project's required artifact metadata and teaching content. A confirmed prior artifact for the same concept may be refreshed; do not overwrite any other pre-existing file without confirmation.
3. Run `jj file track <path>` only for files created by this run. Never force ignored content. If ignore policy rejects a path, remove only the new file from this run, warn, and skip archival.
4. Before composing, editing, or checking the archival change description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
5. Use `jj describe -m "<message composed from the standards above>"`, set the feature bookmark to the archival change, start a fresh `jj new <bookmark>`, and publish with `jj git push --remote <remote> --bookmark <bookmark>`.
6. Generate each link with `gh browse -R <base-owner>/<repo> -n -b <bookmark> -- <path>` so GitHub Enterprise hosts work, then place it with the corresponding concept teaching before applying the PR body.

If archival description or publication fails, warn and continue without the link. Do not strand PR creation.

For concept handoffs, default to `/ce-explain <name>` and use `$ce-explain <name>` only on Codex or a host that explicitly documents dollar-prefixed skill invocation. Output one form. When a body applied by this run teaches concepts, report their names after the PR URL and, in an interactive full workflow, add one rendered invocation per concept. Print no concept trailer when no body was applied.

**Babysit handoff:** After creating a ready PR, submitting a ready stack, or publishing new changes to an existing open PR, completion requires `ce-babysit-pr` to own follow-on unless an explicit skip applies. Announce the handoff and invoke it with the PR URL without asking. For a stack, pass the bottom open non-draft PR, the derived posture, and stack-wide scope when pipeline mode requires it. Pipeline mode waits for the babysitter's structured stop result.

Report successful ownership transfer so an outer caller does not start a duplicate babysitter. Do not auto-start in `mode:pipeline` unless this run completed a stack-mode submit; that exception passes stack-wide scope and waits for the structured stop result.

Do not substitute local polling or `gh pr checks --watch`. If `ce-babysit-pr` cannot load or start, report blocked. `babysit:off` skips; `babysit:continuous` and `babysit:checkpoint` force those modes. An active winning `auto_babysit: false` from the ordinary configuration cascade is a standing opt-out.

Do not auto-start babysitting when this run did not publish a ready PR state that the current user can push: description-only/update mode, no PR change, non-GitHub hosting, a draft created or updated by this run, or an unpushable head bookmark. Fork PRs remain eligible when the head remote is pushable. Explicit draft-watch intent still invokes `ce-babysit-pr` with the requested watch mode.

## Applying via gh

Resolve the body-file root by running `jj workspace root` as its own command. On success, use `<workspace-root>/.tmp/rocketclaw/ce-commit-push-pr/`. If it fails in a description-only or description-update flow, use `.tmp/rocketclaw/ce-commit-push-pr/` under the current directory.

Generate a fresh high-entropy `<run-id>`, reserve its private subdirectory with `mkdir` (retry with a new ID on collision), and write the composed body to `pr-body.md` there with the native file-writing capability. Pass that path through `--body-file`; never use stdin, a pipe, or command substitution for body transport.

```bash
mkdir -p "<resolved-body-directory>"
mkdir -m 700 "<resolved-body-directory>/<run-id>"
gh pr create -R <base-owner>/<repo> --head <head-owner>:<bookmark> --base <base> --title "<runtime-composed-title>" --body-file "<body-file>"
gh pr edit <pr-ref> -R <base-owner>/<repo> --title "<runtime-composed-title>" --body-file "<body-file>"
```

Use the runtime-composed title verbatim with appropriate shell quoting. Run only the applicable `gh` command. Remove the body file after the `gh` call succeeds or fails; leave the skill-owned directory in place.

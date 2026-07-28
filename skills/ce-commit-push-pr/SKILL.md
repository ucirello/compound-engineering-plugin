---
name: ce-commit-push-pr
description: Describe and publish Jujutsu changes, then open or update a PR. Use when asked to ship/open a PR, or for PR-description-only flows such as writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Describe, Push, and Open a PR with Jujutsu

**Asking the user:** When this skill says "ask the user", use the platform's blocking question capability. Fall back to presenting the question in chat only when no blocking capability exists or the call errors. Never silently skip the question.

## Mode

- **Description-only** - the user wants only a description ("write/draft a PR description", "describe this PR", or a pasted PR URL/number alone). Run Step 4 only and print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the correct range.
- **Description update** - the user wants to refresh an existing PR description without publishing changes. Only an exit-0 `[]` from the existing-PR check means "no open PR"; a non-zero check is unknown, so resolve `gh auth status` or connectivity first. With an open PR, run Step 4 in PR mode, then Step 5 to preview, confirm, and apply with `gh pr edit -R <repo>`.
- **Full workflow** - otherwise, run Steps 1-5 in order.

**`mode:pipeline` modifier** - run the resolved mode non-interactively and suppress every blocking ask. The existing-PR rewrite defaults to not rewriting. Description-update mode applies directly because that invocation supplies apply intent. Any other suppressed ask takes its conservative documented default; if the base or publication target cannot be resolved, stop rather than guess.

## Context

Gather context by running each command as its own shell tool call. Read each exit status directly; a non-zero exit is a state to interpret, not one to suppress.

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace - report and stop |
| `jj status` | Working-copy and conflict state | Not a Jujutsu workspace |
| `jj diff` | Current change content | Empty output means the working-copy change has no content |
| `jj log -r '::@' -n 10` | Recent description style and ancestry | No usable local history |
| `jj bookmark list -r @` | Bookmarks exactly at the working-copy revision | Empty output is normal; Jujutsu work does not require a bookmark until publication |
| `jj bookmark list --all-remotes` | Local and remote bookmark state | Remote state is unavailable |
| `gh repo view -R <repo> --json defaultBranchRef --jq '.defaultBranchRef.name'` | Repository default bookmark name | Resolve from tracked remote bookmarks; if still ambiguous, stop |
| `gh pr list -R <repo> --head <bookmark> --state open --json number,url,title,body,state,headRefName,headRepositoryOwner` | Open PR for the publication bookmark; run only after `<bookmark>` is known | Exit 0 with `[]` means no open PR. Non-zero means PR state is unknown |

Before any repository-scoped `gh` operation, resolve `<repo>` in `[HOST/]OWNER/REPO` form from an explicit PR URL or the applicable base remote reported by `jj git remote list`; verify it with `gh repo view -R <repo>`. Do not rely on GitHub CLI discovering repository metadata from the workspace. Use `-R <repo>` on every `gh repo`, `gh pr`, and `gh browse` command that supports it. When a `gh` operation still needs local repository context, prefix that same shell call with `GIT_DIR="$(jj git root)"`; do not export it for later calls.

Resolve one `<remote>` dynamically from `jj git remote list`: the remote for the writable publication repository whose owner must match the PR head owner. Do not assume its name. If no remote or multiple remotes match, ask the user; in pipeline mode, stop. Carry this same `<remote>` through every fetch, remote bookmark reference, normal or archival push, and the bookmark-creation reference.

Pass only the bookmark name to `gh pr list -R <repo> --head`. For a fork, `<repo>` is the base repository, while `headRepositoryOwner` must match the publication remote owner. Never select index 0 blindly: match both `headRefName` and `headRepositoryOwner` to the publication target, and stop on unresolved ambiguity.

Everything gathered here is a snapshot. Recheck the bookmark, remote, and open-PR state immediately before publication and PR creation.

---

## Step 1: Resolve the base, publication bookmark, and PR state

Resolve the default bookmark with `gh repo view -R <repo>`; if unavailable, inspect tracked remote bookmarks and choose only an unambiguous repository default. Do not assume a fixed name.

Jujutsu does not require the working copy to be attached to a bookmark. Resolve the publication target as follows:

- **Existing feature bookmark in the current stack** - identify it with `jj log -r 'heads(::@ & bookmarks())'` and use it only when its ancestry and remote owner match this work.
- **Current change or stack has work but no feature bookmark** - derive a non-conflicting bookmark name from the change content. Defer creation until Step 3, when the final publishable revision is known.
- **Working copy is exactly the default bookmark with no unpublished work** - report that there is no feature work and stop.
- **Work is based directly on the default bookmark** - read `references/bookmark-creation.md` before Step 3. Publishing the default bookmark directly is unsupported.

If a matching open PR exists, retain its URL and body for Steps 4-5. If the PR check exits non-zero, keep PR state unknown and resolve authentication or connectivity before any create action.

## Step 2: Determine message conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Read the project's active instructions and run `jj log -r '::@' -n 10 --no-graph -T 'description ++ "\n"'` at runtime. Those sources define the present standards and override the sentence above; apply only compatible Go quality guidance. Determine the message shape from that evidence; do not impose a prefix, type, scope, template, capitalization rule, or fixed wording.

## Step 3: Describe changes and publish the bookmark

If the work is based directly on the default bookmark, pass `<remote>` to `references/bookmark-creation.md` and follow its fetch, selection, and rebase flow first.

Review `jj status`, `jj diff`, and the unpublished stack with `jj log -r 'remote_bookmarks()..@'`. Jujutsu snapshots the working copy, so there is no staging step.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For every split, squash, or description message, reapply the project's active instructions and the runtime output of `jj log -r '::@' -n 10 --no-graph -T 'description ++ "\n"'`. They win over the sentence above; use only compatible Go guidance.

If the current change contains clearly separate concerns, use `jj split <filesets> -m "<message composed from the standards above>"` to separate at file level, with at most three publishable changes. Use `jj squash -m "<message composed from the standards above>"` when a split or pre-existing change should be folded into its intended parent and the resulting description must represent the combined contents. When grouping is ambiguous, retain one change.

Describe each resulting change with repository-derived wording while preserving required issue references, semantic scope, and actual contents. Supply `-r <revision>` when describing an earlier result of a split:

```bash
jj describe -r <revision> -m "<message composed from the standards above>"
```

After the last described content change, run `jj new` so the working copy is an empty change above the publishable head.

**Hard conflict gate:** Immediately before any bookmark create or move and before each push, run `jj status` and `jj resolve --list` as separate shell calls. If either reports conflicts, stop before moving the bookmark or pushing. Tell the user that Jujutsu has no continue step: resolve the files and squash the resolution into the intended change if needed, then rerun both checks. Proceed only when both report no conflicts.

Create or move the feature bookmark to `@-`:

```bash
jj bookmark create <bookmark> -r @-
```

If it already exists, use `jj bookmark move <bookmark> --to @-`; do not create a duplicate. Recheck `jj status`, `jj diff`, `jj log -r '<bookmark>@<remote>..<bookmark>'`, and `jj bookmark list <bookmark> --all-remotes`. Apply the hard conflict gate again, then publish only that bookmark:

```bash
jj git push --remote <remote> --bookmark <bookmark>
```

If there is no new content and the bookmark already points to the intended published head, this step is a no-op.

## Step 4: Compose the PR title and body

**Read `references/pr-description-writing.md` in full.** In full workflow, pass the `<remote>` resolved in Step 1 unchanged. In a standalone description mode, let the reference resolve `<remote>` once. Pass the PR ref when mode dispatch identified one. If Step 1 found an existing PR, pass its URL so PR mode preserves existing related references and user-supplied evidence.

Treat evidence as user-supplied context or validation prose:

1. Incorporate supplied URLs, embeds, or requested artifact paths under a heading appropriate to the artifact. Do not invent or upload evidence.
2. If the user explicitly requests evidence but supplied none, ask for it or direct them to the active harness's capture capability.
3. If authored changes make no reviewer-relevant behavioral claim, skip evidence handling. Classify by runtime purpose, not extension.
4. For behavior a reviewer must verify, include a concise note describing what was exercised and observed. State plainly when credentials, services, infrastructure, hardware, or setup prevented a real run.

Do not block PR creation solely because no visual artifact exists. Never label test output as a demo or screenshot.

Read `<workspace-root>/.rocketclaw/config.local.yaml` with the native file-read tool. Only active, non-commented keys count:

- `pr_teaching_section: false` disables concept handling; missing or any other value means on.
- `pr_teaching_archive: true` enables archival; missing or any other value means off.
- `archive:on|off` overrides the archival setting for this invocation.

When teaching is on, follow Step B2 of the reference. When it is off, skip concept judgment, the section, archival, and the Step 5 trailer and offer.

Continue through the reference's composition and pre-apply coverage audit.

## Step 5: Apply and report

**Description-only** - print the title and body, then stop unless the user asks to apply.

**New PR candidate** - immediately re-run `gh pr list -R <repo>` for the live publication bookmark. Resolve a non-zero result before proceeding. If a matching PR appeared, switch to the existing-PR path. Otherwise retain new-PR state; do not create it yet.

**Existing PR after publication** - report the URL and ask whether to rewrite the description. In pipeline mode, default to no rewrite.

**Description update or confirmed rewrite** - compare the proposed title and body with the existing PR. If identical and no explainer archival is pending, do not call `gh pr edit -R <repo>`.

Before applying a changed title or body, preview the title, its character count, the first two summary sentences, and total body lines. Ask whether to apply unless the active mode already supplies apply intent. If declined, accept focus text for regeneration and do not apply.

**Explainer archival** runs only in full workflow when archival is on, a `## New concepts` section was composed, and body application is confirmed. Complete it before the single PR create or edit so the applied body contains every available archival link. Resolve every path from the workspace root.

1. Check the project's active ignore rules for each proposed `docs/explainers/YYYY-MM-DD-<concept-slug>.md` path. If ignored, warn and skip archival without overriding the rule.
2. Write one file per concept with YAML frontmatter `title`, `date`, `input_shape: concept`, and `subject`, followed by the teaching content. Reuse an existing path from a prior run.
3. Review the new content with `jj status` and `jj diff`.
4. Read the project's active instructions and run `jj log -r '::@' -n 10 --no-graph -T 'description ++ "\n"'`; those sources win and only compatible Go guidance from https://go.dev/wiki/CommitMessage applies. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
5. Describe the archival change with `jj describe -m "<message composed from the standards above>"`. Apply the hard conflict gate, move the publication bookmark to `@`, run `jj new`, apply the gate again, then `jj git push --remote <remote> --bookmark <bookmark>`. If there is no content change, retain the existing link and continue.
6. Use `gh browse -R <repo> -n -b <bookmark> -- <path>` to obtain host-correct blob URLs and splice them into the concept section before applying.

If writing, describing, or publishing the archival change fails, warn and continue PR application without the link.

After archival has produced its URLs, been skipped, or taken its failure path, apply the final title and body exactly once:

- **New PR** - create with `GIT_DIR="$(jj git root)" gh pr create -R <repo>` as described below and report its URL.
- **Existing PR** - compare the final title and body, including any archival links, with the existing PR. If identical, do not edit it; otherwise apply one `gh pr edit -R <repo>`.

For user-runnable concept handoffs, default to `/ce-explain <name>`; use `$ce-explain <name>` only when the active host is Codex or explicitly documents that form. Output exactly one form. After an applied body containing `## New concepts`, print `New concepts: <name>[, <name>]` and, in interactive full workflow, one invocation per concept.

In interactive full workflow, auto-invoke `ce-babysit-pr` after a newly created PR or newly published changes on an existing open PR. `babysit:off` skips it; `babysit:continuous` and `babysit:checkpoint` force the corresponding mode. An active `auto_babysit: false` in `.rocketclaw/config.local.yaml` is a standing opt-out, and a run token overrides config.

Do not invoke babysitting for pipeline, description-only, description-update, no applied PR change, non-GitHub hosting, or a head bookmark the user cannot publish. Fork PRs remain eligible when this workflow can publish their head bookmark. A checkpoint-only harness runs one tick and prints the resume invocation.

---

## Applying via gh

Write the body verbatim to `$(jj workspace root)/.tmp/ce-pr-body-<unique-id>.md`; if workspace-root resolution fails after context was gathered, use local `.tmp/ce-pr-body-<unique-id>.md`. Create `.tmp` when absent. Use the native file-writing tool so body content is not expanded by a shell, and never use stdin to supply the body.

```bash
WORKSPACE_ROOT=$(jj workspace root)
```

Then apply with the resolved file path and repository. Supply the resolved base and head explicitly; for a fork, `<head>` is `<head-owner>:<bookmark>`, otherwise it is `<bookmark>`:

```bash
GIT_DIR="$(jj git root)" gh pr create -R <repo> --base <base> --head <head> --title "<composed title>" --body-file "<body-file>"
gh pr edit -R <repo> <ref> --title "<composed title>" --body-file "<body-file>"
```

If a required identity field cannot be omitted, use `ai:assistant` for protocol data or `AI Assistant` for display text. Add no optional identity metadata.

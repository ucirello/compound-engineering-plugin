---
name: ce-commit-push-pr
description: Commit JJ changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability. Fall back to chat only when no such tool is listed or a real question call errors, and never silently skip a required question.

## Outcome and modes

The full workflow finishes when the intended JJ changes are described, a feature bookmark points to the published change, that bookmark is pushed to the selected Git remote, the correct GitHub PR is created or updated, and required follow-on has an owner. Stop before an external write whenever repository, remote, bookmark, PR, or authorization state is unresolved.

- **Description-only:** compose and print a title and body for the supplied PR ref or current change range. Apply only when asked.
- **Description update:** resolve an existing PR, compose from its exact range and body, then preview, confirm, and apply with `gh pr edit`. Exit-0 `[]` means no open PR; non-zero means unknown and blocks mutation.
- **Full workflow:** run Steps 1-5. Enter Stack mode only when intent or standing preference wants a stack.

**`mode:pipeline`:** run non-interactively. Conservative unresolved decisions stop rather than guess; do not rewrite an existing PR unless requested; apply a requested description update directly after preview generation. Stack mode uses only supplied intent and scope and passes posture into the handoff.

## Stack mode

Enter only for explicit intent or a standing preference for multiple PRs. An explicit stack request cannot be converted into a single PR with a custom base. Do not proactively suggest stacks, and do not create artificial layers for one logical change unless the user explicitly required a stack.

Read `references/stack-submit.md` before Step 3. It owns topology, JJ-to-`gh stack` interop, retrospective construction, submission, and residuals. Step 5 owns submission and handoff posture: `posture:stack-ready` by default or `posture:stack-land` only on explicit land intent, starting from the bottom open non-draft PR.

## Step 1-2: Context and conventions

Read `references/context.md` before acting. It owns the argv-only probe table, exit meanings, GitHub fork matching, default-bookmark resolution, and PR detection. Every `jj` and `gh` probe is a separate argv-form shell call; treat exit status as control flow. Re-verify workspace, bookmark, remote, and PR state immediately before push or PR creation.

Only exit-0 `[]` from a query against the base repository proves no open PR. For fork heads, target the base repository with `-R` and query the bookmark name only. Match both head owner and name; ambiguous matches block mutation.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime project instructions and the syntax visible in recent history win. Use only compatible Go guidance: make the first line a concise summary of the change, use the body to explain motivation and behavior when needed, and do not impose Go-specific package naming on a project that uses another convention. Do not assume a fixed prefix, type, scope, subject form, or body template.

## Artifact root

When archival is enabled, resolve `<root>` once and write explainers only under `<root>/explainers/`.

- Read `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml`, where `<workspace-root>` comes from `jj workspace root`. Unset means `docs`.
- A configured value must be a workspace-relative directory whose resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or the colocated `.git/`. Invalid values stop; never silently fall back.
- Create the selected root if absent and do not also read or write the default root.

## Step 3: Describe changes and push

Read `references/commit-and-push.md`. It owns fileset grouping, change descriptions, feature-bookmark placement, and `jj git push`. When the publish base needs resolution, `references/branch-creation.md` owns the safe remote-base decision. If stack construction already described every retrospective layer, continue to Step 4; Step 5 submits the stack.

`exclude:<paths>` is a strict fileset boundary. Those paths remain in the working-copy change, are never included in a described change or pushed bookmark, and are named in the report.

## Step 4: Compose the PR title and body

Read `references/pr-description-writing.md` in full, then `references/compose.md`. They own range evidence, project-template compliance, related-reference preservation, teaching gates, neutral actor fields, and the pre-apply audit. Pass an existing PR URL so composition preserves its body where required.

## Step 5: Apply and report

Read `references/apply-and-handoff.md`. Immediately before `gh pr create`, repeat the existing-PR query and route by its result: matching PR updates, exit-0 `[]` creates, and non-zero blocks. Pass bodies through a workspace-local file with `--body-file`; never use stdin.

The run is not complete after a new PR, a stack submit, or new changes on an open PR until `ce-babysit-pr` owns follow-on, unless `babysit:off`, the winning `auto_babysit: false` setting, or a documented do-not-fire condition applies. Do not substitute another watcher. If the skill cannot load or start, report the handoff as blocked.

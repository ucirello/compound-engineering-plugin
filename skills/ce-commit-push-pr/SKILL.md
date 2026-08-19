---
name: ce-commit-push-pr
description: Commit changes with Jujutsu, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Commit, Push, and PR

**Done:** the requested description is returned or applied, or the selected changes are described, the intended bookmark is pushed, the correct GitHub PR is created or updated, and follow-on ownership is transferred when required. Any unresolved repository, authentication, topology, conflict, or authority state is reported instead of guessed.

**Asking the user:** When this skill says "ask the user", use the platform's blocking question capability. Fall back to the host's user-visible chat surface only when no blocking capability exists or it errors. Never silently skip the question.

## Mode

- **Description-only:** The user wants only a description. Run Step 4 and print the result. Apply only if asked. Pass a supplied PR ref to Step 4.
- **Description update:** The user wants an existing PR's description rewritten without committing or pushing. Only exit 0 with `[]` from the existing-PR check means no open PR. A non-zero result means PR state is unknown; resolve `gh auth status` or connectivity first. Run Step 4 with the PR URL, then preview and apply through Step 5.
- **Full workflow:** Otherwise run Steps 1-5 in order. Enter Stack mode only when user intent or a standing preference requires a stack.

**`mode:pipeline`:** Run non-interactively. Do not rewrite an existing PR unless the invocation requests it. A description-update invocation supplies apply intent. Other suppressed choices take the conservative route: preserve the current bookmark topology, and stop rather than guessing a base, partition, or PR identity.

## Stack Mode

Stack mode is opt-in. An explicit stack request must remain a stack request; do not reinterpret it as one PR with a custom base. Do not proactively suggest stacks, and do not manufacture a stack from one logical change unless the user explicitly required one.

Load `references/stack-submit.md` before Step 3. Before Step 3, use only its Probe, Topology, and Retrospective construction sections. Step 5 owns submission and post-submit PR metadata. `gh stack` is a soft dependency: required stack intent plus an unavailable command is a blocker; soft intent falls back to one PR with the residual reported.

After a successful ready submission, hand the bottom open non-draft PR to `ce-babysit-pr`. Use `posture:stack-ready` unless merge/land intent was explicit, in which case use `posture:stack-land`. Draft-only submission remains a residual when babysitting is on.

## Context

Run each command as its own shell call and read its exit status. Do not join commands with shell operators.

| Command | Purpose | Non-zero exit / empty output |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace: report and stop |
| `jj status` | Working-copy change and conflict state | Repository unavailable |
| `jj diff -r @` | Current change content | Empty means no content in `@` |
| `jj bookmark list -r @` | Bookmarks exactly at the current change | Empty means the change has no bookmark |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent description style and topology | No usable history |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | GitHub default branch | Resolve from tracked remote bookmarks or ask |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for the head bookmark | Exit 0 with `[]` means none; non-zero means unknown |

Run the PR check only after `<bookmark>` is known. Pass the bookmark name only. In a fork checkout, target the base repository with `-R <base-owner>/<repo>` when default repository resolution points at the fork. Match `headRepositoryOwner` and `headRefName` to the head being pushed; never select array index 0 when same-named fork bookmarks make the result ambiguous.

The snapshot is advisory. Recheck the bookmark, remote state, and open PR immediately before push or PR creation.

## Artifact Root

When concept archival is on, write explainers under `<root>/explainers/`. Resolve `<root>` once.

- Read `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml`. Unset means `docs`.
- Require a repo-relative directory whose real path remains inside the workspace and is neither the workspace root nor under `.jj/` or `.git/`. Invalid values are blockers, not a reason to fall back.
- Use `<root>` as the only artifact root and create it when needed.

## Step 1: Resolve Bookmark and PR State

Resolve the default branch with `gh repo view`; if unavailable, use the unambiguous tracked remote bookmark that represents the remote default, otherwise ask. The corresponding Jujutsu remote bookmark is `<base>@<remote>`.

Bookmark routing:

- **No feature bookmark with work to ship:** derive a non-conflicting feature bookmark from the change outcome. If the working change is based on the default line, follow `references/branch-creation.md`; otherwise create the bookmark at the intended head with `jj bookmark create <bookmark> -r <head>`.
- **Default bookmark with work:** follow `references/branch-creation.md`. Pushing the default bookmark directly is not supported.
- **Default bookmark with no feature work:** report that there is nothing to ship and stop.
- **Feature bookmark:** continue.

If the PR query returns candidates, select only a candidate whose owner and head name identify the bookmark this workflow can push. Ambiguity is a blocker. Preserve its URL and body for Steps 4-5.

## Step 2: Determine Description Conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and observed repository history always win. Apply compatible Go clarity and structure guidance so each description communicates the change's effect and material motivation or consequences without restating the patch. Do not impose fixed syntax or examples.

## Step 3: Select Changes, Describe, and Push

If stack construction already described retrospective layers, skip the ordinary path; Step 5 submits the stack.

If the change starts from the default line, read and follow `references/branch-creation.md`. Then inspect the complete current change. Distinct concerns may become 2-3 descriptions; otherwise keep one. Prefer whole-file filesets. Use `jj split -i` only when the requested partition genuinely requires hunk-level selection and the user has approved that boundary.

Jujutsu snapshots tracked working-copy content into `@`; it has no staging index. Select exactly each logical group with filesets:

```bash
jj commit -m "<description derived from local standards and history>" <fileset>...
```

With filesets, the selected content remains in the described change and unselected content moves to the new working-copy child. Honor `exclude:<paths>` by never selecting those paths. Verify each resulting change with `jj show <revision>` and verify excluded content remains outside the described revisions. If a plan Implementation Unit ID is already in hand for a change, append its U-ID in parentheses; do not search for a plan.

After the final selected change, point the feature bookmark at the described tip, not at an empty or excluded-content working-copy child:

```bash
jj bookmark set <bookmark> -r <described-tip>
jj git fetch --remote <remote>
jj rebase -b <bookmark> -o <base>@<remote>
jj git push --remote <remote> --bookmark <bookmark>
```

Rebase only after confirming the fetched base is the intended destination and inspecting the exact branch closure `(<base>@<remote>..<bookmark>)::`. Proceed with `-b` only when every revision in that closure belongs to this feature line. A revision targeted by an unrelated local bookmark, edited by another workspace, or otherwise outside the intended line is an unsafe descendant: stop, or isolate the selected work onto a dedicated change/bookmark and recompute the closure before rebasing. Stop on conflicts or bookmark divergence and report the state; do not push conflicts or resolve them by discarding content. A clean change whose bookmark already matches the remote makes this step a no-op.

## Step 4: Compose the PR Title and Body

Read `references/pr-description-writing.md` in full. Pass any resolved PR URL so it can preserve existing body content and derive the exact range. Stack mode composes each newly created PR against its immediate parent after submission.

Evidence policy:

- Incorporate user-supplied evidence under an appropriate evidence heading.
- If evidence was requested but not supplied, ask for it or state how the user can provide it.
- Skip evidence for changes with no material observable claim.
- Otherwise state what was exercised and any material validation limitation. Do not invent or upload evidence, and do not label test output as a demo or screenshot.

Resolve ordinary configuration keys from `<workspace-root>/.rocketclaw/config.local.yaml`, then `<workspace-root>/.rocketclaw/config.yaml`. The first active valid scalar wins; a present list or map replaces the lower layer. `docs_root` remains tracked-config-only.

`pr_teaching_section` is off only when the winning active value is exactly `false`; otherwise it defaults on. `pr_teaching_archive` is on only when exactly `true`; `archive:on|off` overrides it. When teaching is on, use Step B2 of the reference. When off, omit concept judgment, sections, trailers, and archival.

## Step 5: Apply and Report

- **Description-only:** print title and body; stop unless asked to apply.
- **New PR:** immediately rerun the exact open-PR query for the live bookmark and owner. Resolve non-zero status before creating. If none exists, apply with `gh pr create --head <bookmark>`; otherwise switch to the existing-PR route.
- **Existing PR after push:** report its URL and ask whether to rewrite unless pipeline mode has selected the conservative no-rewrite default.
- **Description update or confirmed rewrite:** skip `gh pr edit` when title and body are unchanged. Otherwise preview title, opening, and body length, ask to apply when interactive, then edit the explicit PR URL.
- **Stack:** follow the Submit section of `references/stack-submit.md`, report the bottom open non-draft PR, and perform the babysit handoff.

### Explainer Archival

Archive only in full workflow when enabled, a `## New concepts` section exists, and body application is confirmed. Resolve every path from the workspace root. If `jj file list -r @ <path>` or the project's ignore rules show the destination cannot be tracked, warn and skip without forcing it.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and observed repository history always win. For the archival change, apply compatible Go clarity and structure guidance from Step 2 and communicate the teaching artifact's purpose without imposing fixed syntax or examples.

Write one explainer per concept with the existing explainer schema. Select only those paths with `jj commit -m "<description derived from local standards and history>" <explainer-filesets>...`, move the feature bookmark to that described tip, rebase it onto the fetched base if needed, and push it with `jj git push --remote <remote> --bookmark <bookmark>`. Splice host-correct blob links obtained through `gh browse -n -b <bookmark> -- <path>` before applying the PR body. If writing, describing, or pushing archival fails, warn and continue without links.

### Follow-On Ownership

When this run applies a body containing `## New concepts`, report the concept names. In interactive full workflow, tell the user to invoke `ce-explain <name>` through the active harness's callable skill mechanism.

After a new PR, stack submission, or newly pushed changes on an existing open PR, completion requires `ce-babysit-pr` to start unless an explicit skip applies. Announce the transfer and invoke it with the PR URL. Pass stack posture and stack-wide pipeline scope when applicable. In pipeline mode, wait for its structured stop result.

Skip automatically for description-only/update, no PR changed this run, non-GitHub hosts, a draft PR unless an explicit watch mode forces it, or a head bookmark this workflow cannot push. `babysit:off` is an explicit per-run skip. `auto_babysit: false` in the layered `.rocketclaw` config is a standing opt-out. If the skill cannot be loaded or started, report blocked rather than substituting an ad-hoc watcher.

## Applying via `gh`

Write the body under the Jujutsu workspace's `.tmp`; if `jj workspace root` is unavailable in a description-only context, use the current directory's `.tmp`. Create the directory, use a collision-resistant file name, and pass it through `--body-file`. Do not use stdin or an OS temp API/path.

```bash
WORKSPACE_ROOT="$(jj workspace root)"
if [ -z "$WORKSPACE_ROOT" ]; then WORKSPACE_ROOT="."; fi
BODY_DIR="$WORKSPACE_ROOT/.tmp"
mkdir -p "$BODY_DIR"
BODY_FILE="$BODY_DIR/pr-body-<unique-token>.md"
```

Write the composed body verbatim without shell expansion, then run the applicable explicit command:

```bash
gh pr create --head "<bookmark>" --title "<title>" --body-file "$BODY_FILE"
gh pr edit "<pr-url>" --title "<title>" --body-file "$BODY_FILE"
```

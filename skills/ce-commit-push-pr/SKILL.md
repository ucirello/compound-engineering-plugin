---
name: ce-commit-push-pr
description: Describe JJ changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Change, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to the chat surface only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Apply it only if asked. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — refresh or rewrite an existing PR's description, with no commit or push intent. Resolve PR presence by the Context rule below: an exit-0 `[]` is "no open PR" (report it and stop), and a non-zero exit is **unknown** (resolve auth or connectivity, then stop until presence is known). **With an open PR**, run Step 4 in PR mode on that URL, then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run the resolved mode non-interactively and suppress every blocking ask; each takes the conservative default: no existing-PR rewrite, the bookmark kept, an unresolvable base stopping rather than guessed, and a description-update preview applied directly, since that invocation is the apply intent. Pipeline stack mode uses only the intent and scope on the invocation and passes posture into the handoff.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` **before Step 3** and follow only its probing, topology, and retrospective construction; that layer-by-layer commit flow replaces ordinary Step 3. **Do not submit there.** Step 5 owns submission, the `gh stack` CLI dependency and residuals, and the handoff posture: `posture:stack-ready` by default, `posture:stack-land` only on explicit land intent, from the **bottom open non-draft** PR. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` before Step 1.** It owns the command table, exit-code meanings, fork handling, and bookmark and PR resolution Steps 1-2 use. A working-copy change does not need a bookmark until publication. Before pushing, create or move a feature bookmark to the completed change; never push the default bookmark directly.

Three rules govern the run.

**Every `jj` and `gh` probe is its own argv-form call**, gathering and re-verification alike, and its exit status is control flow. The reference gives the reason and names the compound recipes this skill pins.

**Probe output is a snapshot.** Re-verify bookmark, remote, and PR state right before each consequential action: Step 3's push and Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork workspace, target the base with `-R` and pass the bookmark name only, since `--head <owner>:<bookmark>` silently returns `[]`. With results, do not blindly take index 0: match head owner and bookmark, and stop on an ambiguous match. Note the URL and body from that entry; Step 5 routes on the URL and Step 4 rewrites the existing body.

## Artifact Root

Resolve `<root>` once when archival is on: it writes an explainer under `<root>/explainers/`.

<!-- rocketclaw-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value; never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- rocketclaw-docs-root:end -->

## Step 3: Commit and push

**Read `references/commit-and-push.md`** for bookmark creation, change grouping, description mechanics, and push. Creating work from the default bookmark is the fragile case; `references/bookmark-creation.md` owns fresh-base and local-divergence handling. If the stack reference already constructed retrospective layers, skip to Step 4; `gh stack submit` pushes in Step 5.

Two rules bound this step. Use explicit JJ filesets for each completed change so `.env`, build, generated, excluded, or unrelated files cannot ride along. Honor `exclude:<paths>`: those files remain in the working-copy change and the report says so.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full. It owns the title and body content rules, including preserving an existing `Related:` or `Fixes` reference on rewrite. Then read **`references/compose.md`** for the evidence and teaching gates. `pr_teaching_section` defaults on, `pr_teaching_archive` defaults off, and only an active non-commented key changes either.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for the apply routes, preview-before-edit, archival, and handoff. Two rules bound the external writes. Re-run the existing-PR check right before `gh pr create` and route on it: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. And pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**The completion gate is here.** In an interactive full workflow, or in `mode:pipeline` when this run submitted a stack, a reported PR URL, a stack submit, or new commits on an open PR leave this run **not done** until `ce-babysit-pr` owns follow-on for that PR. Reporting the PR URL alone is not success.

The only skips are `babysit:off`, a standing `auto_babysit: false` in the configuration, and that reference's do-not-fire cases, drafts among them. No other watch substitutes: not `ci-watcher`, not `gh pr checks --watch`, not a hand-rolled poll, not "later". If `ce-babysit-pr` cannot be loaded or started, stop and report it blocked.

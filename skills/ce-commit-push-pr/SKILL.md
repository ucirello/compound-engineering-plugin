---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to asking in chat only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Apply it only if asked. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — an explicit request to apply an update authorizes applying it without another approval; an optional rewrite otherwise requires approval. Resolve PR presence by Context: exit-0 `[]` means none; nonzero means unknown and blocks mutation. Run Step 4 in PR mode, then Step 5. Already-authorized babysitting factual refresh is maintenance, not this standalone approval flow. Description-only remains draft-only.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run the resolved mode non-interactively and suppress every blocking ask. Each suppressed ask takes the conservative default: no existing-PR rewrite, the branch kept, an unresolvable base stopping rather than guessed, and a description-update preview applied directly, since that invocation is the apply intent. Pipeline stack mode uses only the intent and scope on the invocation and passes posture into the handoff.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` **before Step 3** and follow only probing, topology, and retrospective construction; that layer-by-layer flow replaces ordinary Step 3. **Do not submit there.** Step 5 handles native JJ/gh submission, capability residuals, and handoff: `posture:stack-ready` by default, `posture:stack-land` only on explicit land intent, from the **bottom open non-draft** PR. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` before Step 1.** It defines absolute workspace cwd, repository-scoped gh environment, exit-code meanings, fork traps, and bookmark/PR resolution. No feature bookmark or default-bookmark work creates a feature bookmark without another ask; no default-bookmark work reports and stops. Determine message syntax at runtime using `references/commit-and-push.md`, never a fixed type default.

Three rules govern the run.

**Every JJ and gh probe has independently inspected status.** Run from the absolute workspace root and supply gh with `GIT_DIR` obtained by `jj git root`, as Context prescribes. Never invoke Git directly.

**Probe output is a snapshot.** Re-verify branch, remote, and PR state right before each consequential action: Step 3's push, Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork checkout, target the base with `-R` and pass the branch name only, since `--head <owner>:<branch>` silently returns `[]`. With results, do **not** blindly take index 0: match head owner and branch, and stop on an ambiguous match. Note the URL and body from that entry — Step 5 uses the URL to pick the existing-PR path, Step 4 rewrites the existing body.

## Artifact Root

Resolve `<root>` once when archival is on: it writes an explainer under `<root>/explainers/`.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Step 3: Commit and push

**Read `references/commit-and-push.md`** for commit/push mechanics and default-branch handling via `references/branch-creation.md`. If stack mode committed its layers, skip to Step 4; Step 5 submits them.

**Project publishing gate.** Before publishing commits, resolve every applicable pre-push or review-ready requirement from the project's active instructions and conventions already in context and any additional scoped instructions governing the committed paths. Only evidence valid for the exact commit state being sent satisfies them; otherwise stop before the external write and report what is missing or failing. If none, proceed.

Commit only explicitly named owned paths using JJ; preserve unrelated and excluded files. Read the full Go guide and compare recent full JJ subjects and bodies as required by `references/commit-and-push.md` before composing messages.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full, including preserving existing `Related:` / `Fixes`. Then read **`references/compose.md`** for evidence and teaching decisions: `pr_teaching_section` defaults **on**, `pr_teaching_archive` defaults **off**, and only active (non-commented) keys change them. Do not add creator/model/harness attribution or badges.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for apply, preview, archival, and handoff. Before `gh pr create`, re-check PR presence: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. Pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**Completion is decided here.** An interactive full workflow or pipeline stack submit is **not done** until `ce-babysit-pr` owns follow-on for the published PR. Reporting the PR URL alone is not success. Load the callee to choose the monitoring mode. If running it in this session, continue until its stop condition permits a final report.

Only `babysit:off`, config's `auto_babysit: false`, or a "Do not fire" case in `references/apply-and-handoff.md` skips it. No other watch substitutes: not `ci-watcher`, not `gh pr checks --watch`, not a hand-rolled poll, not "later". If `ce-babysit-pr` cannot be loaded or started, stop and report it blocked.

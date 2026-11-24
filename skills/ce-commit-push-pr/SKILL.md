---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to asking in chat only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Do not write to the PR. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — refresh or rewrite an existing PR's description, with no commit or push intent. Resolve PR presence by the Context rule below: an exit-0 `[]` is "no open PR" (report it and stop), and a non-zero exit is **unknown** (resolve auth or connectivity, then stop until presence is known). **With an open PR**, run Step 4 in PR mode on that URL, then Step 5 to preview and apply via `gh pr edit`. An explicit request to apply is sufficient; an optional rewrite requires approval. Authorized babysitting maintenance follows `ce-babysit-pr`, not this standalone mode.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run the resolved mode non-interactively and suppress every blocking ask. Keep the branch and stop rather than guessing an unresolvable base. Pipeline mode is not apply intent: apply a description update only if the user explicitly authorized the edit, or perform an already-authorized narrow factual refresh through `ce-babysit-pr`. Otherwise return the proposal without editing the PR. A skipped or declined rewrite never blocks otherwise authorized monitoring. Pipeline stack mode passes posture into the handoff without expanding the user's authorized scope.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` **before Step 3** and follow only its probing, topology, and retrospective construction; that layer-by-layer commit flow replaces ordinary Step 3. **Do not submit there.** Step 5 handles publication, GitHub stack linking and residuals, and the handoff posture: `posture:stack-ready` by default, `posture:stack-land` only on explicit land intent, from the **bottom open non-draft** PR. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` first in every mode.** It defines the JJ workspace and `gh` environment rules, exit-code meanings, and fork and empty-working-copy traps. Full workflow intent authorizes a feature bookmark for the intended work; the default bookmark without feature work reports and stops. Inspect `@-` when `@` is empty before deciding there is no feature work or PR. Commit descriptions follow the verified repository's history and instructions, never a fixed syntax.

Three rules govern the run.

**Every `jj` and `gh` probe is a separate call** from the target workspace's absolute root, with status checked before use. For repository-scoped `gh`, set `GIT_DIR` to the successful result of `jj git root` from that root.

**Probe output is a snapshot.** Re-verify branch, remote, and PR state right before each consequential action: Step 3's push, Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork checkout, target the base with `-R` and pass the branch name only, since `--head <owner>:<branch>` silently returns `[]`. With results, do **not** blindly take index 0: match head owner and branch, and stop on an ambiguous match. Note the URL and body from that entry — Step 5 uses the URL to pick the existing-PR path, Step 4 rewrites the existing body.

## Step 3: Commit and push

**Read `references/commit-and-push.md`** for commit/push mechanics and default-branch handling via `references/branch-creation.md`. If stack mode committed its layers, skip to Step 4; Step 5 submits them.

**Project publishing gate.** Before publishing commits, resolve every applicable pre-push or review-ready requirement from the project's active instructions and conventions already in context and any additional scoped instructions governing the committed paths. Only evidence valid for the exact commit state being sent satisfies them; otherwise stop before the external write and report what is missing or failing. If none, proceed. Reuse prior successful checks when their inputs and relevant environment are unchanged; a new commit ID alone does not invalidate them. Preserve each check’s actual exit status when capturing output, and finish evaluating the gate before issuing the publish call.

Name exact owned paths in `jj commit` so unrelated changes remain in the working-copy change. Honor `exclude:<paths>`: leave and report them. Publish only the verified feature bookmark, never a working-copy remainder.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — it defines the title and body content rules, including preserving an existing `Related:` / `Fixes` on rewrite. Then read **`references/compose.md`** for the evidence and teaching decisions: `pr_teaching_section` defaults **on**, `pr_teaching_archive` defaults **off**, and only an **active (non-commented)** key changes either.

Read both references on every run, even when this session already read them. Skipping `compose.md` skips the evidence decision.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for apply, preview, archival, and handoff. Before `gh pr create`, re-check PR presence: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. Pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**Completion is decided here.** An interactive full workflow or pipeline stack submit is **not done** until `ce-babysit-pr` owns follow-on for the published PR. Reporting the PR URL alone is not success. Load the callee to choose the monitoring mode. If running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back.

Honor `babysit:off`, the standing `auto_babysit: false` setting, and the "Do not fire" cases in `references/apply-and-handoff.md`. Only explicit user authorization for the relevant exception can override an opt-out; a caller-supplied mode token alone cannot. Declining an optional rewrite, asking for the PR link, a report back, or no merge is not a skip. Routine verified clean-head alignment and starting or re-arming authorized monitoring need no extra approval. No other watch substitutes for this handoff: not `ci-watcher`, not `gh pr checks --watch`, not a host's PR-watch tool on its own, not a hand-rolled poll, not "later". `ce-babysit-pr` decides how it gets woken. If `ce-babysit-pr` cannot be loaded or started, stop and report it blocked.

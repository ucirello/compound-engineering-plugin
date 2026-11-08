---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Change, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to asking in chat only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Apply it only if asked. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — an explicit request to apply an existing PR update authorizes applying the preview without another approval. Resolve PR presence by Context; unknown state blocks writes. Description-only requests remain draft-only. Authorized babysitting factual refreshes use the maintenance path, not optional-rewrite approval.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run the resolved mode non-interactively and suppress every blocking ask. Each suppressed ask takes the conservative default: no existing-PR rewrite, the branch kept, an unresolvable base stopping rather than guessed, and a description-update preview applied directly, since that invocation is the apply intent. Pipeline stack mode uses only the intent and scope on the invocation and passes posture into the handoff.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` before Step 3 for native JJ topology and construction; its layer flow replaces ordinary Step 3. Only Step 5 publishes. Hand off the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only on explicit land intent. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` before Step 1.** It defines JJ bookmark, repository and PR resolution. Full workflow intent authorizes creating a feature bookmark when needed. Read `references/commit-and-push.md` before composing messages; runtime repository syntax wins over Go guidance and no fixed prefix is imposed.

Three rules govern the run.

**Every probe's exit status is control flow.** Run JJ from the target absolute workspace root and all repository-scoped `gh` calls there with `GIT_DIR=$(jj git root)`, including every reference's examples. Never execute Git directly.

**Probe output is a snapshot.** Re-verify branch, remote, and PR state right before each consequential action: Step 3's push, Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork checkout, target the base with `-R` and pass the branch name only, since `--head <owner>:<branch>` silently returns `[]`. With results, do **not** blindly take index 0: match head owner and branch, and stop on an ambiguous match. Note the URL and body from that entry — Step 5 uses the URL to pick the existing-PR path, Step 4 rewrites the existing body.

## Step 3: Commit and push

**Read `references/commit-and-push.md`** for commit/push mechanics and default-branch handling via `references/branch-creation.md`. If stack mode committed its layers, skip to Step 4; Step 5 submits them.

**Project publishing gate.** Before publishing commits, resolve every applicable pre-push or review-ready requirement from the project's active instructions and conventions already in context and any additional scoped instructions governing the committed paths. Only evidence valid for the exact commit state being sent satisfies them; otherwise stop before the external write and report what is missing or failing. If none, proceed. Reuse prior successful checks when their inputs and relevant environment are unchanged; a new commit ID alone does not invalidate them. Preserve each check’s actual exit status when capturing output, and finish evaluating the gate before issuing the publish call.

Name only owned paths in JJ commits so unrelated work stays out. Honor `exclude:<paths>`: leave and report them.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full, preserving existing related references, then **`references/compose.md`** for evidence and teaching decisions. Do not append creator badges, branding or model/harness attribution.

Read both references on every run, even when this session already read them. Skipping `compose.md` skips the evidence decision.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for apply, preview, archival, and handoff. Before `gh pr create`, re-check PR presence: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. Pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**Completion is decided here.** An interactive full workflow or pipeline stack submit is **not done** until `ce-babysit-pr` owns follow-on for the published PR. Reporting the PR URL alone is not success. Load the callee to choose the monitoring mode. If running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back.

Only `babysit:off`, config's `auto_babysit: false`, or a "Do not fire" case in `references/apply-and-handoff.md` skips it. Asking for the PR link, a report back, or no merge is not a skip. No other watch substitutes for this handoff. `ce-babysit-pr` decides how it gets woken. If it cannot be loaded or started, report it blocked. Authorized monitoring, re-arming and clean-head alignment need no second approval; optional rewrites are separate and declining one never blocks monitoring.

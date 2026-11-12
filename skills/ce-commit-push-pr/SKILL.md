---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [branding:on|off] [babysit:off|continuous|checkpoint]"
---

# Commit, Push, and PR

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to asking in chat only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Apply it only if asked. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — refresh or rewrite an existing PR's description, with no commit or push intent. Resolve PR presence by the Context rule below: an exit-0 `[]` is "no open PR" (report it and stop), and a non-zero exit is **unknown** (resolve auth or connectivity, then stop until presence is known). **With an open PR**, run Step 4 in PR mode on that URL, then Step 5's optional-update approval flow unless apply was explicitly requested. Already-authorized babysitting factual maintenance bypasses that standalone approval flow; description-only remains draft-only.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run the resolved mode non-interactively and suppress every blocking ask. Each suppressed ask takes the conservative default: no existing-PR rewrite, the branch kept, an unresolvable base stopping rather than guessed, and a description-update preview applied directly, since that invocation is the apply intent. Pipeline stack mode uses only the intent and scope on the invocation and passes posture into the handoff.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` **before Step 3** and follow only its probing, topology, and retrospective construction; that layer-by-layer commit flow replaces ordinary Step 3. **Do not submit there.** Step 5 handles submission, the `gh stack` CLI dependency and residuals, and the handoff posture: `posture:stack-ready` by default, `posture:stack-land` only on explicit land intent, from the **bottom open non-draft** PR. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` before Step 1.** It defines JJ workspace context, exit-code meanings, fork and unbookmarked-head traps, and bookmark/PR resolution. Resolve the verified task history head even when empty `@` sits above it. Full-workflow intent authorizes a necessary feature bookmark; default-bookmark work must not be pushed directly. Before composing any message, read the full Go guide and several complete historical subjects and bodies as that reference requires; project instructions and history always win.

Three rules govern the run.

**Every JJ and `gh` probe has its own captured exit status**, gathering and re-verification alike. Run JJ from the absolute target workspace root and repository-scoped `gh` with `GIT_DIR=$(jj git root)` there. Never execute Git directly. Keep all scratch under that workspace's `.tmp/`.

**Probe output is a snapshot.** Re-verify branch, remote, and PR state right before each consequential action: Step 3's push, Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork checkout, target the base with `-R` and pass the branch name only, since `--head <owner>:<branch>` silently returns `[]`. With results, do **not** blindly take index 0: match head owner and branch, and stop on an ambiguous match. Note the URL and body from that entry — Step 5 uses the URL to pick the existing-PR path, Step 4 rewrites the existing body.

## Step 3: Commit and push

**Read `references/commit-and-push.md`** for commit/push mechanics and default-branch handling via `references/branch-creation.md`. If stack mode committed its layers, skip to Step 4; Step 5 submits them.

**Project publishing gate.** Before publishing commits, resolve every applicable pre-push or review-ready requirement from the project's active instructions and conventions already in context and any additional scoped instructions governing the committed paths. Only evidence valid for the exact commit state being sent satisfies them; otherwise stop before the external write and report what is missing or failing. If none, proceed. Reuse prior successful checks when their inputs and relevant environment are unchanged; a new commit ID alone does not invalidate them. Preserve each check’s actual exit status when capturing output, and finish evaluating the gate before issuing the publish call.

Commit only explicitly owned paths using the JJ isolation flow in the reference. Honor `exclude:<paths>`: leave and report them, preserving unrelated tracked, ignored, and untracked work.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — it defines title/body rules and preservation of existing related references. Read **`references/compose.md`** for evidence and teaching decisions: `pr_teaching_section` defaults **on**, `pr_teaching_archive` defaults **off**, and only active keys change them. Output creator/model/harness attribution is prohibited; the compatibility branding token does not add attribution.

Read both references on every run, even when this session already read them. Skipping `compose.md` skips the evidence decision.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for apply, preview, archival, and handoff. Before `gh pr create`, re-check PR presence: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. Pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**Completion is decided here.** An interactive full workflow or pipeline stack submit is **not done** until `ce-babysit-pr` owns follow-on for the published PR. Reporting the PR URL alone is not success. Load the callee to choose the monitoring mode. If running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back.

Only `babysit:off`, RocketClaw config's `auto_babysit: false`, or a "Do not fire" case in `references/apply-and-handoff.md` skips it. Asking for the PR link, a report back, or no merge is not a skip. No other watch substitutes for this handoff: not `ci-watcher`, not `gh pr checks --watch`, not a host's PR-watch tool on its own, not a hand-rolled poll, not "later". `ce-babysit-pr` decides how it gets woken. If `ce-babysit-pr` cannot be loaded or started, stop and report it blocked.

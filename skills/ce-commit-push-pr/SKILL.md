---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Change, Push, and PR

All source commands run from the target absolute `workspace_root`; paths remain repo-relative. Export `GIT_DIR` obtained there from `jj git root` before every repository-scoped `gh` call, including stack commands. Every reference inherits this cwd/environment contract. Never substitute `jj -R` for cwd. Temporary files and error paths belong under `$workspace_root/.tmp/`. Native JJ semantics: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-experts/ .

```bash
cd "$workspace_root"
export GIT_DIR="$(jj git root)"
mkdir -p "$workspace_root/.tmp"
```

Already-authorized factual babysitting refreshes, clean-head alignment, and monitoring/rearming need no extra approval. Preserve unrelated authored content and issue links. Verify head repository, remote, bookmark, and commit; an empty `@` directly above that pushed head is already aligned. Inspect `@-` and its PR before stopping for an empty tip. Dirty/conflicted state, ambiguous targets, denied permissions, or unknown push authority require a safe decision, never reset/discard. Optional rewrites outside authorized maintenance or explicit apply intent still require approval; keep them separate from alignment/monitoring, never prerequisite. Declining a rewrite retains the body and continues authorized monitoring. Description-only is draft-only. Respect opt-outs, watch boundaries, merge/scope-expansion and needs-human decisions.

**Asking the user:** use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to asking in chat only when no such tool is in the list or a real question call errors, and never silently skip the question.

## Mode

- **Description-only** — the user wants *just* a description ("write/draft a PR description", "describe this PR", a pasted PR URL or number). Run Step 4 only and print it. Apply it only if asked. Pass any pasted PR ref so Pre-A resolves the range.
- **Description update** — refresh or rewrite an existing PR's description, with no commit or push intent. Resolve PR presence by Context: exit-0 `[]` means none (report and stop), non-zero means unknown (resolve auth/connectivity and stop until known). With an open PR run Step 4 in PR mode and Step 5. Explicit apply intent or authorized factual babysitting maintenance applies without another approval; optional rewrites outside that authority still preview and require approval.
- **Full workflow** — otherwise: Steps 1-5. Enter **Stack mode** instead when intent or preference wants a stack.

**`mode:pipeline` modifier**, set by orchestrated callers such as `lfg`. Run non-interactively and suppress blocking asks. Optional existing-PR rewrite defaults to no; already-authorized factual maintenance still proceeds, and explicit description-update apply intent applies directly. Keep the feature bookmark; an unresolvable base stops rather than being guessed. Pipeline stack mode uses only invocation intent/scope and passes posture into the handoff.

## Stack mode (opt-in)

**Opt-in only.** Enter it when intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay single-PR.

In stack mode, load `references/stack-submit.md` **before Step 3** and follow only its probing, topology, and retrospective construction; that layer-by-layer commit flow replaces ordinary Step 3. **Do not submit there.** Step 5 handles submission, the `gh stack` CLI dependency and residuals, and the handoff posture: `posture:stack-ready` by default, `posture:stack-land` only on explicit land intent, from the **bottom open non-draft** PR. Do not add `posture:` to this skill's argument-hint.

## Context

**Read `references/context.md` before Step 1.** It defines probe exit meanings, fork traps, and bookmark/PR resolution. Full shipping intent authorizes feature bookmark creation when none exists or work is on the default bookmark; no extra approval. Default with no work reports and stops. Before composing or validating messages/titles, read `references/commit-and-push.md` and derive syntax at runtime; no Conventional Commit default.

Three rules govern the run.

**Every probe's exit status is control flow.** Native tool calls use the target absolute cwd and explicit GIT_DIR environment; shell calls use the setup above.

**Probe output is a snapshot.** Re-verify branch, remote, and PR state right before each consequential action: Step 3's push, Step 5's create.

**Only an exit-0 `[]` from a query against the base repo means "no open PR."** A non-zero exit is **unknown**, never "none". On a fork checkout, target the base with `-R` and pass the branch name only, since `--head <owner>:<branch>` silently returns `[]`. With results, do **not** blindly take index 0: match head owner and branch, and stop on an ambiguous match. Note the URL and body from that entry — Step 5 uses the URL to pick the existing-PR path, Step 4 rewrites the existing body.

## Artifact Root

Resolve `<root>` once when archival is on: it writes an explainer under `<root>/explainers/`.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = the absolute `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Step 3: Commit and push

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

**Read `references/commit-and-push.md`** for commit/push mechanics and default-branch handling via `references/branch-creation.md`. If stack mode committed its layers, skip to Step 4; Step 5 submits them.

**Project publishing gate.** Before publishing commits, resolve every applicable pre-push or review-ready requirement from the project's active instructions and conventions already in context and any additional scoped instructions governing the committed paths. Only evidence valid for the exact commit state being sent satisfies them; otherwise stop before the external write and report what is missing or failing. If none, proceed.

Select exact owned files with native JJ splitting as needed; inspect resulting revisions so unrelated work stays out. Honor `exclude:<paths>`: leave and report them.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — it defines title/body rules, including preservation of existing `Related:` / `Fixes` on rewrite. Then read **`references/compose.md`** for evidence and teaching decisions: `pr_teaching_section` defaults **on**, `pr_teaching_archive` defaults **off**, and only **active (non-commented)** keys change either. Do not add attribution badges, author bylines, or model/harness branding.

If Step 1 found an existing PR, pass its URL to Step 4 so PR mode fetches the existing body.

## Step 5: Apply and report

**Read `references/apply-and-handoff.md`** for apply, preview, archival, and handoff. Before `gh pr create`, re-check PR presence: a matching PR takes the existing-PR path, exit-0 `[]` creates, non-zero blocks. Pass the body via `--body-file <path>`, never stdin — `gh` exits 0 with an empty body.

**Completion is decided here.** An interactive full workflow or pipeline stack submit is **not done** until `ce-babysit-pr` owns follow-on for the published PR. Reporting the PR URL alone is not success. Load the callee to choose the monitoring mode. If running it in this session, continue until its stop condition permits a final report.

Only `babysit:off`, RocketClaw config's `auto_babysit: false`, or a "Do not fire" case in `references/apply-and-handoff.md` skips it. No other watch substitutes: not `ci-watcher`, not `gh pr checks --watch`, not a hand-rolled poll, not "later". If `ce-babysit-pr` cannot be loaded or started, stop and report it blocked.

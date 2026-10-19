---
name: ce-commit-push-pr
description: Commit, push, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# JJ Commit, Push, and PR

**Asking the user:** use the host's blocking question tool by capability when available, otherwise ask in chat. Ask only for genuine unresolved decisions; do not request approval again for actions already authorized by the user or active workflow. Respect higher-priority rules, actual permissions, watch boundaries, standing monitoring opt-outs, final-merge and scope-expansion decisions.

## Mode

- **Description-only** — draft/write/describe a PR, including a pasted PR reference: Step 4 only, print the result, no mutations or monitoring unless explicitly requested.
- **Description update** — explicit apply intent for an existing PR: Step 4 in PR mode, then Step 5 applies the factual requested update without a second yes/no. Unknown PR presence blocks; no matching PR reports and stops.
- **Full workflow** — otherwise Steps 1–5. Stack mode is opt-in for explicit intent or standing preference. Do not proactively suggest stacks; standing preference alone does not justify artificial slices, but explicit multi-PR intent must not be reinterpreted as one PR.

**`mode:pipeline`** suppresses blocking asks: optional existing-description rewrite defaults to no, current bookmark is kept, ambiguous base stops, explicit description-update intent applies directly. Return genuine decisions as residuals rather than guessing. Stack mode uses only supplied scope and intent.

## Context and Steps 1–2

Read `references/context.md` for workspace, bookmark, remote, fork, empty-tip and PR resolution, and `references/branch-creation.md` when selecting a new base. Shipping intent authorizes a needed feature bookmark, never publishing the default directly. A default bookmark with no work reports and stops.

Run every JJ operation with cwd set to the absolute target workspace root, not merely `jj -R`. Every repository-scoped `gh` call uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, adding `-R <base-owner>/<repo>` for fork PRs. Inspect exit statuses: only exit-0 `[]` means no PR; errors mean unknown. Match exact head repository, owner and bookmark rather than choosing the first result. Re-verify targets immediately before every external write. An empty `@` above the pushed head is already aligned; inspect `@-` before concluding there is no PR.

## Artifact root

When archival is enabled, read `docs_root` only from `<repo-root>/.rocketclaw/config.yaml` (`jj workspace root`), never local config. Unset defaults to `docs`. A set value must be repo-relative, symlink-resolved within the repository, neither root nor under `.git/` or `.jj/`; otherwise stop without fallback. Use `<root>/explainers/` exclusively.

## Step 3: Commit and push

Read `references/commit-and-push.md`, including its full Go excerpts and mandatory runtime full-guide/history comparison before composing messages. Repository-local syntax wins; do not impose a fixed template. Commit explicit repo-relative file groups only. Honor `exclude:<paths>` and preserve/report unrelated work.

**Project publishing gate:** resolve applicable pre-push/review-ready requirements from active project and scoped instructions. Only evidence valid for the exact commit state being sent satisfies them; stop before publishing on missing/failing evidence.

For stack mode, read `references/stack-submit.md` before Step 3. Its probe, topology and layer construction replace ordinary committing, but only Step 5 submits. Use JJ local topology; never a Git-checkout bridge.

## Step 4: Compose title and body

Read `references/pr-description-writing.md` in full and `references/compose.md`. Preserve existing related/closing references and unrelated user-authored content. Pass an existing PR's explicit URL so PR mode uses its verified base/head/body. Do not add creator/model/harness attribution or branding.

## Step 5: Apply and report

Read `references/apply-and-handoff.md` for apply intent, optional rewrite approval, local temporary body files, archival and handoff. Re-check PR presence before creation: matching existing PR uses that path, exit-0 `[]` creates, unknown blocks. Stack submission belongs here; hand off from the bottom open non-draft PR with `posture:stack-ready`, or `posture:stack-land` only for explicit landing intent.

Authorized babysitting includes factual stale-description refresh, verified clean-head alignment, and starting/re-arming authorized monitoring without another question. Optional interactive rewrites outside that scope still need approval, must not be bundled with alignment/monitoring permission, and declining never blocks an otherwise authorized handoff. Description-only remains draft-only.

**Completion gate:** interactive full workflow or pipeline stack submission is not done until `ce-babysit-pr` owns follow-on, except explicit `babysit:off`, standing `auto_babysit: false`, or the reference's Do-not-fire cases. Load the callee and obey its monitoring mode and stop condition. No other watcher substitutes; inability to load/start is a reported blocker. Return all typed needs-human decisions unchanged.

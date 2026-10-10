# Opt-in stack construction and submit recipes

Load this file only when commit-push-pr stack mode is active (the user asked for a PR stack, or a standing preference wants one). Use the `gh stack` CLI when it is present; never require a separate gh-stack skill package.

This reference has two phases. Before ordinary Step 3 (commit and push), run Probe, Topology, and, when needed, Retrospective construction only; do not run Submit. Step 5 (apply and report) is the only phase that runs Submit and applies titles and bodies to PRs created in this run.

A **residual** below means an unresolved item you report back to the user or the calling pipeline instead of guessing.

## Probe

```bash
command -v gh
gh stack view --json
```

If `gh` or `gh stack` is missing, or the stack command reports that stacks are unavailable for this repo (rather than merely reporting that the current branch is not part of a stack), stop with a clear residual. Stack intent is **required** when the user explicitly demanded a multi-PR stack or a standing preference forces stacks → hard-stop. Otherwise intent is **soft** → report the residual and fall back to the ordinary single-PR create.

## Topology

**When the user named a parent PR or branch to stack on, classify it and root the layers there.** Classify by **PR number** wherever one exists — that is what pulls a stack down from GitHub; a bare branch name resolves local stacks only. `references/gh-stack-cli.md` lists the exit codes and what each command does.

Classification uses read-only metadata per `gh-stack-cli.md`, not manager checkout. Record the original JJ revision/bookmark and preserve a recovery bookmark before any owned local mutation. Keep the parent and original work distinct so parent classification cannot replace the work being split.

- **In a stack** — build the owned JJ layer above the exact verified requested parent. If that parent is not the manager's top and cannot be represented safely, report a residual; never silently select a different top.
- **Standalone** — verify PR owner and exact `headRefOid`, then create/reuse a matching local JJ bookmark without resetting any stale/unrelated name. A branch-only parent requires fresh verified remote/local identity and can only be an untouched trunk. Adopt a standalone PR as managed bottom only when authored by the current user and authorized. Register hosting topology only through a verified compatible external-tool manager route.
- **Unproven** — report a residual, never guess standalone or create a second stack. Distinguish auth/network, ambiguous parent, and unavailable stacks.

In construction, `<base>` is the verified parent's tip. `references/branch-creation.md` uses the repo default and must not be followed when a parent was named. Require PR-derived bookmark names to match `[A-Za-z0-9._/-]+` before interpolation and stop with a residual otherwise; shell double quotes do not prevent command substitution in interpolated command text.

When `gh stack view --json` confirms the current branch belongs to a managed stack, preserve that topology. If no topology exists, use retrospective construction below. When the user did not ask for a stack in this request — a standing preference alone is not asking — and the complete work is one logical change or only artificial slices are possible, refuse the stack and use the single-PR path. An explicit request is not refusable on those grounds. (Probe's soft/required split governs what to do when the CLI is missing, not whether a stack may be refused.)

Any explicit new upstack layer must start from the **authoritative parent tip** after `jj git fetch --remote <tracking-remote>`: prefer the verified current `<parent>@<tracking-remote>`, or the verified local parent tip when newer local work is not published. From the absolute workspace root, use `jj new '<verified-parent-tip>'` then `jj bookmark create '<layer-name>' -r @`. Preserve unrelated tracked/ignored/untracked work; stop on conflicts or collisions rather than stash/remove. Pipeline mode reports the blocker. Do not follow default-base `branch-creation.md` for an upstack layer or hard-code origin when the tracking remote differs.

## Retrospective construction

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before ordinary Step 3, inspect the **complete change set** against the verified base: existing JJ revisions plus tracked and untracked working changes. Derive the smallest useful set of linear, independently reviewable layers, foundation first. Each layer must be coherent against its parent without upstack dependencies. Use whole-file `jj split` groups or existing revision boundaries, never force hunk partitions.

When one safe topology is clear, proceed without asking: explicit stack intent authorizes the necessary local branches and commits. When multiple reasonable topologies would materially change review boundaries, ask the user with a concise bottom-to-top proposal. In `mode:pipeline`, stop with that proposal as a residual instead of guessing. If the split requires hunk-level partitioning or rewriting published history, ask the user before proceeding in interactive mode. In `mode:pipeline`, do not split or rewrite; stop with a residual that describes the required partition or rewrite and the explicit confirmation needed to proceed. Never rewrite published history without explicit confirmation.

Choose the bottom layer from the original verified JJ bookmark/revision. Starting on the default bookmark without a named parent follows `branch-creation.md`, including the foreign-local-commit decision. Existing feature work instead fetches the topology's verified base remote using native JJ and uses that exact remote-bookmark tip as bottom parent. If a parent was already verified locally, use that exact revision (a PR-specific fetched head may have no remote bookmark). Preserve the original tip with a recovery bookmark before mutation. Do not confuse feature revisions with unpushed local-default work or carry the entire feature tip into the bottom layer. Every upstack revision starts at its verified immediate parent through native JJ; registration uses only the compatible manager route in `gh-stack-cli.md`.

For uncommitted whole-file groups, preserve the original owned revision with a recovery bookmark, then use native `jj split` to form dependency-ordered revisions. Keep unrelated/excluded work outside all layers and in place; do not save/move/restore excluded paths. Inspect each revision and the constructed top against the complete original change set minus exclusions. Stop on any collision or ambiguous partition. Compose every layer message under `references/commit-and-push.md`: first read the full Go guide and compare several recent subjects AND bodies; runtime repository instructions/history win syntax. Record an already-known unit ID in repository-compatible form only when unambiguous; do not hunt for plans.

```bash
(cd "$workspace_root" && jj describe -r '<verified-bottom-revision>' -m "<message composed from the standards above>")
(cd "$workspace_root" && jj bookmark create '<bottom-branch>' -r '<verified-bottom-revision>')
(cd "$workspace_root" && jj describe -r '<verified-next-revision>' -m "<message composed from the standards above>")
(cd "$workspace_root" && jj bookmark create '<next-branch>' -r '<verified-next-revision>')
```

For committed work whose boundaries match the plan, create/reuse one JJ bookmark at each verified planned tip. Reuse the original feature bookmark only when its unchanged tip is one of them. Preserve a recovery bookmark before rearranging owned unpublished revisions with native JJ. Register bottom-to-top only through the compatible hosting route in `gh-stack-cli.md`, then read back manager topology and exact heads. Verify order and top-layer completeness before submit; missing local tracking is a blocker, not success.

## Submit (ready / non-draft)

Apply the **Project publishing gate** before submitting the stack.

Before submit, resolve the ordinary `pr_teaching_archive` / `archive:on|off` gate. If archival is on, stop with a residual before `gh stack submit`; do not create an explainer commit after submission or silently disable requested archival. The user can rerun with `archive:off` to use the safe post-submit description path until stack archival has a manager-aware route.

Before submit, inspect the stack's open PRs (`gh stack view --json` / `gh pr view`) for any **existing draft** layers. If any draft already exists that the author did not explicitly ask to open this run, do **not** pass `--open` (GitHub documents `--open` as also marking existing PRs ready for review). In that case, submit with `gh stack submit --auto` only, then treat the remaining drafts as a hard residual before babysit when babysit is on. Never mark someone's work-in-progress drafts ready.

When no existing drafts are present (or the user explicitly authorized opening every layer):

```bash
gh stack submit --auto --open
```

`--auto` alone creates drafts, and babysit skips drafts by default. When babysit is on, a draft-only outcome is a hard residual (or a step to mark the PRs ready) before the babysit handoff. Never treat drafts as a successfully shipped stack.

After submit, map every new PR to its exact head bookmark and URL. Pass each URL to ordinary PR-description composition so PR mode derives immediate parent/exact head, then apply with `gh pr edit "<pr-url>"`. Never rely on the current workspace to select a PR. Existing stack PRs retain titles/bodies unless rewrite or factual maintenance is already authorized; optional pipeline rewrite defaults to no. Authorized babysitting refreshes verified stale run results without reapproval, preserving unrelated authored content and issue links. Do not invent stack-specific title improvements.

## Forbidden on managed members

```bash
gh pr merge …
```

Landing uses `gh stack merge` only, run by `ce-babysit-pr` under `posture:stack-land` or by the user.

## Ownership

Step 5 exclusively owns stack submission and the post-submit description steps above, for PRs created in this run. No earlier step submits.

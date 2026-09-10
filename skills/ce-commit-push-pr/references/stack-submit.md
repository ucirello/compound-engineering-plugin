# Opt-in stack construction and submission

Load this file only when stack mode is active. `gh stack` is the stack manager; JJ owns local changes, bookmarks, fetches, and pushes. After any `gh stack` command that changes local refs, run `jj git import` before inspecting or mutating JJ state.

Before ordinary Step 3, run Probe, Topology, and any Retrospective construction. Step 5 alone runs Submit and applies metadata.

## Probe

```bash
command -v gh
jj git colocation status
GIT_DIR="$(jj git root)" gh stack view --json
```

`gh stack` requires the colocated repository state it manages. If colocation is disabled, `gh` or `gh stack` is missing, or stacks are unavailable for the repository, explicit stack intent hard-stops. A non-explicit standing preference may fall back to a single PR with a reported residual.

## Topology

When the user named a parent PR or bookmark, classify it by PR number whenever possible. A PR number can pull stack state from GitHub; a bare bookmark can classify only local state. `references/gh-stack-cli.md` owns exit meanings.

Classification can select another stack layer. Record the original JJ change ID, bookmark, and revision before classification. Run `jj git import` afterward and return with `jj edit <original-change-id>` before construction.

- If the parent is in a stack, add the new layer only from that exact top parent. Exit 5 means the named parent is not the top and is a residual; do not select a different top.
- If the parent is standalone, resolve `headRefName`, `headRefOid`, and `author` with `GIT_DIR="$(jj git root)" gh pr view`. Fetch with `jj git fetch`, resolve the returned commit ID, and create a local bookmark there only when absent and non-conflicting. Use it as an untouched trunk, or adopt it as the bottom layer only when the current account owns that PR.
- If classification is unproven or ambiguous, stop with a residual rather than creating a second or mis-parented stack.

Validate bookmark names received from GitHub as inert CLI arguments before use. Pass them as quoted arguments and reject names that the called tool cannot accept safely.

When `GIT_DIR="$(jj git root)" gh stack view --json` confirms membership, preserve that topology. Without topology, use retrospective construction. Refuse an artificial multi-PR split unless the user explicitly requested a stack.

For an explicit new upstack bookmark, fetch and use the authoritative parent tip: prefer the tracked remote bookmark when current, otherwise the verified local parent bookmark. Create the JJ child change with `jj new <parent-revision>`, then set the new bookmark only after that layer is complete. Do not use default-bookmark creation for an upstack layer.

## Retrospective construction

Inspect the complete JJ revision range from the resolved base through the current change, including working-copy content. Derive the smallest useful linear set of independently reviewable layers in dependency order. Use whole-file groups or existing change boundaries; `jj split <filesets>` or `jj commit <filesets>` partitions the working-copy change directly.

Proceed without asking when one safe topology is clear. Ask when multiple reasonable topologies materially change review boundaries. In `mode:pipeline`, return a residual instead of guessing. Rewriting published revisions requires explicit confirmation; pipeline mode stops rather than rewriting.

Preserve the original work with its stable JJ change ID and confirm it remains visible in `jj op log` before any rewrite. Root the bottom layer at the fresh default remote bookmark unless Topology resolved a parent. Every later layer starts from its immediate parent.

Files in `exclude:<paths>` remain in the original working-copy change and belong to no layer. Every split or commit uses explicit included filesets. Stop if construction cannot keep excluded content isolated.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Project instructions and runtime `git log` syntax win. Preserve an already-known Implementation Unit reference when it maps unambiguously to one layer, without forcing fixed syntax.

For each new layer:

```bash
jj commit <layer-filesets> -m "<message composed from the standards above>"
jj bookmark set <layer-bookmark> -r @-
GIT_DIR="$(jj git root)" gh stack init --base "<base-bookmark>" "<bottom-bookmark>" "<next-bookmark>"
```

Use `GIT_DIR="$(jj git root)" gh stack add "<next-bookmark>"` for a layer added to an existing managed top. Run `jj git import` after the manager command. Existing boundaries that already match the plan need only bookmarks at the corresponding revisions and bottom-to-top adoption. Verify `GIT_DIR="$(jj git root)" gh stack view --json` order and confirm the top layer contains the complete intended change set before submission.

## Submit

Resolve `pr_teaching_archive` and `archive:on|off` before submit. If archival is on, stop with a residual; do not create an unmanaged explainer change after stack submission.

Inspect existing stack PRs for drafts. Do not pass `--open` when it would mark an existing draft ready without explicit authorization. Otherwise submit ready PRs with:

```bash
GIT_DIR="$(jj git root)" gh stack submit --auto --open
```

Draft-only outcomes remain a residual when babysitting is on.

After submit, run `jj git import` and map each new PR to its head bookmark and URL. Compose and apply each new PR's metadata by explicit URL with `GIT_DIR="$(jj git root)" gh pr edit "<pr-url>"`. Existing stack PRs retain metadata unless this invocation explicitly requested a rewrite. Pipeline mode keeps the no-rewrite default.

## Managed-member boundary

Do not run `GIT_DIR="$(jj git root)" gh pr merge` for a stack member. Landing uses `GIT_DIR="$(jj git root)" gh stack merge`, owned by babysit under `posture:stack-land` or by the user.

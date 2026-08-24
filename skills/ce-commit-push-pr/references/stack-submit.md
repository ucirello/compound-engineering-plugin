# Opt-in Jujutsu stack construction and submission

Load this file only when stack mode is active. A stack is a linear sequence of Jujutsu changes with one publication bookmark and one GitHub PR per review layer. Jujutsu owns topology and push; `gh` owns GitHub PR metadata.

Before ordinary Step 3, run Topology and Retrospective construction only. Step 5 exclusively owns bookmark pushes and PR creation for layers created in this run.

## Topology

Read `references/jj-github-stack.md`. Resolve a named parent PR by PR metadata, fetch its head bookmark from the correct remote, and verify its object ID. Resolve a named parent bookmark from local and remote bookmark state. Unproven identity, ambiguous ownership, conflicted bookmarks, or non-linear ancestry are residuals, not guesses.

When the current work already forms a linear Jujutsu stack, preserve it. A standing preference alone does not justify artificial layers: if the user did not request a stack and the complete work is one logical change, use the single-PR path. An explicit stack request must remain a stack request.

Each explicit new upstack layer starts from the authoritative parent change after fetch. Use `jj new <parent-change>` for new work or `jj rebase -r <layer-change> -o <parent-change>` to preserve existing change identity. Never substitute a remote bookmark whose target lags the confirmed local parent.

## Retrospective construction

Inspect the complete unpublished change set against the resolved base with `jj log`, `jj show`, and `jj diff`. Derive the smallest useful linear set of independently reviewable layers in dependency order. Prefer existing change boundaries or whole-file filesets. Do not use hunk-level splitting merely to manufacture a stack.

Proceed when one safe topology is clear. Ask when multiple reasonable topologies materially change review boundaries. In `mode:pipeline`, return that proposal as a residual instead of guessing. Rewriting a published change requires explicit confirmation; in pipeline mode, stop with the required partition or rewrite and the confirmation needed.

Use path-limited `jj commit` or `jj split` for whole-file layers, then verify every layer with `jj show` and the full stack with `jj log`. Preserve the original change IDs where possible; before a material rewrite, record the operation ID so Jujutsu's operation log can recover the prior state. Files in `exclude:<paths>` belong to no layer and must remain outside every pushed change.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository instructions and the syntax established by `git log` always win. Apply compatible Go guidance only where those sources leave the choice open. Do not impose a type, scope, prefix, fixed subject form, fixed body, or Conventional Commit example. A known plan unit ID may be included only in the repository's established syntax and only when the layer maps clearly to that unit.

Create or move one bookmark per completed layer, pointing at that layer's exact change. Verify that the bottom-to-top bookmark sequence matches the change ancestry and that the top contains the complete intended change set.

## Submit

Resolve `pr_teaching_archive` and `archive:on|off` before external writes. If archival is requested, stop before stack submission because this workflow has no atomic manager-aware route for adding explainer changes to every affected layer. Report that `archive:off` enables the safe per-layer PR path.

Push bookmarks bottom to top with `jj git push --remote <push-remote> --bookmark <bookmark>`. A push safety refusal blocks dependent layers until fetch and bookmark reconciliation succeed.

For each layer without an open PR, use `gh pr create` with the layer bookmark as head and the immediate parent bookmark as base; the bottom uses the resolved repository base or named parent. Existing PRs retain their titles and bodies unless rewrite intent is explicit. In `mode:pipeline`, keep the conservative no-rewrite default.

After creation, map every PR to its bookmark and explicit URL. Pass each new URL to ordinary PR-description composition so PR mode derives the immediate parent and exact head, then apply with `gh pr edit <pr-url>`. Never select a PR from the working-copy change or list position.

Draft state is per PR. Do not mark an existing draft ready unless the user explicitly asked. A draft-only outcome is a hard residual before babysit when babysit is on.

Landing is not owned here. Return the bottom open non-draft PR and the derived stack posture to the handoff.

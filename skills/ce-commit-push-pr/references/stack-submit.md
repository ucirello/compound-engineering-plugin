# Opt-in JJ stack construction and submission

Load only for requested or standing-preference stacks. Before Step 3 run Probe, Topology, and Retrospective construction; only Step 5 submits. A residual is an unresolved item reported to the user or pipeline rather than guessed.

## Probe

Read `references/gh-stack-cli.md`. Run `gh stack link --help` with `GIT_DIR` obtained from `jj git root` in the absolute workspace root. JJ owns all local topology and pushes; `gh stack link` connects already-created PR URLs on GitHub without local stack tracking. Never use branch arguments, which cause implicit Git pushes.

If the CLI is missing or the repository cannot support stacks, explicit stack intent or a forcing preference is a hard residual. Soft intent may fall back to single-PR creation with the residual reported. Do not require a separate gh-stack skill package.

## Topology

Record the original change ID, commit ID, intended bookmark, and verified tip before construction. Read PR metadata without checking out a parent. For a named parent PR, use `gh pr view <url> --json headRefName,headRefOid,author,baseRefName,url,state`; match repository ownership as well as head name. Resolve GitHub stack membership using a supported read-only API available in the installed CLI; local `gh stack view` is not evidence of membership for externally managed JJ stacks. If remote membership or position cannot be proven, stop with a residual rather than treating the parent as standalone.

- **Parent in a stack:** preserve the existing topology. Append above the specified parent only if it is the top; otherwise report the conflict, never silently pick another parent.
- **Standalone parent:** use its verified head as an untouched trunk, or include its PR as the bottom layer only when its author is the current user.
- **Branch-only parent:** fetch and verify its remote bookmark; without proven PR ownership it can only be a trunk.
- **Unproven or ambiguous ownership/topology:** stop with a residual, never create a second stack by guessing.

Fetch the confirmed parent remote with `jj git fetch --remote <remote> --branch <parent>`. Verify the resulting commit against `headRefOid` for a PR. A same-named local bookmark at a different commit must not be reset. If the PR head is not reachable through the confirmed remote, stop with that residual; never read internal fetch files. Validate externally supplied branch names against `[A-Za-z0-9._/-]+` and pass values as argv, not interpolated shell expressions.

Preserve any confirmed existing stack. New upstack work is based on the authoritative immediate-parent tip: its fetched remote bookmark if current, otherwise the proven newer local parent when it has not yet been pushed. Do not run the default-base flow in `references/branch-creation.md` for an upstack layer. Creating a bookmark does not move the working copy; use a new JJ change on the verified parent only when doing so preserves all existing and excluded work. On colliding ignored paths or uncertain preservation, stop; do not stash or delete files.

Without an explicit request in this invocation, refuse artificial slices or a stack for one logical change and use a single PR. An explicit stack request retains its required intent even if one logical change is awkward to split.

## Retrospective construction

Inspect the complete change set against the resolved base: existing changes and current working-copy content, including new files. Plan the smallest useful linear layers, foundation first, with independently reviewable file groups or existing commit boundaries. No layer may depend on an upstack change.

Proceed when one topology is clear. If review boundaries are materially ambiguous, ask with the bottom-to-top proposal; pipeline reports the proposal as a residual. Hunk-level partitioning or published-history rewriting requires explicit confirmation; pipeline stops rather than performs either. Never rewrite published history without authorization.

When starting on the default bookmark with no named parent, use `references/branch-creation.md` to resolve stale-base and local-only work. On a feature bookmark, fetch and verify the resolved base instead; its existing feature commits are not local-default commits. A verified local parent can be the base when no remote bookmark exists. Preserve the original tip with a recovery bookmark before rearranging unpublished commits. Every next layer must descend from its immediate parent.

Files named by `exclude:<paths>` belong to no layer. Leave their working-copy content exactly as found; do not move, restore, or include them in any outgoing ancestor. If a required topology change cannot preserve them, stop with a residual. JJ path-selective commits retain unselected content in the working-copy child; verify both the completed layer and remainder after each operation.

Read https://go.dev/wiki/CommitMessage before composing or validating layer messages.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Here the quoted history command means `jj log` in this workflow; never execute Git. Runtime project instructions and visible history syntax override Go guidance. Include an already-known Implementation Unit ID when the layer belongs to one unit, using project conventions; omit when unclear or spanning units. Preserve relevant issue/PR references and do not hunt for a plan.

For working-copy whole-file groups already on the correct parent, repeat from the absolute workspace root:

```bash
jj commit -m "<message composed from the standards above>" -- <layer-files>
jj bookmark create <layer-branch> -r @-
```

Use `file:"<literal-path>"` filesets with correctly escaped inner strings for selected files; argv or shell quoting alone does not escape fileset syntax. For committed work already matching planned boundaries, create or reuse one bookmark at each planned tip without rewriting it. Reuse the original feature bookmark only if its unchanged tip is one of those boundaries. Verify the ancestry order, each layer's diff, and the top's complete original change set minus exclusions before submitting. Empty `@` is not an additional stack layer.

## Submit (ready / non-draft)

Apply the **Project publishing gate** to the exact outgoing stack. Resolve archival first: if enabled, stop with a residual before any push or PR creation. Do not silently disable requested archival or append an unmanaged explainer commit; the user can rerun with `archive:off`.

Re-check each PR by head owner/name against its base repository before creating anything. Unknown or ambiguous presence blocks creation. Push each verified bookmark using `jj git push --remote <head-remote> --bookmark <layer-branch>` (allow a new remote bookmark only when explicitly selected). Then create only absent PRs with explicit head and immediate-parent base; use ordinary PR-description composition and `--body-file` for every new PR. Keep existing titles and bodies unless rewrite was requested, including pipeline's conservative no-rewrite default.

Link explicit PR URLs bottom-to-top using `gh stack link --base <bottom-base> <bottom-pr-url> <next-pr-url> ...`. Do not pass `--open` when any existing draft lacks explicit authorization to become ready. New PRs may be created ready, but existing author drafts remain drafts. If every existing draft was explicitly authorized to open, `--open` may be used. Verify remote topology and PR states afterward; do not infer success from a local stack view. Draft-only outcomes or remaining drafts are hard residuals before babysit when babysit is enabled.

Report each created PR's URL and head bookmark. Hand off the bottom open non-draft PR, with `posture:stack-ready` by default or `posture:stack-land` only on explicit land intent, and stack-wide scope for pipeline submissions. `ce-babysit-pr` owns monitoring and landing; it must resolve the remotely linked stack without assuming local gh-stack tracking. Never merge a stack member with `gh pr merge`.

Step 5 exclusively owns submission and post-submit description application. No earlier step publishes.

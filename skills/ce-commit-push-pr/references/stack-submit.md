# Opt-in stack construction and submission

Load this file only when stack mode is active. Soft-depend on `gh stack`; do not depend on another skill package. Before ordinary Step 3, run Probe, Topology, and any retrospective construction. Step 5 alone runs Submit and applies metadata.

`gh stack` owns a GitHub/Git branch view of the stack. Keep Jujutsu authoritative: run `jj git export` before manager operations and `jj git import` after any operation that can create or move branches or change the checkout. Use Git branch names only at this interoperability boundary; use Jujutsu bookmarks and revisions everywhere else.

## Probe

```bash
command -v gh
jj git export
gh stack view --json
```

If `gh` or `gh stack` is unavailable for the repository, explicit stack intent hard-stops with a residual. Soft intent leaves a residual and falls back to one PR.

## Topology

When the user names a parent PR or branch, classify it and root the layers there. Prefer the PR number because it can pull topology from GitHub; a bare branch name can classify only exported local state. `references/gh-stack-cli.md` owns exit meanings.

Classification can move the Git checkout. Record the current Jujutsu change ID and intended bookmark first, then import and restore the intended change with `jj edit <change-id>` before construction.

- **Managed parent:** plan from the restored work change, export, classify the parent again, and run `gh stack add` there. Exit 5 means the named parent is not the top; stop rather than reparenting through `gh stack top`.
- **Standalone parent:** resolve `headRefName`, `headRefOid`, and `author` with `gh pr view`. Import or fetch the object, then create or verify a Jujutsu bookmark exactly at that revision; never move a colliding bookmark whose identity is unproven. Export it and initialize with the parent as untouched trunk, or adopt it as the bottom layer only when the current user is its author.
- **Unproven parent:** stop. Guessing can create a second stack.

Use the topology-specific `gh stack init` form rather than replacing an adopted parent with a generic base. A PR-derived name must match `[A-Za-z0-9._/-]+` before it reaches `gh`; stop on invalid input.

Preserve an existing managed topology. Without an existing topology, use retrospective construction. A standing preference alone does not justify artificial layers, but an explicit stack request is required intent and is not downgraded.

For a user-directed upstack layer, fetch the parent remote bookmark with `jj git fetch`, choose the authoritative parent revision, run `jj new <parent-revision>`, and create the new bookmark at `@`. Do not use default-bookmark creation logic for an upstack layer.

## Retrospective construction

Inspect the complete range from the resolved base through `@`, including existing revisions and current tracked or untracked content. Derive the smallest useful linear set of independently reviewable layers in dependency order. Use whole-file groups or existing revision boundaries; never force a hunk-level split.

Proceed without asking when one safe topology is clear. Ask when alternatives materially change review boundaries. In `mode:pipeline`, return the proposal as a residual instead of guessing. Rewriting published revisions always requires explicit confirmation; pipeline mode stops instead.

Choose the bottom parent from the authoritative remote bookmark, or the verified local parent resolved by Topology. Preserve the original change ID before rewriting. For each layer, create or reuse a Jujutsu revision on its immediate parent, commit only that layer's whole-file fileset, and put a bookmark at the completed revision. Files in `exclude:<paths>` belong to no layer and must remain in the working-copy change; stop if topology work cannot preserve them.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime project instructions and history read with `jj log` win. Apply the Step 2 quality guidance to every layer description and use neutral descriptions derived from each layer's outcome. Append an already-known Implementation Unit ID when applicable; do not search for one.

```bash
jj new <bottom-parent>
jj commit -m "<bottom-description>" <bottom-files>
jj bookmark create <bottom-bookmark> -r @-
jj new <bottom-bookmark>
jj commit -m "<next-description>" <next-files>
jj bookmark create <next-bookmark> -r @-
jj git export
gh stack init --base "<base>" "<bottom-bookmark>" "<next-bookmark>"
jj git import
```

For existing revision boundaries that already match the plan, create or reuse bookmarks at those revision tips and export them for bottom-to-top adoption. Reuse the original feature bookmark only when its unchanged target is a planned tip. Verify `gh stack view --json` order and confirm that the top Jujutsu revision contains the complete original change set before submit.

## Submit

Resolve `pr_teaching_archive` / `archive:on|off` first. If archival is on, stop before submit; stack archival has no manager-aware route.

Inspect existing layers for drafts. If any existing draft was not explicitly authorized to open, submit without `--open` and treat remaining drafts as a residual before babysitting. Otherwise:

```bash
jj git export
gh stack submit --auto --open
jj git import
```

`--auto` alone creates drafts. Draft-only outcomes do not satisfy stack shipping when babysitting is on.

Map every PR created in this run to its head bookmark and explicit URL. Pass each URL through ordinary PR-description composition and apply with `gh pr edit "<pr-url>"`. Existing stack PRs retain metadata unless rewrite intent is explicit; pipeline mode keeps the conservative no-rewrite default.

## Forbidden on managed members

Do not use `gh pr merge` on a stack member. Landing remains `gh stack merge`, owned by babysitting under `posture:stack-land` or by the user.

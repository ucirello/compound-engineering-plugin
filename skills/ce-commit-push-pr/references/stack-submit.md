# Opt-in stack construction and submit recipes

Load this file only when stack mode is active (user intent or standing preference wants a PR stack). Soft-depend on the `gh stack` CLI — never hard-depend on an external stack package.

This reference has two lifecycle phases. Before ordinary Step 3, run Probe, Topology, and, when needed, Retrospective construction only; do not run Submit. Step 5 is the only phase that runs Submit and applies metadata to PRs created in this run.

## Probe

```bash
command -v gh
gh stack view --json
```

If `gh` or `gh stack` is missing, or the stack command exits unavailable for this repository (rather than merely reporting that the current head is not part of a stack), stop with a clear residual. Stack intent is **required** when the user explicitly demanded a multi-PR stack or standing preference forces stacks → hard-stop. Otherwise intent is **soft** → residual + fall back to ordinary single-PR create.

## Topology

**When the user named a parent PR or bookmark to stack on, classify it and root the layers there.** Classify by **PR number** wherever one exists — that is what pulls a stack down from GitHub; a bare head name resolves local stacks only. `references/gh-stack-cli.md` carries the exit codes and command semantics.

Classification may move the stack manager's current head, so record the work bookmark and change ID **before** classifying. Run `jj git import` after manager operations and return with `jj edit <work-change>` before construction; otherwise construction can mistake the parent for the original work.

- **In a stack** (exit 0 — parent now selected) — plan layers from the restored work change, then select the parent through the manager and run `gh stack add` there so the layer sits above the named parent. Exit **5** means that parent is not the top: residual. Never clear it with `gh stack top`, which reparents onto a different layer.
- **Standalone** (exit 2 — nothing selected) — resolve `<parent-bookmark>` with `gh pr view "<n>" --json headRefName,headRefOid,author`, fetch through `jj git fetch`, and make sure a local bookmark targets the revision matching `headRefOid`. If the name already targets another revision, stop rather than moving it and risking local-only work. Then export bookmarks with `jj git export`; use `gh stack init --base "<parent-bookmark>" …` for an untouched trunk, or list the parent's exported ref first to adopt it as the bottom layer only when `author` is the current user.
- **Unproven** — a residual, not a guess: a wrong "standalone" is what creates the second stack, as are exit 6 and exit 9.

Use the `init` form chosen here in place of the generic one shown in construction, whose `--base` would leave an adopted parent unmanaged. The parent's tip is `<base>` there, and `references/bookmark-creation.md` roots on the repository default and must not be followed when a parent was named. Require a bookmark name taken from a PR to match `[A-Za-z0-9._/-]+` before it reaches a command and stop with a residual on a name that fails.

When `gh stack view --json` confirms the current head belongs to a managed stack, preserve that topology. If no topology exists, use retrospective construction below. When the user did not ask for a stack in this request — a standing preference alone is not asking — and the complete work is one logical change or only artificial slices are possible, refuse the stack and use the single-PR path. An explicit request is not refusable on those grounds. (Probe's soft/required split governs what to do when the CLI is missing, not whether a stack may be refused.)

Any explicit new upstack bookmark the user already directed must base from the **authoritative parent tip** after `jj git fetch`: prefer `<parent>@<tracking-remote>` when current for the confirmed layer; if the parent's latest work is only local, use the local parent bookmark. Create with `jj new <parent-tip>` and `jj bookmark create <bookmark-name> -r @`. For an **upstack** layer, do **not** follow `references/bookmark-creation.md`, whose default-base flow would detach the layer from its parent. Do not hard-code `origin` when another remote owns the parent.

## Retrospective construction

Before ordinary Step 3, inspect the **complete change set** against the resolved base: existing described changes plus the working-copy change. Derive the **smallest useful set of linear, independently reviewable layers** in dependency order, foundation first. Each layer must be coherent against its parent and must not depend on an upstack layer. Use whole-file groups or existing change boundaries; do not force hunk-level splits.

When one safe topology is clear, proceed without asking: explicit stack intent authorizes the necessary local bookmarks and changes. When multiple reasonable topologies would materially change review boundaries, ask the user with a concise bottom-to-top proposal. In `mode:pipeline`, stop with that proposal as a residual instead of guessing. If the split requires hunk-level partitioning or rewriting published history, ask the user before proceeding in interactive mode. In `mode:pipeline`, do not split or rewrite; stop with a residual that describes the required partition or rewrite and the explicit confirmation needed to proceed. Never rewrite published history without explicit confirmation.

Choose the bottom layer from the bookmark and change active when retrospective construction began. If construction starts on the resolved default bookmark and no parent was named, follow `references/bookmark-creation.md` to fetch and resolve its safe base. If construction starts on an existing feature bookmark, fetch the resolved base from its owning remote, verify the remote bookmark, and use that exact revision as the bottom parent. When Topology already resolved a verified local parent bookmark, use it instead. Record the original bookmark and change ID, and preserve that change before rewriting. Do not carry the whole feature series into the bottom layer. Every upstack layer starts from its immediate parent through an exported bookmark and `gh stack add`.

Partition whole-file groups directly from the working-copy change with `jj commit <filesets>`; Jujutsu keeps the remaining files in the child change, so no stash transition is needed. Initialize or adopt the bottom layer at the resolved base revision, describe only its files, then create and describe each next layer in order. Files named by `exclude:<paths>` belong to no layer: leave them in the final working-copy change and path-limit every layer operation. If a topology change would make excluded work unsafe, stop with a residual.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax. Preserve semantic plan-unit associations already in hand.

```bash
jj new <base>
jj bookmark create <bottom-bookmark> -r @
jj commit -m "<message composed from the standards above>" <bottom-files>
jj bookmark set <bottom-bookmark> -r @-
jj bookmark create <next-bookmark> -r @
jj commit -m "<message composed from the standards above>" <next-files>
jj bookmark set <next-bookmark> -r @-
jj git export
gh stack init --base "<base>" "<bottom-bookmark>" "<next-bookmark>"
```

For described work whose existing change boundaries already match the plan, create or reuse one bookmark at each planned change and export them before adopting them bottom-to-top with `gh stack init --base "<base>" "<bottom-bookmark>" "<next-bookmark>" ...`. Reuse the original feature bookmark only when its unchanged target is one of those planned changes. If unpublished changes need rearrangement, preserve the original change ID before rewriting. After construction, run `gh stack view --json`; verify the reported order matches the plan and the top layer contains the complete original change set before submit.

## Submit (ready / non-draft)

Before submit, resolve the ordinary `pr_teaching_archive` / `archive:on|off` gate. If archival is on, stop with a residual before `gh stack submit`; do not create an explainer change after submission or silently disable requested archival. The user can rerun with `archive:off` to use the safe post-submit description path until stack archival has a manager-aware route.

Before submit, inspect the manager's open PRs (`gh stack view --json` / `gh pr view`) for any **existing draft** layers. If any draft already exists that the author did not explicitly ask to open this run, do **not** pass `--open` (GitHub documents `--open` as also marking existing PRs ready for review). In that case: submit with `gh stack submit --auto` only, then treat remaining drafts as a hard residual before babysit when babysit is on — never auto-ready WIP drafts.

When no existing drafts are present (or the user explicitly authorized opening every layer):

```bash
gh stack submit --auto --open
```

`--auto` alone creates drafts; babysit skips drafts by default. Draft-only outcomes are a hard residual / reopen step before babysit handoff when babysit is on — never treat drafts as successful stack-ship completion.

After submit, run `jj git import`, then map every PR created in this run back to its head bookmark and explicit PR URL. For each new PR, pass that URL to ordinary PR-description composition so PR mode derives the immediate parent and exact head, then apply the result with `gh pr edit "<pr-url>"`; never rely on the restored current bookmark to select the PR. Existing stack PRs retain their titles and bodies unless the current invocation explicitly requested a rewrite; `mode:pipeline` keeps the documented conservative no-rewrite default. Do not invent stack-specific auto-title quality improvements in this skill.

## Forbidden on managed members

```bash
gh pr merge …
```

Landing uses `gh stack merge` only (owned by babysit under `posture:stack-land`, or the user).

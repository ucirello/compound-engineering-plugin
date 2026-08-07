# Opt-in stack construction and submission

Load this file only when stack mode is active. `gh stack` remains the GitHub stack manager; Jujutsu owns local changes, bookmarks, rebases, workspace state, and all Git transport.

Before ordinary Step 3, run Probe, Topology, and, when needed, Retrospective construction. Step 5 alone runs Submit and applies metadata.

## Probe

Run these separately:

```bash
command -v gh
gh stack view --json
```

If `gh` or `gh stack` is unavailable, required stack intent stops with a residual. Soft intent reports the residual and returns to one-PR creation.

## Topology

When the user names a parent PR or bookmark, classify it and root the layers there. Prefer a PR number because that identifies GitHub state; a name alone can establish only local manager state. `references/gh-stack-cli.md` owns the exit codes and manager semantics.

Classification can move the colocated checkout. Record the current Jujutsu change ID and intended work bookmark before classifying, then restore the intended work with `jj edit <change>` before construction. Never recover by moving an unrelated bookmark or abandoning a change.

- A parent already in a managed stack must remain the named parent. Add above it only when it is the top; otherwise stop with a residual rather than selecting another parent.
- A standalone PR parent must resolve to its exact `headRefOid` and a safe local bookmark. Create the bookmark at the fetched change when absent. If the name already targets different work, stop rather than moving it. A parent the current user does not own can serve as the stack trunk but must not be adopted as a managed layer.
- An unproven parent, ambiguous manager state, or repository without stack support is a residual rather than a guessed topology.

Require every bookmark name obtained from GitHub to pass Jujutsu's bookmark-name acceptance and the conservative Git-host interchange form `[A-Za-z0-9._/-]+` before using it. Pass command arguments as separate quoted values; never interpolate names into shell expressions.

When `gh stack view --json` confirms that the exported bookmark names form a managed stack, preserve that topology. If no topology exists, use retrospective construction. When stack intent is not explicit in the current request and the work is one logical change, use one PR.

For an explicitly requested upstack layer, fetch through `jj git fetch` and choose the authoritative parent change: use the tracked remote bookmark when it contains the parent's latest work, otherwise use the confirmed local parent bookmark. Start the child with `jj new <parent-bookmark>`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Describe the child according to project instructions and the syntax observed in `jj log`, then create its bookmark. Do not use the default-bookmark creation flow for an upstack layer.

## Retrospective construction

Inspect `trunk()..@` and the current working-copy diff. Derive the smallest useful linear set of independently reviewable layers in dependency order. Each layer must work against its parent and must not depend on a child. Preserve coherent existing change boundaries; use `jj split <files>` only for whole-file groups. Paths supplied through `exclude:<paths>` remain outside every layer and publication action.

One clear topology may proceed without another question because explicit stack intent authorizes the required local changes and bookmarks. Ask when multiple reasonable topologies materially change review boundaries. Pipeline mode returns that choice as a residual. Hunk-level partitioning or rewriting already-published changes requires explicit confirmation; pipeline mode stops rather than rewriting.

If construction begins from the default bookmark, follow `references/branch-creation.md` for fetch and base resolution. From an existing feature bookmark, fetch the default remote bookmark through `jj git fetch`, verify its target, and use that exact change as the bottom parent. Preserve the original tip with a recovery bookmark before any rebase or split that could make recovery difficult. When Topology resolved a named parent, use that parent instead of the repository default.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For working-copy content, split selected whole-file groups into ordered changes, describe each according to project instructions and the syntax observed in `jj log`, and create one bookmark at each layer tip. Use `jj new <parent>` and `jj rebase -s <change> -d <parent>` when a layer must be relocated. Stop on conflicts instead of resolving them without direction. Do not impose a fixed message, prefix, type, scope, suffix, template, or example.

After the Jujutsu parent chain is complete and its bookmarks are exported to the colocated Git view, initialize or adopt the manager topology:

```bash
gh stack init --base "<base>" "<bottom-bookmark>" "<next-bookmark>"
```

Include every layer bookmark bottom-to-top. Run `gh stack view --json` and verify that the manager order matches the Jujutsu parent chain and that the top contains the complete intended work before submission.

## Submit (ready / non-draft)

Resolve `pr_teaching_archive` and the `archive:on|off` override first. If archival is enabled, stop before stack submission; do not append an unmanaged archival change after submission or silently disable requested archival.

Inspect managed PRs with `gh stack view --json` and `gh pr view`. Preserve existing draft state unless the user explicitly requested that every layer become ready. Submit without `--open` when a protected draft exists, then report remaining drafts as a residual before ordinary babysitting. Otherwise submit ready:

```bash
gh stack submit --auto --open
```

Map each PR created in this run to its head bookmark and explicit URL. Pass each URL through ordinary PR composition, then apply through `gh pr edit <pr-url>`. Existing stack PRs retain metadata unless rewriting was requested; pipeline mode preserves the no-rewrite default.

After submission, run `jj git fetch` for the involved remotes so local remote bookmarks reflect GitHub's accepted heads. Do not use another Git transport path.

## Managed-member boundary

Do not use `gh pr merge` for a managed member. Landing is owned by `gh stack merge`, either through `ce-babysit-pr` with `posture:stack-land` or by the user.

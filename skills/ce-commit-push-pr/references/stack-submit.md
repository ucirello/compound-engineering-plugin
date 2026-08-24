# Opt-in stack construction and submit recipes

Load this file only when stack mode is active. It soft-depends on the `gh stack` GitHub provider command and does not depend on another skill package.

Before ordinary Step 3, run Probe, Topology, and, when needed, Retrospective construction only. Step 5 alone runs Submit and applies metadata to PRs created in this run.

## Probe

Read `references/gh-stack-cli.md` before any provider mutation. Its backing-Git adapter gate governs every `gh stack checkout`, `gh stack init`, and `gh stack add`; a failed gate is a residual, not a synchronization task.

```bash
gh stack view --json
```

If `gh` or `gh stack` is missing, or stacked PRs are unavailable for this repository, stop with a clear residual when stack intent is required. When stack intent is only a standing preference, report the residual and use the ordinary single-PR route.

## Topology

When the user names a parent PR or bookmark, classify it and root the layers there. Resolve by PR number when available because that is what pulls GitHub stack metadata down. `references/gh-stack-cli.md` owns the provider command's exit meanings.

Classification can move the provider's checked-out head. Run it only after the backing-Git adapter gate proves that both views are clean and aligned. Record the current change ID, bookmark, and Jujutsu operation before classification; after the provider checkout, re-establish alignment through the verified colocated adapter and confirm the expected change before construction. If clean synchronization cannot be proven, stop instead of restoring or moving state speculatively.

- **Managed parent**: plan from the recorded feature line, return to the named parent with `gh stack checkout <parent-pr-number>`, and use `gh stack add <layer-bookmark>` only when that parent is the confirmed top. Exit 5 is a residual; do not use `gh stack top` because it would choose a different parent.
- **Standalone parent**: resolve it with `gh pr view <ref> --json headRefName,headRefOid,author`. Fetch its remote bookmark with `jj git fetch`, verify the resulting revision matches `headRefOid`, and create a local bookmark at that revision only when the name is absent. If the name exists at another revision, stop rather than moving it. Use the parent bookmark as the `gh stack init --base` trunk, or adopt it as the bottom layer only when the current user owns it.
- **Unproven parent**: stop with a residual rather than guessing.

When `gh stack view --json` confirms managed topology, preserve it. Otherwise use retrospective construction. A standing preference alone does not justify artificial layers: when the user did not explicitly request a stack and the complete work is one logical change, use the single-PR path.

For an explicitly directed upstack layer, fetch and verify the authoritative parent bookmark. Prefer `<parent>@<tracking-remote>` when current; use the local parent bookmark only when its latest work is intentionally unpublished. Create a new Jujutsu change on that parent with `jj new <parent-ref>`, then create the layer bookmark only after the layer commit exists. Do not use `references/bookmark-creation.md` for an upstack layer because that reference roots work on the repository default.

## Retrospective construction

Inspect the complete change set against the resolved base with `jj log` and `jj diff`: existing revisions plus the working-copy change. Derive the smallest useful linear set of independently reviewable layers in dependency order. Use whole-file groups or existing revision boundaries. When a safe split requires hunk selection or rewriting published revisions, ask first; in `mode:pipeline`, stop with a residual rather than guessing or rewriting.

Choose the bottom parent from Topology. If construction starts from the default bookmark with no named parent, follow `references/bookmark-creation.md`. If it starts from an existing feature line, fetch the resolved base remote bookmark and use that exact revision. Record the original change ID and Jujutsu operation before rewriting so `jj op restore <operation-id>` remains an explicit recovery route; never restore automatically if later external writes have occurred.

Files named by `exclude:<paths>` belong to no layer. Leave them in the working-copy change, path-limit every layer commit, and stop if an external provider checkout would overwrite them.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime conventions and observed history win. Apply compatible Go guidance, preserve required semantic context such as a known implementation-unit identifier, and do not impose a fixed prefix, type, scope, or template.

For uncommitted whole-file groups, rebase `@` onto the resolved bottom parent, then commit each group and create its bookmark at the completed revision. Each `jj commit` creates the next empty working-copy change on top, which becomes the next layer's workspace. Before `gh stack init`, the adapter gate must verify that this working-copy change is empty and every layer bookmark has an identical provider branch; otherwise stop without initializing the stack.

```bash
jj rebase -r @ -o <base-ref>
jj commit -m "<bottom-message-derived-from-current-conventions>" <bottom-files>...
jj bookmark create <bottom-bookmark> -r @-
jj commit -m "<next-message-derived-from-current-conventions>" <next-files>...
jj bookmark create <next-bookmark> -r @-
gh stack init --base <base-bookmark> <bottom-bookmark> <next-bookmark>
```

Add only as many layer pairs as the plan requires. When existing Jujutsu revision boundaries already match the plan, create or reuse bookmarks at those revision tips and adopt them bottom-to-top with `gh stack init`. Reuse a feature bookmark only when its unchanged target is a planned tip.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

After construction, compare `gh stack view --json` with `jj log` and verify the top layer contains the complete original change set while excluded paths remain in `@`.

## Submit

Before submit, resolve the ordinary `pr_teaching_archive` / `archive:on|off` gate. If archival is on, stop with a residual before `gh stack submit`; do not create an explainer commit after submission or silently disable requested archival.

Inspect managed open PRs for existing draft layers. If any draft was not explicitly authorized to become ready, submit without `--open` and treat remaining drafts as a residual before babysit when babysit is on.

When no existing drafts remain, or the user explicitly authorized opening every layer:

```bash
gh stack submit --auto --open
```

After submit, map every PR created in this run to its head bookmark and explicit PR URL. For each new PR, pass that URL to ordinary PR-description composition so PR mode derives the immediate parent and exact head, then apply it with `gh pr edit <pr-url>`. Existing stack PRs retain their titles and bodies unless this invocation explicitly requests a rewrite; `mode:pipeline` retains the conservative no-rewrite default.

Managed members are landed only through `gh stack merge`, owned by babysit under `posture:stack-land` or by the user. Step 5 exclusively owns stack submission and post-submit metadata for PRs created in this run.

# Opt-in Stack Construction and Submission

Load this file only in Stack mode. `gh stack` manages GitHub stack metadata; Jujutsu owns local changes, bookmarks, parentage, workspace state, and Git transport.

Before ordinary Step 3, run Probe, Topology, and, when needed, Retrospective construction. Step 5 alone runs Submit and applies metadata.

## Probe

Run `gh stack version`, `gh stack view --json`, and applicable live help as separate calls. Load `references/gh-stack-cli.md` for the decision contract. Required stack intent stops when the extension, repository support, or colocated exported-bookmark state is unavailable. Soft intent reports the residual and returns to one-PR creation.

## Topology

When the user names a parent PR or bookmark, classify it and root the layers there. Prefer a PR number because it identifies GitHub state; a name alone establishes local manager state only.

Classification can move the colocated checkout. Record the current Jujutsu change ID and intended work bookmark before classifying, then restore the intended work with `jj edit <change>` before construction. Never recover by moving an unrelated bookmark or abandoning a change.

- A parent already in a managed stack must remain the named parent. Add above it only when it is the top; otherwise stop with a residual rather than selecting another parent.
- A standalone PR parent must resolve to its exact `headRefOid` and a safe local bookmark. Create the bookmark at the fetched change when absent. If the name already targets different work, stop rather than moving it. A parent the current user does not own can serve as trunk but must not be adopted as a managed layer.
- An unproven parent, ambiguous manager state, or repository without stack support is a residual rather than a guessed topology.

Require each bookmark name obtained from GitHub to pass Jujutsu's bookmark-name acceptance and a conservative Git-host interchange form before use. Pass names as separate quoted arguments; never interpolate them into shell expressions.

When manager JSON confirms that exported bookmark names form a managed stack, preserve that topology. If none exists, use retrospective construction. When stack intent is not explicit in the current request and the work is one logical change, use one PR.

For an explicitly requested upstack layer, fetch through `jj git fetch` and choose the authoritative parent change: use the tracked remote bookmark when it contains the parent's latest work, otherwise use the confirmed local parent bookmark. Start the child with `jj new <parent-bookmark>`.

Before composing, editing, checking, recommending, or exemplifying the child description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Use `jj describe -m "<message composed from the standards above>"` after deriving the message from project instructions and runtime history. Then create the child bookmark. Do not use the default-bookmark creation flow for an upstack layer.

## Retrospective Construction

Inspect `trunk()..@` and the current working-copy diff. Derive the smallest useful linear set of independently reviewable layers in dependency order. Each layer must work against its parent and must not depend on a child. Preserve coherent existing change boundaries; use `jj split <files>` only for whole-file groups. When `exclude:<paths>` is present, select only intended files into the layer chain and leave excluded paths in an unbookmarked descendant working-copy change. Verify that no excluded path occurs in any layer diff before creating or moving layer bookmarks.

One clear topology may proceed because explicit stack intent authorizes required local changes and bookmarks. Ask when multiple reasonable topologies materially change review boundaries. Pipeline mode returns that choice as a residual. Hunk-level partitioning or rewriting published changes requires explicit confirmation; pipeline mode stops rather than rewriting.

If construction begins from the default bookmark, follow `references/branch-creation.md` for fetch and base resolution. From an existing feature bookmark, fetch the default remote bookmark, verify its target, and use that exact change as the bottom parent. Preserve the original tip with a recovery bookmark before any rebase or split that could make recovery difficult. When Topology resolved a named parent, use that parent instead of the repository default.

For every layer description composition, edit, check, recommendation, command template, or example: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Use `jj split`, `jj new`, and the narrowest correct `jj rebase` selector to form the chain. Describe each layer with `jj describe -r <change> -m "<message composed from the standards above>"`, following project instructions and runtime history and applying only compatible Go guidance. Do not impose fixed message syntax. Stop on conflicts instead of resolving them without direction. Create one bookmark at each layer tip.

After the Jujutsu parent chain is complete and its bookmarks are exported to the colocated Git view, initialize or adopt the manager topology with the runtime-supported `gh stack init` form. Include every layer bookmark bottom-to-top. Run `gh stack view --json` and verify that manager order matches Jujutsu parentage and that the top contains the complete intended work before submission.

## Submit

If archival is enabled, stop before stack submission; do not append an unmanaged archival change after submission or silently disable requested archival.

Inspect managed PRs with `gh stack view --json` and `gh pr view`. Preserve every existing draft unless the user explicitly requested that all affected layers become ready. Use the runtime-supported submit form from live help. A draft-only outcome is a residual before ordinary babysitting.

Map every PR created in this run to its head bookmark and explicit URL. Pass each URL through ordinary PR composition, then apply through `gh pr edit <pr-url>`. Existing stack PRs retain metadata unless rewriting was requested; pipeline mode preserves the no-rewrite default.

After submission, run `jj git fetch` for each involved remote so local remote bookmarks reflect accepted GitHub heads. Do not use another Git transport path.

Do not use `gh pr merge` for a managed member. Landing is owned by `gh stack merge`, either through `ce-babysit-pr` with `posture:stack-land` or by the user.

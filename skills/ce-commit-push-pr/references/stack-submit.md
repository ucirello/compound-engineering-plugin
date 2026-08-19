# Opt-In Stack Construction and Submission

Load this reference only when stack intent is active. Before ordinary Step 3, run Probe, Topology, and Retrospective Construction. Step 5 alone runs Submit and applies metadata.

## Probe

Run `gh stack view --json`. If `gh`, the extension, or repository support is unavailable, explicit stack intent is blocked; soft intent reports the residual and returns to one PR. Read `references/gh-stack-cli.md` before crossing between Jujutsu and manager state.

## Topology

When the user names a parent PR or bookmark, identify it by PR number where possible and root the stack there. Record the current Jujutsu change ID, bookmark, and tip before manager classification. After any `gh stack checkout`, run `jj git import` and restore the recorded work with `jj edit <change-id>` before construction; otherwise the parent can be mistaken for the work to partition.

- If the parent is managed, add only above that exact parent. Exit 5 from `gh stack add` means it is not the top and is a residual; do not reparent through `gh stack top`.
- If the parent is standalone, obtain `headRefName` and `headRefOid` with `gh pr view`. Fetch the head through `jj git fetch` when a matching remote bookmark exists; otherwise import the pull ref through the colocated Git boundary and verify the resulting commit. Create or set a Jujutsu bookmark only after confirming it targets that exact commit. Never move a same-named bookmark whose ownership is uncertain.
- If parent identity or topology remains unproven, stop rather than creating a second stack.

An explicit upstack bookmark starts from the authoritative parent tip: use the current local parent when it contains unpublished work, otherwise the freshly fetched remote bookmark. Create the child with `jj new <parent-tip>` and `jj bookmark create <child> -r @`. Do not use default-line bookmark creation for an upstack layer.

Preserve an existing managed topology. Without one, use retrospective construction. A standing preference does not justify artificial slices when the request itself did not ask for a stack; an explicit stack request does.

## Retrospective Construction

Inspect the complete range from resolved base to the working change, including all committed Jujutsu changes and current tracked content. Build the smallest useful linear set of independently reviewable layers in dependency order. Prefer existing change boundaries or whole-file filesets. Hunk-level `jj split -i` and rewriting already-pushed changes require explicit confirmation; pipeline mode stops with the proposed partition instead.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and observed repository history always win. Apply compatible Go clarity and structure guidance from the main skill to every layer description without imposing fixed syntax or examples. Append an already-known Implementation Unit ID in parentheses when one unambiguously belongs to that layer; do not search for a plan.

For each planned layer, create a Jujutsu change on its immediate parent, select only its filesets, and describe it:

```bash
jj new <parent-revision>
jj commit -m "<description derived from local standards and history>" <fileset>...
jj bookmark create <layer-bookmark> -r <described-tip>
```

Files in `exclude:<paths>` belong to no layer and must remain outside every selected fileset. If preserving them across the planned topology is not possible without clobbering content, stop. After every layer, verify its diff against its parent. Before manager adoption, verify the top contains the complete intended original change set and excluded content is absent.

Export the completed bookmarks and adopt them bottom-to-top:

```bash
jj git export
gh stack init --base "<base-bookmark>" "<bottom-bookmark>" "<next-bookmark>"
jj git import
```

Run `gh stack view --json` and verify manager order, bookmark targets, and top-layer completeness. A mismatch is a blocker.

## Submit

Resolve `pr_teaching_archive` and `archive:on|off` first. If archival is on, stop before submission; stack archival has no manager-safe route here.

Inspect existing stack PRs for drafts. Do not pass `--open` when it would ready a draft the user did not authorize. Submit with `gh stack submit --auto` in that state and report remaining drafts as a residual before default babysitting. Otherwise submit ready PRs:

```bash
gh stack submit --auto --open
```

After submission, run `jj git import` and verify local state. Map each newly created PR to its explicit head bookmark and URL. Compose and apply each new PR body against its immediate parent with `gh pr edit <pr-url>`. Existing PR bodies remain unchanged unless this invocation requested a rewrite; pipeline mode defaults to no rewrite.

Managed members land only through `gh stack merge`, owned by `ce-babysit-pr` under `posture:stack-land` or by the user.

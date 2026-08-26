# Describing changes and pushing

If the stack reference constructed retrospective layers before this step, skip ordinary single-bookmark commit/push and continue to Step 4; `gh stack submit` in Step 5 pushes the stack.

If the work is rooted on the default bookmark, feature-bookmark creation must account for local-only changes and a fresh remote base. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan the working-copy change for naturally distinct concerns. If files clearly group into separate logical changes, create two or three changes at most. Group at file level only; when ambiguous, keep one change.

Use explicit filesets for each group. **Honor `exclude:<paths>` when the invocation carries it:** excluded files remain in the working-copy change and never enter a completed fileset. When a plan Implementation Unit ID is already in hand and maps unambiguously to a change, preserve that semantic reference without forcing fixed syntax. Do not hunt for a plan.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Project instructions and runtime `git log` syntax win.

```bash
jj commit <included-filesets> -m "<message composed from the standards above>"
```

With filesets, selected paths stay in the completed change and all other paths move to the new working-copy change. Repeat for each group. Do not use an unbounded fileset while excluded or unrelated work exists.

After the final `jj commit`, set the feature bookmark to `@-`; bookmarks do not advance automatically. Immediately before pushing, verify that the intended bookmark targets the completed change and that its remote state is current:

```bash
jj bookmark set <bookmark> -r @-
jj git push --bookmark <bookmark> --remote origin
```

If the working-copy change is empty and the bookmark already matches its remote bookmark, this step is a no-op.

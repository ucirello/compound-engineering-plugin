# Describing changes and pushing a bookmark

If stack construction already described all retrospective layers, skip this file's single-bookmark flow and continue to PR composition.

When work is based on the default bookmark, read `references/branch-creation.md` and resolve the exact parent before publication. A JJ working-copy change is already tracked without staging; never introduce an index or stash workflow.

## Group and describe

Use `jj status`, `jj diff --summary`, and `jj diff` to identify the complete work. Group naturally separate concerns into the smallest useful set of linear changes, normally no more than three. Use whole-path filesets; do not use interactive hunk selection merely to manufacture a split. One change is correct when boundaries are ambiguous.

`exclude:<paths>` removes those paths from every fileset in this run. Because `jj commit <filesets>` leaves unselected content in the new working-copy change, verify after each commit that excluded content remains only there and that the published ancestry does not contain it.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime project instructions and recent history determine the message. Compatible Go guidance means a concise summary and, when useful, a body that explains why and the resulting behavior. Use dynamic `<message-derived-from-local-standards>` content; do not impose a fixed prefix, type, scope, subject, or body template. Append a known Implementation Unit ID only when runtime conventions permit it and the change maps unambiguously to one supplied unit; do not search for a plan.

Commit each whole-path fileset:

```bash
jj commit -m "<message-derived-from-local-standards>" <fileset>...
```

After each command, use `jj show <created-change>` and `jj status` to validate content and residual paths. If the description needs correction, the same message rule above governs `jj describe <created-change> -m "<revised-message-derived-from-local-standards>"`.

## Place and push

Set `<publish-change>` to the final intended described change, not automatically `@`: after `jj commit`, `@` is the new working-copy change and the committed change is its parent. Create or safely advance the feature bookmark per `references/branch-creation.md`.

Re-verify bookmark target and remote, then push exactly that bookmark:

```bash
jj git push --remote <remote> --bookmark <bookmark>
```

JJ push safety is lease-like and depends on fetched remote state. On a rejection, fetch the same named remote, resolve bookmark conflicts or changed remote state, and retry only after the intended target is still proven. Do not switch to an all-bookmark push. A clean working-copy change does not prove the bookmark is already pushed; compare local and remote bookmark targets.

# Committing and pushing

If the stack reference constructed and described retrospective layers before this step, skip ordinary single-bookmark publication and continue to Step 4; Step 5 pushes the stack bookmarks.

If the work starts from trunk, read `references/bookmark-creation.md`. It protects the decision between a fresh remote base and unpublished local base changes without relying on Git's current-branch or stash model.

Scan the complete unpublished range and working-copy change for naturally distinct concerns. If whole-file groups form separate logical changes, use path-limited `jj commit` or `jj split` to produce the smallest useful sequence. When the boundary is ambiguous, keep one change. Do not use an interactive hunk split unless the user explicitly approves that review boundary.

Jujutsu snapshots visible working-copy files and has no staging area. Pass each group's filesets to `jj commit` so only that group remains in the described change and the rest moves to the new working-copy change. **Honor `exclude:<paths>`:** excluded paths belong to no published change, and the report names them. If ignored or generated content is already tracked in the current change, separate or untrack it before publication rather than relying on an index.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository instructions and the syntax established by `git log` always win. Apply compatible Go guidance where those sources leave room, including a history-useful first line and rationale in the body when needed. Do not force a type, scope, prefix, subject grammar, body, or Conventional Commit form. When a plan Implementation Unit ID is already in hand and the repository's syntax permits it, include that unit ID without changing the established message form. Do not hunt for a plan; omit it when the change spans units or the unit is unclear.

Pass the composed description directly as one argv value to `jj commit --message` or `jj describe --message`; do not substitute a fixed message placeholder. After each operation, inspect `jj show` and `jj status` to verify the change has exactly its intended files and description and that excluded paths remain outside the publication range.

Move or create the feature bookmark at the intended completed change. An empty working-copy child normally means the bookmark targets `@-`; a still-active described working-copy change may target `@`. Verify the exact target instead of assuming either shape. Re-check the bookmark, push remote, and remote bookmark immediately before publication:

```bash
jj git push --remote <push-remote> --bookmark <bookmark>
```

If the bookmark and its tracked remote bookmark already agree and no unpublished changes belong to the PR, this step is a no-op. On a stale or conflicted remote-bookmark refusal, fetch and reconcile; never bypass Jujutsu's safety checks.

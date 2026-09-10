# Describing changes and pushing

If the stack reference constructed and committed retrospective layers before this step, skip ordinary single-bookmark commit/push and continue to Step 4; `GIT_DIR="$(jj git root)" gh stack submit` in Step 5 pushes the stack.

If the work is rooted on the default bookmark, bookmark creation needs to handle a stale local `<base>`, local-only changes on local `<base>`, and working-copy content that collides with the fresh remote base. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate JJ changes (2-3 max). Group at file level only — no interactive hunk split. When ambiguous, one change is fine.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in git log, compose commit messages adherent to the present standards. Then: repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax.

Complete each group with an explicit fileset. **Do not pass an unbounded fileset** — that sweeps in `.env`, build artifacts, and generated files. **Honor `exclude:<paths>` when the invocation carries it:** a caller names files that must stay in the working-copy change (typically a user's own in-progress edits it could not separate from its work); never include them in a completed fileset, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), preserve that unit's U-ID as a constraint on the composed message — `(U3)` means unit 3. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit file1 file2 file3 -m "<message composed from the standards above>"
```

The fileset on `jj commit` is load-bearing: a bare `jj commit` describes the whole working-copy change, so excluded paths or work the user did not name would ride into the completed change. Naming the paths keeps exactly that group in the completed change and moves every other path to the new working-copy change.

After the final `jj commit`, set the feature bookmark to the completed parent — bookmarks do not advance automatically. Immediately before pushing, re-confirm the intended feature bookmark targets that completed change (`jj bookmark list -r @-`) — the bookmark gathered in Context is a hint, and Step 1 may have created or moved bookmarks since. Push the bookmark, never a stale name:

```bash
jj bookmark set <bookmark> -r @-
jj git push --bookmark <bookmark> --remote origin
```

If the working-copy change is empty and the bookmark already matches its remote bookmark, this step is a no-op.

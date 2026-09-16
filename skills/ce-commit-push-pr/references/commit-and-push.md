# Describing changes and pushing

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark commit and push and continue to Step 4 (compose the PR title and body); `gh stack submit` in Step 5 (apply and report) pushes the stack.

If you are on the default bookmark, creating the feature bookmark has to handle three things: a stale local `<base>`, unpublished local changes on local `<base>`, and working-copy content that collides with the fresh remote base. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only — no hunk-level split. When ambiguous, one commit is fine.

Commit each group with an explicit fileset. There is no staging area; the working copy is the change. **Honor `exclude:<paths>` when the invocation carries it.** The caller names files that must stay uncommitted, typically the user's own in-progress edits it could not separate from its work. Never include them in a fileset, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins. Do not impose a fixed type, scope, prefix, footer, or body template.

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

`jj commit` has no `-F`; do not feed the message through a shell redirect. A fileset-less `jj commit` takes the whole working copy, so `exclude:` paths or files belonging to a later logical group would ride into the change. Naming the paths commits exactly the group and leaves other working-copy paths alone.

Then apply the **Project publishing gate**. `jj commit` does not move bookmarks forward: after the final `jj commit`, set the feature bookmark to `@-`. Immediately before pushing, re-confirm the intended feature bookmark targets the completed change with `jj log -r @- --no-graph -T bookmarks` and `jj bookmark list`. The bookmark gathered in Context is a hint, and Step 1 (resolve bookmark and PR state) may have created or moved bookmarks since. Push that bookmark, never a stale name:

```bash
jj bookmark set <bookmark> -r @-
jj git push --bookmark <bookmark>
```

If the working-copy change is empty and the bookmark already matches its remote bookmark, this step is a no-op.

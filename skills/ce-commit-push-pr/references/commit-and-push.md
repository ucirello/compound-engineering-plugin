# Committing and pushing

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark change and push and continue to Step 4 (compose the PR title and body); `gh stack submit` in Step 5 (apply and report) pushes the stack.

If you are on the default/trunk bookmark, creating the feature bookmark has to handle three things: a stale local `<base>`, unpushed changes on local `<base>`, and working-copy changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repo-local syntax. Do not choose commit-message syntax here; the executing agent determines it at runtime from those sources.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate changes (2-3 max). Group at file level only — no interactive hunk split. When ambiguous, one change is fine.

The working copy is the change; there is no staging area. **Honor `exclude:<paths>` when the invocation carries it.** The caller names files that must stay out of the described change, typically the user's own in-progress edits it could not separate from its work. Never include them in the fileset, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

Path filesets on `jj commit` put those paths in the current change and move remaining working-copy changes to a new change on top. Naming the paths describes exactly the group and leaves excluded or unnamed paths in the working copy.

Then apply the **Project publishing gate**. Immediately before pushing, re-confirm the intended feature bookmark still names the change to publish (`jj bookmark list <bookmark-name>`). The bookmark gathered in Context is a hint, and Step 1 (resolve bookmark and PR state) may have created bookmarks since. After `jj commit`, `@` is a new empty change and the feature bookmark stays on the described change — push that bookmark, never a stale name, and never the trunk bookmark:

```bash
jj git push --bookmark <bookmark-name>
```

If the working copy is empty and all changes on the feature bookmark are already pushed, this step is a no-op.

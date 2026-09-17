# Committing and pushing

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark commit and push and continue to Step 4 (compose the PR title and body); `gh stack submit` in Step 5 (apply and report) pushes the stack.

If you are on the trunk bookmark, creating the feature bookmark has to handle three things: a stale local `<base>`, unpushed commits on local `<base>`, and uncommitted changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate changes (2-3 max). Group at file level only — no interactive hunk splits. When ambiguous, one change is fine.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from the Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax. Do not choose a type, scope, prefix, or subject template.

Describe and finish each group. **Do not snapshot or commit the whole tree blindly** — that sweeps in `.env`, build artifacts, and generated files. Name the paths that belong in the change. Untracked paths that must enter it need `jj file track` on those paths. **Honor `exclude:<paths>` when the invocation carries it.** The caller names files that must stay uncommitted, typically the user's own in-progress edits it could not separate from its work. Never describe or commit them, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3 — as a constraint on the composed message. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit -m "<message composed from the standards above>" -- file1 file2 file3
```

The fileset on `jj commit` matters. A bare `jj commit` takes the whole working-copy change, so anything already in `@` (a caller's `exclude:` paths, or work the user did not name) would end up in the change. Naming the paths commits exactly the group and leaves other working-copy paths in the new working-copy change on top.

After finishing the change(s), point the feature bookmark at the latest described change (`jj bookmark advance <bookmark> --to @-` when `@` is the new empty working copy) so the bookmark, not a detached working copy, is what gets published.

Then apply the **Project publishing gate**. Immediately before pushing, re-confirm the intended feature bookmark with `jj bookmark list -r @`. The bookmark gathered in Context is a hint, and Step 1 (resolve bookmark and PR state) may have created or moved bookmarks since. Push that bookmark so it reflects the current change, never a stale name:

```bash
jj git push --bookmark <bookmark>
```

If the working copy is clean and all commits are already pushed, this step is a no-op.

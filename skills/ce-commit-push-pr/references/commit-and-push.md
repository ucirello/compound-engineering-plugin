# Committing and pushing

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing local syntax.

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark commit and push and continue to Step 4 (compose the PR title and body); `gh stack submit` in Step 5 (apply and report) pushes the stack.

If you are on the default bookmark, creating the feature bookmark has to handle three things: a stale local `<base>`, unpushed commits on local `<base>`, and uncommitted changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only — no interactive split (`jj commit -i` / `jj split -i`). When ambiguous, one commit is fine.

Describe and commit each group. **Never run `jj commit` without filesets** — that snapshots the whole working copy, including `.env`, build artifacts, and generated files. **Honor `exclude:<paths>` when the invocation carries it.** The caller names files that must stay uncommitted, typically the user's own in-progress edits it could not separate from its work. Never include them in a fileset, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

The fileset list on `jj commit` matters. A bare `jj commit` takes the whole working copy, so anything already in the change before this run (a caller's `exclude:` paths, or work the user did not name) would end up in the commit. Naming the paths commits exactly the group and leaves other working-copy files alone.

Then apply the **Project publishing gate**. Immediately before pushing, re-confirm the intended feature bookmark with `jj log -r @ -T 'bookmarks ++ "\n"' --no-graph` (or `jj bookmark list -r @`). The bookmark gathered in Context is a hint, and Step 1 (resolve bookmark and PR state) may have created or moved bookmarks since. Point the feature bookmark at the change to publish — after `jj commit`, that is typically `@-` because `jj commit` does not move bookmarks — then push that bookmark, never a stale name:

```bash
jj git push --bookmark <bookmark>
```

If the working copy has no file changes and all commits are already pushed, this step is a no-op.

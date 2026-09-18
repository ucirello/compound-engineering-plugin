# Committing and pushing

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark commit and push and continue to Step 4 (compose the PR title and body); `gh stack submit` in Step 5 (apply and report) pushes the stack.

If you are on the default bookmark, creating the feature bookmark has to handle three things: a stale local `<base>`, unpublished commits on local `<base>`, and working-copy changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only — no interactive hunk split (`jj split -i` / `jj squash -i`) to force a layer. When ambiguous, one commit is fine.

There is no index. Never invent a staging step. **Honor `exclude:<paths>` when the invocation carries it.** The caller names files that must stay out of the finished change, typically the user's own in-progress edits it could not separate from its work. Never include them on `jj commit --`, and say in the report that they were left out.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repo-local syntax from project instructions and `git log` always wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing local syntax. Do not apply a Conventional Commit template. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit -m "<message composed from the standards above>" -- file1 file2 file3
```

The trailing path list on `jj commit` matters. A bare `jj commit` finishes the whole working-copy change, so excluded paths (or work the user did not name) would end up in the commit. Naming the paths finishes exactly that group and leaves other working-copy files in the new `@`.

Bookmarks do not follow `jj commit`. After the last commit that should be on the PR, move the feature bookmark to that change (`jj bookmark move <bookmark> --to @-` when `@` is the new empty working copy, or `--to @` when the described change is still the working copy) before pushing.

Then apply the **Project publishing gate**. Immediately before pushing, re-confirm the intended feature bookmark with `jj bookmark list -r @` (and `-r @-` if `@` is empty). The bookmark gathered in Context is a hint, and Step 1 (resolve bookmark and PR state) may have created or moved bookmarks since. Push that bookmark, never a stale name:

```bash
jj git push --bookmark <bookmark>
```

If the working copy is empty of the named work and all of those commits are already on the remote bookmark, this step is a no-op.

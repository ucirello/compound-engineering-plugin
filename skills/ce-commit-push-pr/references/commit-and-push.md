# Committing and pushing

If the stack reference constructed and committed retrospective layers before this step, skip ordinary single-bookmark commit/push and continue to Step 4; `gh stack submit` in Step 5 pushes the stack.

If on the default bookmark, bookmark creation needs to handle stale local `<base>`, unpushed commits on local `<base>`, and working-copy changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only — no interactive hunk split (`jj commit -i` / `jj split -i`). When ambiguous, one commit is fine.

Commit each group. **Never pass `.` or the whole tree to `jj commit`** — that sweeps in `.env`, build artifacts, and generated files. **Honor `exclude:<paths>` when the invocation carries it:** a caller names files that must stay uncommitted (typically a user's own in-progress edits it could not separate from its work); never include them in the fileset, and say in the report that they were left out. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repo-local syntax from the project's active instructions and from `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing repo-local syntax: a short subject (many tools prefer under ~72 characters), imperative phrasing that completes "this change …", no trailing period, body only when motivation or trade-offs are not obvious from the subject, wrapped to ~72 when present. Do not use a fixed `type:` / `type(scope):` / `fix:` / `feat:` template unless that syntax is what the project instructions or recent `git log` already use. **Never use `!` or `BREAKING CHANGE:` without explicit user confirmation.**

```bash
jj commit -m "<message composed from the standards above>" -- file1 file2 file3
```

The fileset list on `jj commit` is load-bearing: a bare `jj commit` describes the whole working-copy change, so excluded paths or work the user did not name would ride into the commit. Naming the paths commits exactly the group; remaining working-copy changes move to a new child. JJ has no index.

Then push. Immediately before pushing, re-confirm you are on the intended feature bookmark (`jj log -r @ -T 'bookmarks.join("\n")' --no-graph` or `jj bookmark list -r @`) — the bookmark gathered in Context is a hint, and Step 1 may have created bookmarks since. Push that bookmark, never a stale name:

```bash
jj git push --remote origin --bookmark <bookmark>
```

`jj commit` does not move bookmarks forward, so after commit the feature bookmark still points at the described change. Push that bookmark.

If the working copy matches its parent (`jj diff` empty) and the bookmark is already on the remote, this step is a no-op.

# Committing and pushing with Jujutsu

If the stack reference constructed and committed retrospective layers before this step, skip ordinary single-bookmark commit/push and continue to Step 4; `gh stack submit` in Step 5 pushes the stack.

If the work is based directly on the default bookmark, read `references/bookmark-creation.md` and resolve the base before continuing.

Inspect the working-copy change with `jj status` and `jj diff`. Group only clearly distinct concerns into separate commits, with no more groups than the work naturally requires. Use whole-file filesets; when a safe split requires hunks, ask before using interactive `jj split`. When ambiguous, one commit is fine.

Honor `exclude:<paths>` when present. Path-limit every commit to its intended files so excluded or unrelated content remains in the new working-copy change. With filesets, `jj commit` keeps the selected paths in the completed commit and moves the remaining content into a new working-copy commit.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime conventions and descriptions visible in current `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, layout, template, tense, punctuation, line length, or example. Preserve any known implementation-unit identifier only when project conventions or the caller require it.

For each whole-file group:

```bash
jj commit -m "<message-derived-from-current-conventions>" <fileset>...
```

Before creating or updating the feature bookmark, verify the completed top commit and its description with `jj show @-` and verify excluded content remains in `@` with `jj status`.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

If `<bookmark>` does not exist, create it at the completed top commit. If it already identifies this feature line, advance it to the completed top commit. Do not move an unrelated bookmark or move one backward without explicit confirmation.

```bash
jj bookmark create <bookmark> -r @-
jj bookmark set <bookmark> -r @-
```

Run only the applicable bookmark command. Immediately before pushing, separately re-confirm the local target with `jj bookmark list <bookmark>` and remote targets with `jj log -r 'remote_bookmarks(exact:"<bookmark>")' --no-graph -T 'json(remote_bookmarks) ++ "\n"'`. Stop if the intended local target or remote is ambiguous. Then push that bookmark explicitly:

```bash
jj git push --remote <remote> --bookmark <bookmark>
```

If push safety checks fail, fetch that remote, resolve bookmark divergence or conflicts, and retry only when the intended target is still clear. If the working-copy change is empty and the bookmark already matches its remote, this step is a no-op.

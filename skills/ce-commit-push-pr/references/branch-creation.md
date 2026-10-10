# Feature bookmark creation from the default bookmark

Fetch the verified base remote from the absolute workspace root:

```bash
(cd "$workspace_root" && jj git fetch --remote origin)
(cd "$workspace_root" && jj log -r '<base>@origin..<verified-local-tip>')
```

If local default-bookmark commits are not on the refreshed base, show them and ask whether to carry them or leave them on the local base. Pipeline mode reports this decision as a residual. Never silently include foreign commits. Carry uses the verified local tip; leave uses the verified remote base and preserves the local bookmark and recovery references.

Create a collision-free feature bookmark at the chosen revision with `(cd "$workspace_root" && jj bookmark create "<feature-bookmark>" -r "<verified-tip>")`. Preserve working changes. If transferring owned changes to the fresh base is required, inspect their exact revision and use native `jj rebase` only for those owned unpublished revisions after preserving a recovery bookmark. Stop on conflicts or possible tracked/ignored/untracked collisions; never stash, reset, discard, or move excluded files. Do not rebase published history without explicit authorization.

On fetch failure, retain the current verified local tip and report that freshness is unverified; skip the unreliable remote comparison. Do not invent a base.

If isolation is needed, detect existing isolation first and invoke `ce-worktree` through the native harness lifecycle. Reuse its verified existing identity, even nondated; never recreate or rename it. New workspaces use a local creation date captured once and a meaningful `YYYYMMDD-<task/pr/revision-slug>` identity, normalized without double prefix, with the same registered name and destination basename under the source workspace's local `.tmp/`. Check registrations and destinations; suffix collisions `-2`, `-3`; retain names across retries/resumes/midnight.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "<dated-unique-name>" --revision "<verified-base>" "<absolute-owned-destination>")
(cd "<absolute-owned-destination>" && jj git colocation status)
```

Use supported harness-native creation/adoption and move the active session to that absolute root. Unsupported colocation/date identity is a compatibility blocker, not a Git fallback or permission bypass.

Retirement is separately authorized: stop workers, move the session to a surviving absolute root, verify exact registered name/path/run ownership and integration where required, preserve recovery bookmarks, copy/read back evidence outside the target, and inspect changes/conflicts/ignored/untracked content (snapshots do not protect ignored/untracked files). Never remove unclear, unrelated, still-referenced, or nondisposable content. Use `(cd "$surviving_workspace_root" && jj workspace remove "<verified-name>")`; verify deregistration AND directory disappearance. On warnings/failure preserve remaining state and report a blocker, never force-delete or use Git cleanup. `jj workspace forget` is only unregister-with-files-preserved. Bookmark deletion is separate; retain best/archive/recovery references and respect harness lifecycle authority.

See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-experts/ .

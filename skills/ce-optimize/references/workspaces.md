# Experiment workspace lifecycle

Use the latest [JJ workspace commands](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace). Run each JJ command at the absolute root of the workspace it operates on, not from the skill directory or via `jj -R` alone. List exact registration names and roots with `jj workspace list -T 'name ++ "\t" ++ root ++ "\n"'`.

## Allocate and recover

- Resolve the exact verified commit ID of the `optimize/<spec-name>` bookmark once for the batch. Discover the source root and existing isolation with `jj workspace root`, `jj workspace list`, and the harness's workspace information. An existing worker workspace may be reused only for the same experiment when its registered name, absolute path, run ownership, colocation and measured base still match. Recover its pending receipt or marker first. Never rename, reset, clean, or silently reuse unrelated or ambiguous isolation. Parallel experiments require distinct working copies; if that isolation is unavailable, report the blocker rather than editing the source workspace.
- Capture the local creation date once per allocation. Use `YYYYMMDD-optimize-<normalized-spec-slug>-exp-<NNN>` as both the workspace name and the basename below `<source-root>/.tmp/rocketclaw/optimize/workspaces/`. Verify the parent is ignored and contained inside the source root, with no symlink escape. Check registrations and filesystem collisions; choose `-2`, `-3`, etc. for a new allocation, never overwrite. Write and verify the planned name, absolute path, base commit, and experiment identity in `run_state.workspace_allocations` before creation; preserve them across retries, resumes, and midnight. A planned record alone does not prove ownership of a path. Existing valid isolation keeps its existing name. Source and result bookmarks are separate from workspace names.
- Prefer a harness's supported colocated JJ workspace lifecycle when it can honor the intended base, name and destination. Otherwise, when direct isolation is authorized and can be adopted by the worker, create it with JJ:

  ```bash
  (cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")
  (cd "$absolute_destination" && jj git colocation status)
  ```

  Confirm the registration, path and empty working-copy change directly atop the verified base. Mark the allocation verified, read it back, then give the OpenCode worker the verified absolute destination as its working directory, or use native session adoption if required. If creation, colocation or adoption cannot be verified, preserve any partial allocation for inspection and report the blocker.
- Before dispatch, copy the source root's regular `.env*` files except `.env.example` and any declared shared files or directories needed by the harness. Use repository-relative destinations for declared inputs. Verify source and destination containment (including symlinks); preserve the layout and copy only authorized inputs into the fresh, owned workspace. Do not expose secret values in prompts or logs, overwrite conflicting unrelated data, or destructively refresh a resumed workspace. Apply the configured port environment to the measurement. Shared inputs and markers are not candidate changes.

## Retire only disposable workspaces

Use the run's recorded allocations, not glob matches, for both per-experiment and final cleanup. Stop workers and leave the target; move any active OpenCode session there to a surviving workspace before removing it. Verify the exact registered name, absolute path and run ownership, and respect harness lifecycle authority and cleanup authorization. Prove integration for a keep; verify the decision and copy/read back the required results and recovery evidence outside the target. Preserve recovery references. Inspect the target for tracked changes, conflicts, and ignored or untracked files; the removal snapshot does not protect ignored or still-untracked files. Do not delete unrelated, ambiguous, referenced, or non-disposable content.

For authorized JJ-owned disposal, from the surviving workspace:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
```

Verify both deregistration and disappearance of the exact destination, even on a successful exit. If either check fails, retain what remains and report the blocker, without force deletion or another removal mechanism. `jj workspace forget` is for unregistering while retaining files, not disposal. Handle bookmark deletion separately and only after confirming it is no longer needed; preserve best, archive and recovery bookmarks.

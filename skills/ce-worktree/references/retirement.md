# Retire a JJ workspace

Respect harness-owned lifecycle and remove only a verified run-owned, disposable workspace under existing cleanup authorization. Stop its workers, leave the target, and move any active harness session to a surviving workspace. Verify the exact registered name, absolute path, and ownership. Inspect tracked changes, conflicts, and ignored or untracked files; ignored and still-untracked files are not protected by the removal snapshot. Prove integration when required, preserve recovery references, and copy required evidence outside the target and read it back before removal. Do not remove unrelated, ambiguously owned, still-referenced, or non-disposable content.

For a removable JJ workspace (not the main workspace), let JJ deregister it and delete its files and colocation metadata:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration and directory disappearance; directory-deletion failures can be warnings even on a successful exit. If either check fails, keep the remaining state and report the blocker. Do not force-delete the path or separately clean up colocation metadata. Use `jj workspace forget` only to unregister while leaving files in place. Bookmark deletion is separate; keep any bookmark needed for integration, archive, or recovery.

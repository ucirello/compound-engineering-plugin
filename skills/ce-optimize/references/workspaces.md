# Native experiment workspace lifecycle

Use OpenCode-native workspace/session tools and shell JJ instructions, not a bridge script. Run every JJ command with cwd equal to its target absolute workspace root; `-R` is not a cwd substitute. Never execute Git directly. Repository-scoped `gh` requires `GIT_DIR=$(jj git root)` from that root.

## Create and resume

Detect existing isolation first. Respect harness ownership and session adoption; do not nest or bypass its lifecycle. If the harness cannot support the naming or colocation contract, report a compatibility blocker. Resolve the optimization bookmark to exactly one verified commit and capture it in the ledger before creating experiments.

Capture ONE local `YYYYMMDD` date for the run and persist it before creation. Normalize a meaningful task/spec/experiment kebab slug without doubling an existing date prefix. Use the same `<YYYYMMDD>-<task-slug>-exp-<NNN>` identity for registration and destination basename. Check both `jj workspace list` registrations and filesystem destinations; collisions use `-2`, `-3`, etc. Persist the chosen name and absolute path before creation, and reuse that identity on retries, resumes and across midnight. Never substitute PID/random/timestamp names. Destinations are absolute children of the source workspace's `.tmp/rocketclaw/optimize/`.

From the surviving source absolute root, run `jj workspace add --colocate --name <verified-name> --revision <verified-base> <absolute-destination>`. From the created absolute root, require `jj git colocation status` to confirm colocation. Adopt the workspace with the native session lifecycle if it becomes the session's primary directory. A failed verification retains state for repair, not destructive retry. Reuse only an exact owned name/path/base match; never reset an existing workspace or clean its files to make a retry succeed.

Copy declared shared files and non-example `.env` files as before, after resolving source and destination symlinks and proving containment in their respective roots. Reject absolute paths, traversal and destinations under `.jj`/`.git`. Never overwrite unrelated or ambiguous existing data; stage copies under local `.tmp` and verify them. Count all registered experiment workspaces, including retained failed workspaces, against the budget; do not infer registration merely from directories.

## Dispose only verified disposable workspaces

Cleanup is not implied by a failed experiment. Stop workers and pending writes; leave the target and move/adopt the harness session to the surviving absolute root first. Verify exact registration name, canonical path, run ownership and cleanup authorization. Confirm integration of winners and recovery refs for rejected or unintegrated candidates. Preserve best, recovery and archive bookmarks; bookmark deletion is a separate authorized action.

Inspect tracked changes, conflicts, ignored and untracked data, including copied shared resources and secrets. A snapshot does not protect ignored/untracked files. Copy required markers, metrics, diffs and recovery evidence outside the target into the run's local `.tmp` evidence store, then read them back. Never remove unrelated, ambiguous, still-referenced or non-disposable data. If any check is uncertain, retain the workspace and report it.

Only after these checks, from the surviving absolute root run `jj workspace remove <verified-name>`. Require both deregistration and directory disappearance before marking cleanup complete. A warning/failure retains lifecycle state: no force-delete, manual recursive removal or Git fallback. `jj workspace forget` is exclusively unregister-and-preserve-files, never a deletion step. Apply this individually to every workspace in batch cleanup; no glob-based deletion.

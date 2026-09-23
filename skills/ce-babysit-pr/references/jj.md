# JJ execution contract

Read this before any local mutation or managed-stack operation. All JJ subprocesses run with the absolute workspace root as cwd. Resolve that root through `jj workspace root`; do not substitute `-R` for cwd. Every `gh` subprocess receives `GIT_DIR` from `jj git root` in that same workspace. Local branches in manager output correspond to named JJ bookmarks, not an implicit checked-out Git branch. An empty `@` may sit above the published head at `@-`.

Keep a verified head bookmark and tracking remote for every layer. Inspect history with `jj log`, changes with `jj diff`, conflicts with `jj resolve --list`, and remote/bookmark state with `jj git remote list` and `jj bookmark list --all-remotes`. No index or staging step exists. “Clean” means no unrelated work or unresolved conflicts; preserve any existing work before a target transition. Transition to a new empty child of the verified layer head with `jj new <head-bookmark>@<head-remote>`, never a Git checkout operation.

## Claimed local merge repair

The currency claim and positive mechanical-resolution evidence in `branch-currency.md` remain mandatory. Inspect the exact head/base trees and their common ancestors before mutation. If a non-mutating preview cannot establish the conflicted paths and the participating file contents, park the item rather than inventing certainty. A semantic fingerprint identifies sorted paths and their base/side file content identities, not Git index stages, and excludes unrelated base movement.

After claim and revalidation, create the exact merge with `jj new <observed-head-oid> <observed-base-oid>`, immediately record mutation-observed, resolve only the proven mechanical conflicts, and validate. Record the operation/change identity so interruption recovery can identify this attempt. A safe abort abandons only this owned unpublished merge after preserving unrelated work; never undo someone else's later operations. Before publishing, verify the exact remote head still matches the claim, advance only the target bookmark to the validated merge, and use `jj git push --remote <head-remote> --bookmark <head-bookmark>`. Preserve the exact-parent and remote-containment confirmation gates.

When describing that merge or composing any locally owned commit message:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Here `git log` means history inspected with `jj log` in this JJ workflow. Runtime project instructions and the observed history's message syntax override the Go guidance. Use `jj describe -m "<message composed from the standards above>"`, preserving the repair rationale and relevant issue/PR references.

## Remote stack manager and JJ propagation

GitHub's remote stack API is authoritative for membership and order, including stacks created by `gh stack link` without local tracking. The snapshot queries it directly. Read `references/stack-commands.md` for JJ-owned dependent propagation and exact-prefix async landing. These retain stack-wide monitoring, maintenance, and landing without requiring a local gh-stack checkout. Do not execute local gh-stack rebase/push/sync commands or infer managed membership from ancestry alone. Remote probe failure yields a residual; missing local tracking does not.

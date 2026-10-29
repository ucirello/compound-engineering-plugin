# Feature bookmark creation from the default bookmark

Use `context.md`'s absolute cwd. Fetch the verified base with `jj git fetch --remote <base-remote> --bookmark <base>` and resolve `<base>@<base-remote>` exactly. On fetch failure, continuing from the previously verified local head requires reporting that freshness was not verified; do not substitute another base or present stale divergence as fresh evidence.

Inspect `jj log --no-graph -r '<remote-base>..<local-head>' -T 'commit_id ++ "\n" ++ description ++ "\n"'`. If unpublished default-bookmark commits exist, show them and ask whether to carry them or leave them on the default. Pipeline mode stops with this decision as a residual; never silently carry foreign work.

Carry uses the verified local head; leave uses the fetched base and preserves local default commits and bookmark. Preserve a recovery bookmark before authorized rearrangement. Create a content-derived non-conflicting feature bookmark with `jj bookmark create <name> -r <verified-head>`; never move the default.

If working changes must move to a different parent, inspect tracked, untracked, ignored, excluded and conflicted content first. Use `jj rebase -r <owned-working-change> -d <verified-parent>` only when the entire change is owned and unrelated work cannot move. Otherwise stop for a safe decision; pipeline mode reports the blocker. Never stash, discard, overwrite ignored content or carry excluded paths into the PR. Verify resulting ancestry, bookmark and content.

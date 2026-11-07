# Feature bookmark from the verified base

From the absolute workspace root, fetch the verified remote/base with `jj git fetch --remote "<verified-remote>" --branch "exact:<verified-base>"` and resolve its exact commit. Substitute verified values without shell evaluation; the `exact:` selector targets only that branch name. A failed fetch blocks freshness-dependent publication: report it, never silently use a stale base.

Inspect full local ancestry absent from that remote base with `jj log`. If local default-base commits are unpushed, show them and ask whether to carry them into the feature or leave them on the existing base. Pipeline mode stops with that decision instead of guessing. Preserve existing bookmarks and recovery refs.

Create a nonconflicting semantic bookmark with `jj bookmark create <feature-name> -r <verified-feature-head>`. Do not move unrelated bookmarks. Stop on dirty/conflicted/ignored/untracked ambiguity before moving work; never stash, discard or overwrite collisions. Existing isolated workspaces are reused unchanged. This workflow does not create or delete workspaces; when isolation is needed load `ce-worktree` and require its verified colocated-workspace lifecycle instead of ad hoc helpers.

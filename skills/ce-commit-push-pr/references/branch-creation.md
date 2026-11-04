# Feature bookmark creation from the default bookmark

Run JJ from the target workspace's absolute root. Fetch with `jj git fetch --remote <verified-remote> --branch <base>`, then resolve `<base>@<remote>` to an exact commit. On failure, report unverified freshness; pipeline mode stops, otherwise ask before using a verified local base. Never guess another ref.

Inspect `jj log -r '<remote-base>..<local-head>'` for local commits not on the fresh base. If present, show them and ask whether to carry them onto the feature bookmark or leave them on the default. Pipeline mode returns this decision as a residual. Preserve existing references and work; never reset the default bookmark.

Create a derived collision-free feature bookmark with `jj bookmark create <feature-name> -r <verified-head>`. Full-workflow intent authorizes this without another question. JJ needs no branch checkout. If the selected base requires transplanting working changes, inspect tracked, untracked, ignored content and conflicts first. Rebase only run-owned unpublished changes onto an unambiguous destination, preserving recovery references. Stop on collisions, ambiguous ownership, conflicts, or possible loss rather than stashing, discarding, or overwriting work. Never rewrite published history without explicit authorization.

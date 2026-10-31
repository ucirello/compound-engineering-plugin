# Feature bookmark creation from the default bookmark

Use the absolute workspace root and scoped GitHub context from `context.md`.

1. Fetch the verified base with `jj git fetch --remote <remote> --branch <base>`.
2. Inspect `jj log --no-graph -r '<base>@<remote>..<verified-work-head>'`. If local default work is absent from the fetched base, show it and ask whether to carry it or leave it on the local default. Pipeline mode reports the decision as a residual, never guesses. Carry uses the verified local head; leave uses the exact fetched base and retains a recovery bookmark for local work.
3. Preserve tracked, ignored and untracked work. Never reset, discard, stash, or overwrite colliding paths. If working changes cannot safely stay at the chosen parent, stop for a decision (pipeline: residual). With a clean working copy, `jj new <verified-base>` starts work at the chosen parent. Create a collision-free feature bookmark at the intended revision with `jj bookmark create <branch-name> -r <verified-work-head>`. Do not move the default or others' bookmarks.

On fetch failure, retain local work and report base freshness unverified. A local feature bookmark may preserve that exact head, but do not pretend an unpushed comparison is fresh or publish against an uncertain target.

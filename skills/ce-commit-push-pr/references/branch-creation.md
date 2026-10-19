# Feature bookmark and verified base selection

Use the absolute workspace cwd and GitHub context in `context.md`. Fetch with `jj git fetch --remote <verified-remote>`, then inspect `jj log -r '<base>@<remote>..<local-tip>'`. Local base work may belong to another session or the user; JJ cannot infer intent.

- No additional local commits: use the verified fetched base revision.
- Additional local commits: show them and ask whether to carry them into the feature or leave them on the local base. Pipeline mode returns a residual instead of guessing. Preserve the original tip with a recovery bookmark before topology changes.
- Fetch failure: report freshness as unverified; use an already verified local tip only where permitted, and do not present an unpushed-commit comparison as fresh.

Create the feature bookmark with `jj bookmark create <feature-name> -r <verified-revision>`. A bookmark does not switch the working copy. Only if a base change is needed and authorized, use JJ revision operations after inspecting tracked, untracked and ignored content and conflicts. Stop on colliding or unrelated work; never stash, discard, reset, or remove it. A named stack parent replaces the default base and remains authoritative.

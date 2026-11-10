# Safe feature bookmark creation

Operate from the verified absolute JJ workspace root. Reuse existing isolation and preserve native harness ownership; naming work does not require another workspace. Resolve and fetch the actual default base via `context.md` and verify its revision.

Inspect local-only changes and working contents, including conflicts, ignored and untracked paths. Preserve local work and others' authorship. Never reset, stash, discard, or move work onto a stale or guessed base. If the work cannot safely use the verified base without altering unrelated work, stop with the required decision; pipeline mode reports the blocker without asking.

Derive a meaningful feature bookmark from the task, check local and remote collisions, and select a nonconflicting suffix. Use `jj bookmark create <feature> -r <verified-work-head>` and verify the target. Never publish the default bookmark. Upstack layers use their verified immediate parent, not the default base.

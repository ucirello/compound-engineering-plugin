# Describing and publishing the refresh

Skip if no files changed. Use `jj status`, `jj diff --summary -r @`, `jj bookmark list -r @`, and `jj log -r :: -n 10` to identify the working-copy change, unrelated modifications, bookmarks, and description style. Keep only refresh-owned files in the described change: use `jj split <refresh-paths> -m '<change-description>'` when unrelated work shares `@`; otherwise use `jj describe -m '<change-description>'`.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.

Non-interactive mode creates a neutral feature bookmark when work is directly on `trunk()` and no feature bookmark identifies it, moves that bookmark to the described revision, pushes it, and attempts a PR. With an existing feature bookmark, update and push it. Report Jujutsu or provider failures without blocking completed document maintenance.

Interactive mode asks with the recommended safe publication route first. At `trunk()`, offer feature bookmark and PR, direct default-bookmark update, or local described change. On feature work, offer updating its bookmark, a separate bookmark, or local described change. Split refresh paths before any ref update when unrelated work shares `@`.

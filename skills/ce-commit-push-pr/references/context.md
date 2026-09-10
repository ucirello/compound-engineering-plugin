# Repository context, bookmark, and PR state

Gather this before Step 1, and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `GIT_DIR="$(jj git root)" gh pr create` in Step 5).

Gather the repository context by running each `jj` command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly — a non-zero exit is a normal state to interpret (no PR yet, no default bookmark, empty working-copy change), not a failure to suppress.

This skill pins two compound recipes: (1) pair every `gh` invocation with `GIT_DIR="$(jj git root)"` so GitHub CLI can see the backing Git repository — if `jj git root` fails, the workspace is not Git-backed and GitHub CLI pairing is impossible, so report and stop; (2) write the PR body under the workspace `.tmp` directory and pass `--body-file` (owned by `references/apply-and-handoff.md`).

Run them in order — the existing-PR check needs a bookmark name from `jj bookmark list -r @`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ workspace — report and stop |
| `jj status` | Working-copy state | (fails only outside a workspace) |
| `jj diff` | Working-copy change vs parent | Empty change |
| `jj bookmark list -r @` | Local bookmarks targeting `@` (`<bookmark>`) | Empty = no bookmark on the working-copy change (Step 1 handles it) |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent change / PR-title style | Empty history |
| `jj git remote list` | Remote names and URLs | No usable remote |
| `GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Unavailable — inspect tracked remote bookmarks; ask rather than guessing |
| `GIT_DIR="$(jj git root)" gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with a local bookmark targeting `@` (or the completed change once Step 3 has set one), and pass the bookmark **name only**. Two traps:

- **No bookmark yet:** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 3 sets a bookmark.
- **Fork workspace:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (push in Step 3, `GIT_DIR="$(jj git root)" gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

JJ's working copy is a change, not a bookmark selection. A missing bookmark on `@` is normal, not an error. Resolve the default bookmark from `GIT_DIR="$(jj git root)" gh repo view`. If that command exited non-zero, inspect tracked remote bookmarks (`jj bookmark list --all-remotes`) for an unambiguous default. If none resolve, ask the user. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `GIT_DIR="$(jj git root)" gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Bookmark routing:

- **No feature bookmark, work present** (working-copy change is non-empty, or local changes exist between the default remote bookmark and `@`) — automatically create a feature bookmark before push. Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to create it — invoking the full change/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived name already exists at an unrelated revision, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely. Never push the default bookmark directly.
- **No feature bookmark, no work** — report no feature work and stop.
- **Feature bookmark already targets the work** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0 — in a base repo with multiple forks, another contributor's PR can share the same bookmark name (`--head` filters by bookmark only, not `<owner>:<bookmark>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark/fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it; if multiple entries share the bookmark name from different owners and none can be confirmed as the current head's, treat it as ambiguous and stop/surface rather than acting on the wrong PR. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in git log, compose commit messages adherent to the present standards. Then: repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax. PR titles follow the project's observed title conventions independently of the JJ change description. The description reference's title step uses this same composition rule.

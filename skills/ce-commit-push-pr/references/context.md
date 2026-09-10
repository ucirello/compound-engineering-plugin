# Repository context, bookmark, and PR state

Gather this before Step 1, and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly — a non-zero exit is a normal state to interpret (no PR yet, no default bookmark, no bookmark on `@`), not a failure to suppress.

This skill pins two compound recipes that are allowed to use `$(...)` because splitting them drops a required coupling: (1) every `gh` invocation that talks to the underlying git repo, `GIT_DIR=$(jj git root) gh …` (and when a workspace cwd is in play, also run `gh` with that workspace root as cwd); (2) the `--body-file` write in `references/apply-and-handoff.md`. Do not invent further compounds.

Run them in order — the existing-PR check needs the bookmark name from `jj log -r @ -T 'bookmarks.join("\n")' --no-graph`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ workspace — report and stop |
| `jj status` | Working-copy state | (fails only outside a workspace) |
| `jj diff` | Working-copy changes vs parents | Empty change / nothing to describe |
| `jj log -r @ -T 'bookmarks.join("\n")' --no-graph` | Current bookmark (`<branch>`) | Empty output = no bookmark on `@` (Step 1 handles it) |
| `jj log -r ::@ -n 10 --no-graph -T builtin_log_oneline` | Recent change / PR-title style | Empty history |
| `jj git root` | Underlying git dir for `gh` | Non-git-backed JJ repo — `gh` pairing cannot proceed |
| `GIT_DIR=$(jj git root) gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<branch>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<branch>` with the current bookmark from `jj log -r @ -T 'bookmarks.join("\n")' --no-graph` (if several, the non-default feature bookmark), and pass the bookmark **name only**. Two traps:

- **Empty bookmark (no bookmark on `@`):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork checkout:** do **not** pass `<owner>:<branch>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

Resolve the remote default bookmark with `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If that exits non-zero, try `jj log -r 'main@origin' -n 1 --no-graph`, then `master@origin`, then `develop@origin`. If none resolve, fall back to `main`. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `GIT_DIR=$(jj git root) gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Bookmark routing:

- **No bookmark on `@`** — automatically create a feature bookmark from the current working-copy change before continuing. Derive the bookmark name from the change content, run `jj bookmark create <branch-name>`, re-read `jj log -r @ -T 'bookmarks.join("\n")' --no-graph`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default bookmark with work to do** (working-copy changes, unpushed, or no upstream) — automatically create a feature bookmark (pushing the default directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to bookmark — committing on the default is not an option here.
- **On default bookmark with no work** — report no feature-bookmark work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0 — in a base repo with multiple forks, another contributor's PR can share the same branch name (`--head` filters by branch only, not `<owner>:<branch>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark/fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it; if multiple entries share the branch name from different owners and none can be confirmed as the current head's, treat it as ambiguous and stop/surface rather than acting on the wrong PR. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Match repo style for change descriptions and PR titles (project instructions in context > recent changes > the Go guidance above). Repo-local syntax from the project's active instructions and from `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing repo-local syntax. Do not use a fixed `type:` / `type(scope):` / `fix:` / `feat:` template unless that syntax is what the project instructions or recent `git log` already use. The user may override. The description reference's title step uses this same composition rule.

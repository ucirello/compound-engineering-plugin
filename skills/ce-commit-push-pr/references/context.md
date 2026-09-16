# Repository context, bookmark, and PR state

Gather this before Step 1 (resolve bookmark and PR state), and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly. A non-zero exit is a normal state to interpret (no PR yet, no trunk bookmark, unbookmarked `@`), not a failure to suppress.

When invoking `gh`, set `GIT_DIR` for that call to the path from a prior `jj git root` (fill the path from that call; do not nest `$(...)`).

Run them in order — the existing-PR check needs the bookmark name from `jj log -r @ --no-graph -T bookmarks`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a jj workspace — report and stop |
| `jj status` | Working-copy state | (fails only outside a workspace) |
| `jj diff` | Working-copy changes | Empty = no content changes (still check `jj status`) |
| `jj log -r @ --no-graph -T bookmarks` | Bookmarks on `@` (`<bookmark>`) | Empty output = no bookmark on `@` (Step 1 handles it) |
| `jj log -n 10 --no-graph` | Recent change-description / PR-title style | Empty history |
| `jj bookmark list` | Local and remote bookmarks; trunk | No bookmarks listed |
| `jj git root` | Git dir for `gh` | No Git backend — `gh` cannot talk to this repo |
| `jj git remote list` | Remote names and URLs | No usable GitHub remote |
| `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` | GitHub default branch (fallback) | No GitHub remote / auth — use the trunk bookmark, else `main` |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with the current bookmark from `jj log -r @ --no-graph -T bookmarks`, and pass the bookmark **name only**. Two traps:

- **Empty bookmark (unbookmarked `@`):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork workspace:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

**Default bookmark name:** from `jj bookmark list` / remote bookmarks, take the trunk name and strip a trailing `@origin` (so `main@origin` → `main`). Fall back to the `gh` default branch, else `main`. Use that bare name for all "on the default bookmark?" checks — never compare against `<name>@origin`. If `jj bookmark list` does not yield a trunk and `gh repo view` also fails, fall back to `main`.

Which bookmark path to take:

- **Unbookmarked `@`** — automatically create a feature bookmark from the current `@` before continuing. Derive the bookmark name from the change content, run `jj bookmark create <bookmark-name>`, re-read `jj log -r @ --no-graph -T bookmarks`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default bookmark with work to do** (working-copy changes, unpublished local changes, or no remote bookmark) — automatically create a feature bookmark (pushing the default directly is not supported). If the default bookmark is on `@`, move it to `@-` so the default stays at the parent, then create the feature bookmark on `@`. Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to bookmark — leaving the work only on the default is not an option here.
- **On default bookmark with no work** — report no feature bookmark work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same bookmark name (`--head` filters by bookmark only, not `<owner>:<bookmark>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the bookmark name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing repo-local syntax. Determine the syntax at runtime from those sources. User override wins. PR titles follow the project's observed title conventions independently of the JJ change description. The description reference's title step uses this same rule.

# Repository context, bookmark, and PR state

Gather this before Step 1 (resolve bookmark and PR state), and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly. A non-zero exit is a normal state to interpret (no PR yet, no trunk bookmark, no bookmark at the working copy), not a failure to suppress.

The one pinned exception: every `gh` invocation that talks to the backing git repo is prefixed with `GIT_DIR="$(jj git root)"` (and `GIT_WORK_TREE="$(jj workspace root)"` when the working tree matters). Gather `jj git root` and `jj workspace root` as their own argv calls first, then pass those values as `GIT_DIR` / `GIT_WORK_TREE` on the `gh` call so the `gh` line itself stays free of nested `$(...)`.

Run them in order — the existing-PR check needs the bookmark name from `jj bookmark list -r @`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu repository — report and stop |
| `jj git root` | Backing git directory for `GIT_DIR` | No Git backend — `gh` cannot see a git repo; report and stop |
| `jj status` | Working-copy state | (fails only outside a repo) |
| `jj diff` | Working-copy changes | Empty change / no diff |
| `jj bookmark list -r @` | Bookmarks at the working copy (`<bookmark>`) | Empty output = no bookmark at `@` (Step 1 handles it) |
| `jj log -n 10 --no-graph -T builtin_log_oneline` | Recent change / PR-title style | Unborn repo — no history yet |
| `jj bookmark list -r trunk()` | Default/trunk bookmark | No trunk — resolve per Step 1 |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty; prefix `GIT_DIR`) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with a bookmark name from `jj bookmark list -r @` (parse names), and pass the bookmark **name only** — that name is what GitHub exposes as the git branch after `jj git push --bookmark`. Two traps:

- **Empty bookmark (none at `@`):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork checkout:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

The trunk bookmark is the repo default. If `jj bookmark list -r trunk()` exited non-zero or returned nothing, try `GIT_DIR="$(jj git root)" gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If both fail, fall back to `main`. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Which bookmark path to take:

- **No bookmark at `@`** — automatically create a feature bookmark from the current working-copy change before continuing. Derive the bookmark name from the change content, run `jj bookmark create <bookmark-name> -r @`, re-read `jj bookmark list -r @`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On trunk bookmark with work to do** (uncommitted, unpushed, or no upstream) — automatically create a feature bookmark (pushing the trunk directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to bookmark — committing on the trunk is not an option here.
- **On trunk bookmark with no work** — report no feature-bookmark work and stop.
- **Feature bookmark** — continue.

If several bookmarks point at `@`, use the non-trunk feature bookmark this workflow is publishing. If more than one feature bookmark matches and none can be confirmed, treat it as ambiguous: stop and show the candidates.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same bookmark name (`--head` filters by name only, not `<owner>:<bookmark>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the bookmark name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from the Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax. Do not choose a type, scope, prefix, or subject template during composition.

Match repo style for change descriptions and PR titles (project instructions in context > recent change descriptions). The description reference's title step uses this same convention source. Never use `!` or a `BREAKING CHANGE:` footer without explicit user confirmation.

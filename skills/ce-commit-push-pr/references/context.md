# Repository context, bookmark, and PR state

Gather this before Step 1 (resolve bookmark and PR state), and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly. A non-zero exit is a normal state to interpret (no PR yet, `trunk()` unresolved, no feature bookmark), not a failure to suppress.

This skill pins two compound recipes that are allowed to break argv-form: (1) `GIT_DIR=<git-dir> gh …` for every `gh` call that talks to the git store, where `<git-dir>` is the snapshot from `jj git root`; (2) the `--body-file` temp-file recipe in `references/apply-and-handoff.md`. Do not add others.

Run them in order — the existing-PR check needs the bookmark name from `jj bookmark list`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a jj repository — report and stop |
| `jj status` | Working-copy state | (fails only outside a repo) |
| `jj diff` | Working-copy changes vs parent | Empty working copy / no commits yet |
| `jj bookmark list -r @` | Bookmarks on `@` (`<bookmark>` when non-empty) | Empty = no bookmark at `@` — then list `-r @-` |
| `jj log -n 10 --no-graph` | Recent commit / PR-title style | Unborn repo — no history yet |
| `jj bookmark list -r 'trunk()'` | Default bookmark | `trunk()` is `root()` or unnamed — resolve per Step 1 |
| `jj git root` | Git dir for `gh` (`<git-dir>`) | No git backend — stop; `gh` cannot see the store |
| `GIT_DIR=<git-dir> gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with the feature bookmark that names this work: the non-default local bookmark pointing at `@`, or at `@-` when `@` is empty. Pass that **name only** to `--head` — GitHub's head ref is the bookmark name. Two traps:

- **Empty bookmark (no feature bookmark):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **On a fork:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

The default bookmark is `trunk()`. If that revset is `root()` or does not name a bookmark, try `GIT_DIR=<git-dir> gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If both fail, fall back to `main`. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Which bookmark path to take:

- **No feature bookmark** — automatically create a feature bookmark from the current `@` before continuing. Derive the name from the change content, run `jj bookmark create <bookmark-name>`, re-read `jj bookmark list -r @` (and `-r @-` if `@` is empty), and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default bookmark with work to do** (working-copy changes, unpublished commits, or no upstream) — automatically create a feature bookmark (pushing the default directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to create a bookmark — committing on the default is not an option here.
- **On default bookmark with no work** — report no feature-bookmark work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same head name (`--head` filters by name only, not `<owner>:<bookmark>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repo-local syntax from project instructions and `git log` always wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing local syntax. Do not apply a Conventional Commit template. Match repo style for PR titles from project instructions in context, else recent commits. The description reference's title step uses those same present standards. The user may override.

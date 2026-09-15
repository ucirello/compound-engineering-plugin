# Repository context, bookmark, and PR state

Gather this before Step 1 (resolve bookmark and PR state), and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly. A non-zero exit is a normal state to interpret (no PR yet, trunk unresolved, no bookmark on `@`), not a failure to suppress.

This skill pins two compound recipes that may join commands: pairing every `gh` invocation that talks to git with `GIT_DIR` from `jj git root` (gather the root as its own argv call first, then set `GIT_DIR` on `gh`), and writing the PR body through `--body-file` under the workspace `.tmp` as shown in `references/apply-and-handoff.md`. Do not invent others.

Run them in order — the existing-PR check needs the bookmark name from bookmarks on `@`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a jj workspace — report and stop |
| `jj git root` | Underlying git dir for `gh` (`GIT_DIR`) | No git backend — `gh` git pairing unavailable; report and stop if a `gh` path is required |
| `jj status` | Working-copy state | (fails only outside a workspace) |
| `jj diff` | Working-copy changes | Empty working-copy change |
| `jj log -r @ --no-graph -T 'bookmarks'` | Bookmarks on `@` (`<bookmark>`) | Empty output = no bookmark on `@` (Step 1 handles it) |
| `jj log -n 10 --no-graph` | Recent change / PR-title style | No history yet |
| `jj log -r 'trunk()' --no-graph -T 'bookmarks'` | Trunk / default bookmark | Unresolvable trunk — resolve per Step 1 |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty; `GIT_DIR` set) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with a non-trunk bookmark on `@` from `jj log -r @ --no-graph -T 'bookmarks'`, and pass the bookmark **name only**. Two traps:

- **Empty bookmark (none on `@`):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork checkout:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

The trunk bookmark is the default. If `trunk()` exited non-zero or resolved only to `root()`, try `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` with `GIT_DIR` set. If both fail, fall back to `main`. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Which bookmark path to take:

- **No bookmark on `@`** — automatically create a feature bookmark on the current `@` before continuing. Derive the bookmark name from the change content, run `jj bookmark create <bookmark-name>`, re-read `jj log -r @ --no-graph -T 'bookmarks'`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default/trunk bookmark with work to do** (working-copy changes, unpushed changes, or no upstream) — automatically create a feature bookmark (pushing the default/trunk bookmark directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to bookmark — describing the work onto the default/trunk bookmark is not an option here.
- **On default/trunk bookmark with no work** — report no feature-bookmark work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same bookmark name (`--head` filters by ref name only, not `<owner>:<bookmark>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the bookmark name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repo-local syntax. Do not choose commit-message syntax here. Match repo style for PR titles from project instructions in context and recent change descriptions; the description reference's title step uses the same sources. The user may override.

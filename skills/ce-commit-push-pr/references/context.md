# Repository context, bookmark, and PR state

Gather this before Step 1 (resolve bookmark and PR state), and re-verify bookmark, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Gather the repository context by running each `jj` command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join `jj` probes with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly. A non-zero exit is a normal state to interpret (no PR yet, no default bookmark, no bookmark on `@`), not a failure to suppress.

**Pinned compound form for every `gh` invocation** (same shell, required so gh sees the colocated Git store):

```bash
GIT_DIR=$(jj git root) gh <subcommand> ...
```

The other pinned compound recipe is the `--body-file` write in `references/apply-and-handoff.md`.

Run the `jj` probes in order — the existing-PR check needs the bookmark name from `jj log -r @ -T 'bookmarks ++ "\n"' --no-graph`:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Repo root | Not a jj repository — report and stop |
| `jj status` | Working-copy state | (fails only outside a repo) |
| `jj diff` | Working-copy changes | Empty working-copy change |
| `jj log -r @ -T 'bookmarks ++ "\n"' --no-graph` | Current bookmark (`<branch>`) | Empty output = no bookmark on `@` (Step 1 handles it) |
| `jj log -n 10 --no-graph` | Recent description / PR-title style | Empty repo — no history yet |
| `jj bookmark list --remote origin` | Remote bookmarks, including the default | No origin remote — resolve per Step 1 |
| `GIT_DIR=$(jj git root) gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<branch>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<branch>` with the current **local** bookmark from `@` (not a `name@origin` remote bookmark), and pass the bookmark **name only**. Two traps:

- **Empty bookmark (no bookmark on `@`):** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork checkout:** do **not** pass `<owner>:<branch>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve bookmark and PR state

Resolve the remote default bookmark with `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If that exits non-zero, try `main` / `master` / `develop` as `<candidate>@origin` via `jj bookmark list --remote origin`. If none resolve, fall back to `main`. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `GIT_DIR=$(jj git root) gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Which bookmark path to take:

- **No bookmark on `@`** — automatically create a feature bookmark from the current `@` before continuing. Derive the bookmark name from the change content, run `jj bookmark create <branch-name>`, re-read `jj log -r @ -T 'bookmarks ++ "\n"' --no-graph`, and use that result for the rest of the workflow. Do not ask whether to create the bookmark — invoking the full commit/push/PR workflow is already confirmation that the work should become bookmark-backed. If the derived bookmark name already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **On default bookmark with work to do** (uncommitted, unpushed, or no upstream) — automatically create a feature bookmark (pushing the default directly is not supported). Derive a name from the change content and continue at Step 3, which handles bookmark creation safely. Do not ask whether to bookmark — committing on the default is not an option here.
- **On default bookmark with no work** — report no feature-bookmark work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same branch name (`--head` filters by branch only, not `<owner>:<branch>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the bookmark and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the branch name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Match repo style for change descriptions and PR titles from the project's active instructions already in context, then from recent history. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing local syntax. The user may override. The description reference's title step uses the same local-style default.

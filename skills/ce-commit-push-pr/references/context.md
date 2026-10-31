# Repository context, branch, and PR state

Gather this before Step 1 (resolve branch and PR state), and re-verify branch, remote, and PR state immediately before each
consequential step (the push in Step 3, `gh pr create` in Step 5).

Run every JJ command from the target workspace's absolute root (`cwd=workspace_root` or `(cd "$workspace_root" && jj ...)`). Resolve that root with `jj workspace root`. For every repository-scoped `gh` sequence, export `GIT_DIR=$(jj git root)` from that same root first; this applies throughout all references. Never invoke the Git executable or a helper that launches it.

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list`. Resolve the actual task history head, intended feature bookmark, head repository and remote. Inspect `@-` and its bookmarks when `@` is empty before deciding there is no PR or work. Multiple candidate bookmarks are ambiguous: stop instead of guessing. Read several recent full descriptions under the message standards in `commit-and-push.md`.

Resolve the remote default bookmark with `gh repo view --json defaultBranchRef`, then verify its remote revision through JJ. If unavailable, ask rather than guess. Query `gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` only for a resolved nonempty feature bookmark. Exit-0 `[]` means none; nonzero means unknown. For forks, target the base repo with `-R <base-owner>/<repo>` and pass the bookmark name alone, never `<owner>:<branch>`.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the branch, remote, and existing-PR state immediately before each consequential step (the push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

## Step 1 detail: resolve branch and PR state

Resolve and verify the default bookmark as above. A nonzero PR query is unknown, not none; resolve authentication/connectivity before any create.

Which branch path to take:

- **No feature bookmark** — automatically create a feature bookmark without asking whether to branch. Preserve any explicit requested/configured base through `references/branch-creation.md`; only when no explicit base applies may the verified current committed task head serve as the intended base, after inspecting its ancestry for unrelated work. Derive a nonconflicting name from the change content, create it at the selected exact revision, and re-read `jj bookmark list`. Bookmark creation alone does not align the working copy: verify the parent and owned changes before committing, and stop rather than moving unrelated work or silently replacing the selected base. Ask only when a conflict or ancestry/base decision cannot be resolved safely.
- **On default branch with work to do** (uncommitted, unpushed, or no upstream) — automatically create a feature branch (pushing the default directly is not supported). Derive a name from the change content and continue at Step 3, which handles branch creation safely. Do not ask whether to branch — committing on the default is not an option here.
- **On default branch with no work** — report no feature branch work and stop.
- **Feature branch** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0. In a base repo with multiple forks, another contributor's PR can share the same branch name (`--head` filters by branch only, not `<owner>:<branch>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the current head — the branch and fork this workflow is pushing. Note the URL and body from that entry (all entries are open — the check filtered `--state open`). If exactly one entry matches, use it. If multiple entries share the branch name from different owners and none can be confirmed as the current head's, treat it as ambiguous: stop and show the candidates to the user rather than acting on the wrong PR. Step 5 uses the URL to choose between creating a new PR and updating the existing one. Step 4 uses the existing body as context for what to preserve when rewriting.

## Step 2 detail: conventions

Determine message syntax at runtime from project instructions and several recent full JJ descriptions, following `references/commit-and-push.md`. Repository-local syntax wins; never assume a fixed prefix or Conventional Commits.

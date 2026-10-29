# Repository context, bookmark, and PR state

Resolve the absolute target `workspace_root` with `jj workspace root`. Run every JJ command with that absolute root as cwd: `(cd "$workspace_root" && jj ...)`, or argv-form subprocess calls with `cwd=workspace_root`. File paths remain repository-relative. Use latest JJ; never invoke the Git executable, including helpers/fallbacks. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/git-command-table/.

Every repository-scoped `gh` command in this skill and its references uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. This preamble applies to all abbreviated examples. With argv-form calls obtain `jj git root` separately and pass it in the child environment. Run probes separately and interpret each exit status rather than suppressing failures.

Gather `jj status`, `jj diff`, `jj bookmark list --all-remotes`, `jj git remote list`, and `jj log --no-graph -r '@ | @-' -T 'commit_id ++ " " ++ bookmarks ++ "\n" ++ description ++ "\n"'`. Resolve the head repository, push remote, feature bookmark and default/base bookmark from instructions, remote bookmarks and `gh repo view --json nameWithOwner,defaultBranchRef`; never guess on failure. Record exact commit IDs. An empty `@` above a published head is normal: inspect `@-`, its bookmarks, remote branch and associated PR before deciding there is no PR/work.

Query `gh pr list -R <base-owner/repo> --head <head-bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Only exit-0 `[]` means no open PR; nonzero means unknown. Resolve authentication/connectivity and re-query before creation. Never query an empty head. Use the bookmark name alone, not `owner:bookmark`; match verified head owner and bookmark, never index 0. Stop on ambiguity. Retain URL and body for composition.

## Step 1: Publishing bookmark

- No feature bookmark at the intended head: the full workflow authorizes a content-derived, non-conflicting bookmark. Use `jj bookmark create <name> -r <verified-head>` and verify it; preserve all other bookmarks. Do not ask whether to create one.
- Default bookmark with working/unpublished changes: follow `branch-creation.md`; never push the default directly.
- Default bookmark without work: report and stop.
- Existing feature bookmark: verify target, remote and authority. Do not choose arbitrarily among several bookmarks.

All probes are snapshots. Re-verify head, bookmark, remote and PR immediately before push and creation. Fork PRs are queried against the base repository but pushed only to the verified head repository with known authority.

## Step 2: Conventions

Read active instructions and `commit-message-standards.md` before composing descriptions or recommending message-derived PR titles. Repository-local syntax wins; impose no Conventional Commit type/prefix fallback. Resolve separate project PR-title conventions when present.

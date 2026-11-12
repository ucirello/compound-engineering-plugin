# Repository context, bookmarks, and PR state

Run every JJ command with cwd equal to the verified absolute target workspace root; `jj root` discovers it. Never use `-R` as a cwd substitute or execute Git directly. For every repository-scoped `gh` command, set `GIT_DIR` to the result of `jj git root` obtained in that same root (a shell adapter may use `GIT_DIR=$(jj git root) gh ...`). Capture each probe's actual exit status separately.

Gather `jj status`, `jj diff`, `jj bookmark list --all-remotes`, and `jj git remote list`. Resolve the actual task history head: an empty `@` may sit above the pushed PR head; inspect `@-`, bookmarks, remote heads, and PR metadata before declaring no work or no PR. Capture the verified task commit ID, not merely mutable `@`.

Resolve the default bookmark from `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, then verify its remote bookmark after `jj git fetch --remote <remote> --bookmark <base>`. If unknown, ask; pipeline stops rather than guessing `main`.

For a known nonempty feature bookmark, query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Never query an empty head: it drops the filter. On forks, target the verified base repository with `-R <base-owner>/<repo>` and pass only the bookmark name, never `<owner>:<branch>`. Only exit-0 `[]` means no PR; nonzero means unknown (auth/network/tool failure), blocking creation until resolved. Match both head owner and bookmark; never take index zero blindly. Ambiguity stops with candidates. Preserve the matching URL and body.

No feature bookmark, or default bookmark with work: derive a nonconflicting feature bookmark from the task and create it with `jj bookmark create <bookmark> -r <verified-task-head>`; full-workflow intent authorizes this without another branch question. Default bookmark without work stops only after inspecting the real task head and remote/PR state. Never push the default bookmark directly. Read `branch-creation.md` before changing ancestry.

Reverify repository, bookmark target, remote, push authority, and PR identity immediately before push or PR creation. Probe results are snapshots, not authority to mutate a different head.

## Step 2: runtime message standards

Before composing any commit message, PR title/body, layer message, or archival message, read https://go.dev/wiki/CommitMessage in full. From the absolute target root, run `jj log -r 'ancestors(<verified-task-history-head>)' -n 10 --no-graph -T 'commit_id ++ "\\n" ++ description ++ "\\n\\n"'` to read several recent complete subjects and bodies, retaining the task-head anchor. Compare prefixes, casing, tense, body organization, wrapping, and issue syntax with project instructions. Project instructions and demonstrated history always win; apply only compatible Go quality guidance. Do not invent Conventional Commit precedent.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

No creator/model/harness attribution or Co-authored-by/Assisted-by trailers. Preserve human authorship and credit humans in prose when needed.

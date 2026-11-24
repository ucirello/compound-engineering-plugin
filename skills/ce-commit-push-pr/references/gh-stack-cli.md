# GitHub stack mechanics for JJ-managed bookmarks

GitHub's [Stacks REST API](https://github.com/github/gh-stack/blob/v0.1.0/docs/src/content/docs/reference/rest-api.md) can read, register, and extend a stack without a local branch checkout or manager catalog. Run the following `gh api` calls with the `GIT_DIR` scope from `references/context.md`, an explicit `--hostname "$host"`, and the verified base owner/repo. Use literal arguments and validated numeric PR and stack IDs. Do not use stack CLI commands that check out, push, or rebase branches; JJ owns those operations.

| Purpose | Endpoint and evidence |
| --- | --- |
| Probe capability | `GET repos/<base-owner>/<repo>/stacks?per_page=1`. A successful valid list proves read access. A 404 does not prove that a PR is standalone; the feature may be unavailable or access denied. |
| Find membership | `GET repos/<base-owner>/<repo>/stacks?pull_request=<pr-number>`. Exit-success `[]` means standalone; require exactly one verified matching stack for a member. |
| Read exact topology | `GET repos/<base-owner>/<repo>/stacks/<stack-number>`. `pull_requests` is ordered bottom to top; record trunk `base.ref`, exact PR numbers, states, draft flags, and head refs/SHAs. Read individual PRs for head and base repository identity. |
| Register | `POST repos/<base-owner>/<repo>/stacks` with `{"pull_requests":[<bottom-pr>,<next-pr>,...]}` and at least two PRs. |
| Extend | `POST repos/<base-owner>/<repo>/stacks/<stack-number>/add` with `{"pull_requests":[<new-pr>,...]}` in order, only the delta above the verified current top. |

For a POST, write the JSON argument document under the workspace's ignored `.tmp/` and pass it with `--input <absolute-path>`. GitHub requires the base branch of each non-bottom PR to be the previous PR's head. Verify the complete chain before registration and re-read after it. Don't remove or move foreign members; when remote state changed, stop and report any already-pushed bookmarks and existing PR URLs instead of replaying writes blindly.

This workflow never merges. The single-PR merge command cannot land a stack; only `ce-babysit-pr` owns the [stack-aware merge decision](https://github.com/github/gh-stack/blob/v0.1.0/docs/src/content/docs/reference/merge-api.md) under `posture:stack-land`.

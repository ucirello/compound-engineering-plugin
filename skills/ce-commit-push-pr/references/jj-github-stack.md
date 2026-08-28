# Jujutsu and GitHub stack semantics

A stack is a linear set of Jujutsu changes. Each published layer has a bookmark, and GitHub sees that bookmark as a Git branch. Jujutsu changes remain the source of truth; do not use a second stack manager to mutate their topology.

Resolve a parent PR with `GIT_DIR="$(jj git root)" gh pr view <ref> --json baseRefName,headRefName,headRefOid,author,url,state`. Fetch its head bookmark from the correct remote with `jj git fetch --remote <remote> --branch <headRefName>`, then verify that `<headRefName>@<remote>` resolves to `headRefOid`. A name match without an object match is not proof of parent identity.

Inspect topology with `jj log` and Jujutsu revsets. A valid stack is linear, each child layer has exactly one intended parent layer, and each bookmark points to the change represented by its PR. Bookmarks do not move automatically when new descendant changes are created, so move each bookmark explicitly to its intended target before push.

Push each layer with `jj git push --remote <push-remote> --bookmark <bookmark>`. Jujutsu maps the bookmark to a same-named Git branch, pushes no descendants beyond its target, and refuses stale or conflicted remote-bookmark updates. On refusal, fetch, resolve the bookmark state, and retry; do not bypass the lease-like safety check.

Create each PR with `GIT_DIR="$(jj git root)" gh pr create`, setting its base to the immediate parent layer's bookmark and its head to the layer bookmark. The bottom layer targets the resolved repository base or named parent. Use explicit PR URLs for later `GIT_DIR="$(jj git root)" gh pr view` and `GIT_DIR="$(jj git root)" gh pr edit` calls.

For non-colocated repositories, point GitHub CLI at the backing Git repository returned by `jj git root` using the invocation environment. This is necessary Git remote interoperability documented by Jujutsu; it does not make Git refs or Git's index authoritative.

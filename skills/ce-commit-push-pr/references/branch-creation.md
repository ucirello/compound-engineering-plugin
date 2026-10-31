# Branch creation from default branch

Local `<base>` may have stale commits (another session/worktree advanced it) or commits the user authored intending to branch from later. Local JJ can't distinguish these — ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

Resolve the exact requested/configured base and its repository/remote first, using Context; use the verified default only when no explicit base was supplied. Record its identity and verified local commit, if available. Never replace an explicit base with the current head or default bookmark. All commands below run from the target workspace's absolute root.

```bash
jj git fetch --remote <verified-base-remote> --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log --no-graph -r '<verified-base-commit>..<verified-local-base-head>' -T 'description ++ "\n"'
```

- Verify the fetched bookmark still identifies the requested base and capture its exact commit as `<verified-base-commit>`. Compare only the verified local counterpart of that base, not an arbitrary current feature head; inspect the full candidate ancestry and ownership before offering to carry commits.
- **Empty output:** set `BASE_REF=<verified-base-commit>` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on the verified remote base. Carry these displayed commits onto the new feature branch, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REF=<verified-local-base-head>`, only when compatible with the requested base and explicitly authorized for the displayed ancestry. An exact requested base commit remains exact unless the user authorizes changing it.
  - **Leave on `<base>`** → `BASE_REF=<verified-base-commit>`. Local commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature branch

```bash
jj bookmark create <branch-name> -r "$BASE_REF"
```

Bookmark creation does not check out that revision or change the working copy's parent. Verify the bookmark points to `BASE_REF`, then inspect the current parent and complete owned/unrelated change set before committing. Do not subsequently commit at an unrelated current parent and move the feature bookmark there: that would silently replace the selected base or include unrelated ancestry. If the working copy is not based on the selected revision, preserve recovery references and use only an explicitly verified owned-change rebase that retains the selected ancestry; otherwise stop with a decision/blocker. Even a clean working copy does not authorize moving unrelated user commits or bookmarks. Do not stash, discard or remove colliding paths. In pipeline mode report the blocker without asking.

## Fetch failure fallback

If `jj git fetch` fails, retain the exact requested/configured base identity. If that explicit base cannot be verified locally, stop: do not substitute the current head, another bookmark, another remote or the default base. A previously verified local commit of that same base may be used only when it satisfies the request's exact-ref/freshness requirements; explicitly disclose its commit and that remote freshness could not be verified. If freshness was required, stop instead. Create the feature bookmark at that verified same-base commit through step 3, never at an arbitrary current head. Skip the purported fresh-remote unpushed comparison because it would be unreliable; do not silently carry local commits. Unknown local-base identity or ancestry is a blocker.

Run all commands from the target absolute workspace root. Creating a bookmark does not move pending work: if the selected base differs, preserve the local default and a recovery bookmark, then rebase only verified owned pending changes to that exact base. Inspect tracked/conflicted/ignored/untracked and excluded work first; stop for collisions or uncertain ownership, never discard or overwrite. Pipeline mode reports required carry/leave decisions instead of guessing.

# Native JJ lifecycle and change descriptions

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

These rules apply to every phase, experiment, remote worker, integration, report commit, and cleanup. `worktree` remains a compatible spec value meaning a JJ workspace, not a Git worktree. Use JJ bookmarks rather than branches. Run **every** JJ subprocess with its absolute target workspace root as cwd: `(cd "$workspace_root" && jj ...)`; never use `jj -R` as a cwd substitute. No direct Git executable calls or transport fallbacks. Repository-scoped GitHub operations run from that target root with `GIT_DIR=$(jj git root)` set for `gh`.

## Isolation and identity

Detect existing isolation first through harness context and `jj workspace list`. Reuse existing isolation unchanged, including nonconforming registered names and colocation. Harness-native lifecycle takes precedence. If it cannot provide required naming and colocation for a new workspace, report a safe blocker instead of silently weakening isolation.

For each new workspace capture the local date once and persist the identity in the run ledger before creation. Use `YYYYMMDD-meaningful-kebab-slug`, derived from the task/spec and experiment (for example `20261008-clustering-exp-003`), for both registered name and destination basename under the source workspace's existing local `.tmp` parent. Normalize caller names without double date prefixes. Check both workspace registrations and destination paths; append `-2`, `-3`, etc. on collision. Never use timestamp, PID, or random identities. Reuse the persisted identity across retries, resumes, and midnight. Do not rename existing source/PR bookmarks.

Resolve the optimization bookmark to one exact verified base commit before creation; store the base ID and intended destination in the ledger. From the absolute source root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Record the verified registration/name/path/colocation receipt before dispatch. Copy only declared shared files, preserving relative paths and containment, without overwriting unrelated content. All temporary files and durable local run scratch live under the workspace-local `.tmp`; without a repository use local `.tmp`. Keep existing ledgers at their existing root on resume rather than relocating them.

## Change descriptions and integration

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing **any** experiment, result-marker, integration, report, or other change description, read the full linked guide and compare several recent subjects **and bodies** at the task-verified history head:

```bash
(cd "$workspace_root" && jj log --no-graph -r "::$verified_history_head" -n 10 -T 'description ++ "\n"')
(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")
```

Repository-local syntax always wins. Examine prefixes/packages, casing, tense, subject/body separation, wrapping, and issue references. With no history use explicit instructions and compatible Go guidance, never invent precedent. Resulting messages contain no Markdown, Co-authored-by, or Assisted-by trailers. Keep hypothesis, measurement, and recovery semantics without prescribing fixed conventional-message syntax.

JJ snapshots working changes automatically; an undescribed or empty working change is not a Git dirty-tree analogue. Preserve unexpected work and conflicts, and capture exact candidate commit IDs after measurement. `result.yaml` must not contaminate the candidate: write it as a separate child change where the remote protocol requires it. Publish only the authorized result bookmark with `jj git push --bookmark`. Fetch with `jj git fetch`, inspect marker content with `jj file show -r`, verify its sole changed path and exact parent, and validate the complete base-to-candidate diff against mutable scope (including renames, deletions, binaries, and modes).

For a winning candidate, preserve a recovery bookmark and integrate its exact mutable-scope change with native JJ rebase/new-merge operations into the optimization history, resolving conflicts explicitly. Move the optimization bookmark only after confirming the intended result. For file-disjoint runner-ups, apply the exact candidate with `jj rebase` or `jj duplicate` into a new integration change and remeasure as specified in the loop. Reject an integration by returning to its verified pre-integration revision in a separate safe working change, preserving recovery revisions; never reset or overwrite unrelated work. Retain exact base/head IDs and paired evidence. A remote result tip containing only the marker is never the integration candidate.

## Destructive cleanup

Completion alone is not permission to remove a workspace. Stop workers; verify exact registered name, absolute path, run ownership, disposal authority, lack of live references, and required integration. Inspect tracked, conflicted, ignored, and untracked content separately: snapshots do not protect ignored/untracked files. Preserve recovery bookmarks. Copy measurements, receipts, and result markers outside the target and read them back before removal. Never remove ambiguous, unrelated, non-disposable, or still-referenced content.

Leave the target and move the harness session to a surviving workspace before removing it. From that surviving absolute root only:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_name")
(cd "$surviving_workspace_root" && jj workspace list)
test ! -e "$verified_absolute_destination"
```

Verify both registration and directory are gone. Warnings or failures retain remaining state and are blockers; no forced-delete fallback, `forget` plus deletion, or broad pattern cleanup. `jj workspace forget` only unregisters and preserves files, so it is not destructive cleanup. Do not delete recovery/result bookmarks until their evidence is verified and no recovery need remains.

## OpenCode setup (documentation only)

Deep delegation requires merging `experimental.subagent_depth` of at least 3 into the user's existing `~/.config/opencode/opencode.json` (or actual existing `opencode.jsonc`). Discover the actual config directory with `opencode debug paths` / `opencode debug paths config`. Preserve sibling/unrelated fields and any higher integer; do not replace the whole config or create a competing file. Higher-precedence configuration must not lower depth. Shipped package config or plugin installation alone does not enable this. Never modify host configuration during the run.

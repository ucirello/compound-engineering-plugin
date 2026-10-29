# `ce-worktree`

> Put the work in an isolated colocated JJ workspace without disturbing the current checkout.

`ce-worktree` is the **isolation** skill, a JJ-workflow tool rather than a core-loop step. Many coding harnesses create isolation at session start. The skill checks that first, then prefers a capable harness-native colocated JJ workspace tool. Native `jj workspace add --colocate` is available only when no harness primitive exists and the harness can adopt the result. An available primitive lacking required naming, colocation or lifecycle capabilities is a compatibility blocker, not permission to bypass it. Nesting isolation or creating a workspace the harness cannot see is worse than working where you already are.

There is no bundled script. Run JJ with the target workspace's absolute root as cwd, not merely `jj -R`. Repository-scoped GitHub CLI calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; never invoke Git directly. See [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Detects existing isolation, prefers a capable harness tool, else creates a colocated JJ workspace under local `.tmp/` |
| When to use it | Starting work that should stay off the current checkout, or when `ce-work` / `ce-code-review` offers a worktree |
| What it produces | Either "already isolated, work here" or a workspace with absolute path, registered name, revision, bookmarks and colocation reported |
| Skip when | Single-task work that fits in the current workspace |

---

## Example invocations

Empty or a work description means **new work**. `isolate` plus a ref means **attach**. Verified existing isolation is reused under its existing name, even when not date-prefixed or colocated. Do not rename, recreate or silently modify it to enforce new-creation rules. Align an existing workspace only after verifying the exact target and preserving unrelated tracked, ignored, untracked and conflicted work; an empty `@` directly above the requested head is already aligned.

```text
# New work. Detect isolation first; otherwise use a verified base and dated identity.
/ce-worktree for the account-notifications feature

# Already isolated: report the verified existing name and path, stay here
/ce-worktree

# Isolate an existing bookmark without renaming it
/ce-worktree isolate feature/account-notifications

# Isolate a verified PR head; preserve its source bookmark and push association
/ce-worktree isolate PR 1234

# Isolate an existing revision
/ce-worktree isolate abcdef1
```

JJ does not impose Git's one-branch-one-worktree restriction. Still detect and reuse appropriate existing isolation first, and never overwrite or adopt unrelated registered names or destinations.

---

## The Problem

"Make a worktree" is often the wrong default, because the agent is usually already in one:

- Creating nested isolation without checking ownership can put work in the wrong tree
- Behind-the-back workspace creation may be invisible to the harness, preventing listing, adoption or cleanup
- If local `.tmp/` is not ignored, scratch state can be snapshotted accidentally
- Random names hide what the workspace is for

## The Solution

Isolation is an ordered decision, not a create script.

**1. Detect existing isolation.** Resolve the absolute root with `jj workspace root`, inspect `jj workspace list` and harness session ownership, and identify the exact registered name/path. A name, `.git` file or workspace count alone does not prove isolation. Reuse verified isolation unchanged; report ambiguous ownership or unsafe alignment instead of nesting or discarding work.

**2. Prefer the harness tool.** Inspect actual explicit-naming, absolute-placement, colocated-JJ and lifecycle capabilities. Request and verify the selected dated name and matching destination basename, verified base and ownership. Move/adopt the active harness session; shell `cd` alone is not session adoption. Unsupported capabilities are blockers, never permission workarounds.

**3. Native JJ creation.** Only when neither applies and the harness can adopt the result. Inspect ignore rules and ensure `.tmp/` is ignored without invoking Git. Resolve the actual default base or exact requested ref; fetch its verified remote/bookmark with JJ when needed. A local-only base may be used only when it satisfies caller intent with freshness limitations disclosed; never substitute a different revision.

Both modes use one `YYYYMMDD-<meaningful-kebab-case-slug>` identity for the JJ name and destination basename. Capture the local creation date once; derive the slug from task, PR or revision. Normalize supplied names without double-prefixing; recorded retry/resume identities survive midnight. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Check registrations and filesystem paths, including symlinks; append `-2`, `-3`, etc. on collisions without overwriting state. Do not use timestamps, PIDs or random names. Preserve the existing absolute `.tmp/` parent layout and all PR/source bookmarks. PR isolation verifies head repository, remote, bookmark and exact commit, including forks; it never calls `gh pr checkout`.

If creation or verification fails on permissions, ownership or capabilities, retain state and report the precise blocker. Do not continue in the source checkout without the existing safe user decision, retry alternate permission paths, reset/discard state or fall back to Git.

---

## Quick Example

You are in verified harness-managed isolation created at session start. `ce-work` offers isolation. `/ce-worktree` confirms registration and ownership, reports the existing name/path/revision, and continues without renaming or altering colocation.

In a checkout with no native workspace tool, resolve a verified base and stable identity, ensure the absolute destination is locally owned under ignored `.tmp/`, then run:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify colocation from the created workspace's absolute root on **every** creation path, including harness-native creation. Verify exact registered name, matching basename, base and ownership, then adopt the session before working.

---

## When to Reach For It

Use `ce-worktree` when:

- The work should stay off the current checkout
- `ce-work` or `ce-code-review` offered a worktree

Skip it when:

- The work fits in the current workspace
- You are already isolated and do not need a second, parallel workspace (the skill detects this)

Why a skill at all? The skill is the order: detect first, defer to a capable harness, do not nest or create phantom state. `ce-work` and `ce-code-review` share that order by calling this skill.

---

## Chain Position

On-demand isolation. Callers select meaningful dated workspace identities using the same normalization, collision and stable-retry rules, not separate random workspace names. Source bookmark names remain unchanged.

```text
/ce-work         ->  /ce-worktree   (optional isolation before implementation)
/ce-code-review  ->  /ce-worktree   (review a PR without touching in-progress work)
```

---

## Reference

| Argument | Effect |
|----------|--------|
| _(empty)_ | Detect isolation. If none, new-work fallback needs a name from context. |
| `<work description>` | New work: dated colocated workspace from the verified base |
| `isolate <bookmark\|tag\|revision>` | Isolate that exact verified ref |
| `isolate PR <n>` | Isolate the verified PR head, preserving its source bookmark |

List and inspect with native JJ from the absolute workspace root; switching directories must also adopt the harness session where required:

```bash
(cd "$workspace_root" && jj workspace list)
cd "$verified_absolute_workspace_root"
```

Completion alone does not authorize deletion. Respect cleanup authorization and harness lifecycle ownership. Before retiring an exact run-owned disposable workspace: stop workers/monitors, move active harness sessions to a surviving workspace, leave the target, verify exact registered name/absolute path/run ownership and references, prove integration where required, and preserve best/archive/recovery bookmarks. Inspect tracked changes, conflicts, ignored and untracked files. Copy required evidence/receipts/recovery information outside the target and read it back. Removal snapshots tracked working state, not ignored or untracked content; stop on unrelated, ambiguous, still-referenced or non-disposable data.

Only then, from the surviving workspace's absolute root:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_owned_workspace_name")
```

Verify **both deregistration and directory disappearance**; deletion failures can be warnings despite exit success. On incomplete cleanup preserve remaining state and report the blocker, never force-delete or use Git removal. Bookmark deletion is separate and must preserve needed recovery/source references. Use `jj workspace forget <verified-name>` only for intended unregister-only behavior preserving files, never followed by deletion.

---

## See Also

- [`/ce-work`](./ce-work.md): offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md): offers worktree isolation for concurrent review
- [`/ce-commit`](./ce-commit.md): commit in the isolated tree without shipping

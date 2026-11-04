---
name: ce-worktree
description: Set up isolated, colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Reuse existing isolation before creating anything.
---

# Workspace Isolation

Ensure work happens in an isolated workspace without disturbing the primary checkout. **Done when:** the absolute workspace path, registered name, verified revision, relevant bookmarks, and harness/session adoption are reported, or a blocker is reported instead.

Use current JJ commands, never the Git executable or workspace bridge scripts. Every JJ subprocess must run from the applicable **absolute workspace root**, for example `(cd "$workspace_root" && jj workspace list)`. A repository selector does not replace the correct working directory. Temporary files, receipts, and failure artifacts belong in local workspace `.tmp/`, never system temporary directories.

## 0. Detect isolation first

Resolve the current root with `jj root`; inspect `jj workspace list`, `jj status`, and native harness workspace/session metadata. Identify the primary checkout and whether this session already occupies an isolated registered workspace. A directory name alone is not evidence. If the checkout is not JJ-managed or ownership/isolation is ambiguous, report a compatibility blocker; do not initialize or convert it silently.

**Reuse existing isolation**, preserving its name and path even if nonconforming. Do not rename, recreate, or nest another workspace. For an existing-ref request, resolve the target and compare it with the current revision. Inspect edits/conflicts and ownership before any approved revision transition; never discard unrelated work or silently repurpose another session's workspace. Report existing isolation rather than creating it again.

## 1. Verify the base and source identity

- **Fresh work:** resolve the repository's configured/default remote bookmark to an exact revision. Do not assume `main` or `origin`. Refresh with `jj git fetch` when appropriate and authorized; if unavailable, disclose use of a verified local base and stale/offline status. Ambiguity blocks creation.
- **Existing bookmark/revision:** resolve the exact unambiguous revision and preserve source bookmarks. JJ does not impose Git's one-branch-per-worktree restriction, but shared changes/bookmarks still require ownership safeguards.
- **PR:** verify repository, number, head repository/bookmark, and exact head revision. Scope repository `gh` calls from the absolute target root, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view "$pr_number" --json number,headRefName,headRefOid,headRepository)`. Fetch the verified remote/ref with JJ when needed. Never use `gh pr checkout`, direct Git, or an unrelated substitute revision. Preserve source/PR bookmarks and their push destinations unchanged; a workspace name is not a replacement bookmark.

Workspace creation does not authorize rewriting history or composing commits. If a later operation needs a description, read the full https://go.dev/wiki/CommitMessage and inspect multiple recent subjects **and bodies** with `jj log` at the absolute target root, anchored to the task's verified history head. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Repository-local syntax wins: compare prefixes/package, casing, tense, subject/body, wrapping, and issue references. Without history use explicit project/user guidance plus compatible Go guidance, never invented precedent or a fixed template.

**Go source guidance — illustrative excerpts, not a repository template.** These verbatim SOURCE excerpts are subordinate to observed repository syntax and explicit project/user instructions. Read the full guide and compare history as required above; apply only compatible guidance.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

## 2. Capture one durable creation identity

For a **new** workspace only, capture the date once as `YYYYMMDD`. Persist it with the task identity, verified base, source root, destination, and run ownership in a local `.tmp/` receipt outside the proposed destination. Reuse this record across retries, resumes, and midnight; check whether a recorded attempt already succeeded before allocating anything else.

Choose a meaningful task slug, `pr-N`, or `review-ID`. Normalize fresh/task/PR/revision/caller-provided names to safe single path components. Recognize a supplied `YYYYMMDD-slug` identity without double-prefixing it; preserve its valid captured date. Do not use a bare hash or random harness token as the task slug. Never normalize source/PR bookmarks or existing isolated workspace names.

For example: `20261008-fix-email-validation` for fresh work, `20261008-pr-214` for PR 214, and `20261008-review-efcb657` for a verified revision. A caller already supplying `20261008-pr-214` keeps that identity; a real collision becomes `20261008-pr-214-2`, recorded once for subsequent retries.

Use exactly **`YYYYMMDD-meaningful-slug`** for both the registered name and destination basename. Place the absolute destination under the source repository's local `.tmp/` workspace area, e.g. `$source_root/.tmp/workspaces/$identity`. Check both registrations with `jj workspace list` and filesystem destinations, including unregistered paths. Resolve genuine collisions with `-2`, `-3`, etc., checking both namespaces and recording the final identity before creation. Never overwrite or adopt unrelated colliding content. A matching owned receipt can establish a successful earlier attempt: verify and resume it instead.

## 3. Create, verify, and adopt

Prefer a native harness creator **only if** it guarantees the captured exact registered name, absolute destination/basename, verified base, explicit JJ colocation, and session ownership/adoption. A loose name-only API or Git-worktree creator is insufficient. Unsupported naming/colocation is a safe compatibility blocker, not permission to bypass the harness or rename/recreate its result.

If no native creator exists and the harness supports adoption of explicitly created JJ workspaces, create with native JJ from the source absolute root:

```bash
(cd "$source_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
(cd "$absolute_destination" && jj workspace list)
(cd "$absolute_destination" && jj status)
```

Require confirmed colocation. Verify the registered name, absolute destination, intended base relationship, clean/conflict state, and unchanged source bookmarks. Move/adopt the active session through the supported native session capability before continuing, and update the caller's absolute working root. If supported adoption is unavailable, stop **before** creation. Never create workspace state invisible to the harness.

Permission/sandbox errors or failed verification mean isolation is **not** established. Preserve the receipt and report partial state. Do not retry alternate paths, force cleanup, or work in the primary checkout. Offer “resolve isolation” versus “explicitly authorize working in the current checkout” through an available blocking question capability, or chat if none is available, and wait. Distinguish permission denial, unsupported capability, and verification failure rather than bypassing them.

## 4. Retire only with separate authorization

Completion alone never authorizes removal. Remove only an explicitly authorized, owned, disposable workspace after these safeguards:

1. Identify a surviving absolute workspace root. Verify the exact target registered name, resolved path, run/task ownership, and disposable status. Reject ambiguous, unrelated, primary, or externally owned targets.
2. Stop and confirm termination of workers using the target. Leave its directory; move the active session and other owned sessions to the survivor before removal. Stop if workers or session ownership cannot be accounted for.
3. Verify required integration against the intended destination and preserve recovery/best/archive bookmarks or other recovery references. Bookmark deletion is separately authorized, never incidental cleanup.
4. Copy evidence, receipts, and recovery instructions outside the target, then **read back** those copies. Inspect tracked changes, conflicts, ignored files, and untracked content through JJ status/diff and explicit filesystem inventory, including ignored `.tmp/` data. A clean JJ status is not proof the directory is disposable. Preserve non-disposable content; stop on uncertainty.
   Removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot. Never remove still-referenced or non-disposable data on the assumption that the snapshot will recover it.
5. From the surviving absolute root run `jj workspace remove "$target_name"`. Never use force flags, direct directory deletion, Git cleanup, or forget followed by deletion.
6. Verify both deregistration in `jj workspace list` and disappearance of the exact directory. Warnings, retained paths/registrations, or incomplete cleanup require retaining recovery state and reporting the issue, never force-deletion.

Reserve `jj workspace forget` for an explicit **unregister while preserving files** request. Explain that the directory remains, run from the surviving absolute root, and verify deregistration and retained files. It is not workspace disposal.

## Report

Return reused/created status, registered identity, absolute path, verified base/current revision, source bookmarks, colocation verification, session adoption, and receipt location. Include blockers and partial cleanup state. An attempted command alone is not successful isolation or retirement.

# Non-interactive runs

A non-interactive run has no one to answer a question, so it asks none, in any phase. With no user present, whoever reviews the pull request it opens does the approving. So the run applies only what a reviewer can judge from that pull request, and lists everything else for a person to decide.

**Outcome:** the checkout's generated files, and the review docs the run was asked for, are current and published as one pull request. Every change only a person can decide is listed in that pull request instead of made. A `standards` run covers only the review docs, as it does interactively. A run that finds nothing to change writes nothing and opens no pull request.

## What a run applies and what it only reports

Apply a write when a reviewer can judge it from the pull request alone. That covers generated output (Step 5's example refresh), the `.gitignore` entries of Steps 7 and 8, and, when the invocation asked for review docs, the drafts and pointer lines `references/project-docs.md` produces.

Report a write instead of making it when it needs a human choice, removes authored content, or changes this machine rather than the checkout. That covers creating `config.yaml`, deleting `rocketclaw.local.md`, repairing `docs_root` or model preferences, every Step 9 addition, moving authored rules, legacy tool-map removal, and the user-level OpenCode depth merge. Never change host config in unattended runs.

A run that did not ask for review docs leaves them alone. It reports whether they exist, because a repository without them has made a valid choice.

A Compound Pack scaffold needs the user's approval. `references/pack-scaffold.md` already says what a non-interactive request for one does: it prints the preview and writes nothing.

## Review docs

Follow `references/project-docs.md`, with these differences:

- There is no offer and no in-session preview. The pull request body carries the preview: each rule added, changed, or retired as one plain line with the pull requests, commits, or records behind it, then a **Recommended** section listing everything this run only reported.
- A new rule also needs its defect class to appear more than once in the evidence. A scheduled run sees a short window, and a single finding in it is more often a one-off than a convention. Changing or retiring an existing rule needs only the ordinary evidence.
- Earlier refresh pull requests are evidence too. If one dropped a rule during review, or was closed without merging while it proposed the rule, leave the rule out unless evidence newer than that decision supports it.

## Publishing

Use a JJ bookmark `ce-setup/refresh-<YYYY-MM-DD>` so later runs can find the pull request. Query GitHub from the absolute workspace root with `GIT_DIR=$(jj git root)`. Reuse the newest existing matching PR bookmark only after verifying its repository, remote, and exact head. Otherwise create a task change from the verified default-branch revision and a new bookmark, never commit onto the default bookmark. Reuse existing verified isolation unchanged; if new isolation is needed, follow the workspace contract below.

Capture local `YYYYMMDD` once per run, stable across retry/resume. New workspace identity is `<date>-setup-refresh` with deterministic `-2`, `-3` suffixes after checking registrations and destinations. Destination is an absolute owned path under the survivor workspace's `.tmp/`. Create with `(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$destination")`, then verify `(cd "$destination" && jj git colocation status)` and adopt the session there. A native lifecycle API must support both explicit name and colocation; otherwise stop with a compatibility blocker, not a bypass.

Cleanup is not authorized by completion alone. For expressly authorized run-owned disposal, stop workers, move the session to a surviving absolute root, verify exact registration/name/path/ownership and integration plus recovery references, and copy/read back needed evidence outside the target. Inspect tracked, conflicted, ignored and untracked content; snapshots do not protect ignored/untracked files. Then `(cd "$surviving_root" && jj workspace remove "$verified_name")`; verify deregistration and directory disappearance. On failure preserve/report, never force-delete. `forget` only unregisters while preserving files. Preserve unrelated work and recovery/archive bookmarks.

If the working tree has uncommitted changes before the run writes anything, write nothing and report that, because those changes would land in the pull request with this run's.

After writing, invoke the `ce-commit-push-pr` skill with `mode:pipeline` to commit, push, and open or update the pull request. Pipeline mode leaves an existing pull request's description alone, so when this run updated one, invoke `ce-commit-push-pr` again with `mode:pipeline` to update that pull request's description from this run's changes.

## Ending

Write the Phase 3 summary without its closing question. End with one line a caller can parse: `Setup complete: <pull request URL>` when the run published, or `Setup skipped: <reason>` when it wrote nothing or could not publish, naming any branch it left behind.

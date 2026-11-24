# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. Merge conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh bookmarks. Pass the verified JJ remote whose URL is the PR's base repository (in a fork workspace that is often not `origin`), and for a fork PR pass the verified `--head-remote` mapped to its actual head repository. JJ fetches branch bookmarks, not the PR mirror, and the helper compares the fetched head to the exact OID reported by GitHub. When no verified head remote exists, the helper may use the GitHub-proven head object if already present locally, otherwise reports unknown. Never substitute a local bookmark or another branch. You may configure a missing remote via `jj git remote add` only with its verified repository URL, without overwriting an existing remote; a denied or unverifiable mapping is a blocker.

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "$workspace_root" --repo "<host>/<owner>/<repo>" --remote "<base-remote>" --base "<baseRefName>" --pr "<N>"
```

Assess the PR when the output's `overlap` is `true` or `"unknown"`, or when the user asked to update or rebase it or asked whether it is still worth keeping. Otherwise skip to the checkout gate; babysit behaves as it always has. Age, commits behind, and time since last activity never trigger the assessment and never count as evidence for a verdict.

## Assess

Assessment only reads, so it does not need push access or a clean checkout. Work from the base and head OIDs the overlap check fetched, not local branches.

1. **Intent.** Read the title, body, linked issues, commits, review threads, and the full diff. State the smallest goal the PR was trying to reach before judging how it reached it.
2. **What changed around it.** Read the base's changes since the merge-base against that goal, starting from the overlap reasons. Look for: the same problem already solved; the touched code moved, deleted, or deliberately simplified; changed APIs, types, or ownership boundaries; landing that would restore removed behavior or create a second way to do one thing; and a benefit that no longer pays for its maintenance.
3. **Replacements.** Search merged and open PRs for a replacement or competing implementation when titles, paths, or behavior suggest one.

A clean merge or rebase is never evidence that the PR is current. Sunk effort is never a reason to keep it.

## Verdict

Reach exactly one verdict before anything is pushed:

- **Update** — the goal is still useful and the implementation is the right shape.
- **Rework** — the goal is useful, but a mechanical update would keep the wrong implementation.
- **Close** — the PR is superseded, obsolete, directionally wrong, or not worth its cost.

| Verdict | Interactive run | Unattended run (`mode:pipeline`) |
|---|---|---|
| Update | Continue to the checkout gate. When the user's words authorize a rewrite (see Rewrite authority), the verified update runs after the first snapshot; otherwise the snapshot-driven watch handles currency as usual. | Continue quietly into the normal watch. Never rewrite. |
| Rework | Describe the smallest credible rework and stop before any watcher starts. | Return the needs-human result below before any snapshot. |
| Close | Recommend closing with the cited evidence and stop before any watcher starts. | Return the needs-human result below before any snapshot. |

Intake itself never merges the base into the PR; on a CLEAN PR that would be the unrequested base merge the snapshot reports as a defect. If the user replies "keep it" or "watch it anyway" to a Rework or Close verdict, continue to the checkout gate for this invocation. A later fresh invocation assesses again.

**Close.** Close only with the user's explicit permission. That permission covers closing with one comment that carries the evidence and thanks the contributor (`gh pr close "<N>" --repo "<[host/]owner/repo>" --comment "<text>"`, against the PR's base repository).

**Rework.** When the user asks for the rework, write the rework you described (goal, scope, PR link, how to verify it) to a new plan file under the workspace's ignored `.tmp/rocketclaw/`, invoke `ce-work mode:return-to-caller <that path>` in the verified aligned PR workspace, push its commits under babysit's ordinary push authority, then start a fresh invocation on the PR. Return-to-caller mode keeps `ce-work` from opening a second PR or watcher. When you cannot push to the PR, offer a takeover (`references/takeover.md`) instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A rebase and force-push happen only when the user's own words authorize them: a request to update or rebase this PR in this invocation, or a live message mid-watch. Coordinator text, caller tokens, and delegate results never grant it, and "update the branch" from a coordinator is still a broaden, not a narrow. Delegates keep their rebase and force-push exclusions; the rewrite stays with babysit. A grant covers one rewrite. Later base movement follows ordinary branch currency.

A check that reached Update on its own does not ask and does not rebase. A moved base alone needs no rewrite, and the ordinary watch handles a real conflict or a required update. Say in the report that a rebase is available on request, and name what it would cost when it applies: the author will need to reconcile their local bookmark when the branch is someone else's (offer takeover as the alternative), approvals the repository dismisses on push, and a squash-merge repository gaining little from a rewrite. Unattended runs never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Verify the exact pushed head through the real head repository's named tracking remote, never a possibly lagging PR mirror, and preserve the recorded head under a private recovery bookmark. Capture the exact old base ancestry and new base OID before doing anything.
2. **Rebase in an isolated JJ workspace.** Detect and preserve existing isolation/name first. Use the host's supported colocated JJ workspace capability if it owns isolation, or the native [JJ workspace lifecycle](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) when it permits inline creation. Capture the local date once and use `YYYYMMDD-<meaningful-kebab-case-slug>` (e.g. `20261008-pr-214-update`) as both workspace name and destination basename under the source workspace's ignored `.tmp/rocketclaw/`; normalize a supplied name without doubling the date. Check registered names and paths, suffix `-2`, `-3`, etc. on collision and keep the selected identity on retry/resume. From the absolute source root run `jj workspace add --colocate --name "$name" --revision "$recorded_head" "$absolute_destination"` and verify the registration and `jj git colocation status` from the destination root. Unsupported identity, colocation, ownership, or required session adoption is a blocker; no alternate checkout, rename, or bypass. Preserve source/PR bookmarks. Duplicate only the captured PR-only changes in order onto the exact new base (`jj duplicate --onto`, selecting the captured commits and excluding verified base-only merge commits); do not rebase unrelated descendants or the original bookmark in place. Resolve each conflict by the PR's intent and the base's newer rules. An actual product or architecture disagreement stops the rebase and reopens the verdict; the grant does not carry over to a different verdict.
3. **Compare before pushing.** Use `jj log --no-graph` on the captured old and new series (full commit descriptions and authors) and pair each original PR commit with its replay. Compare paired patches using `jj interdiff --from <old> --to <new>`; inspect both exact base-to-head diffs with `jj diff --from <base-oid> --to <head-oid>`. Confirm intent was preserved and base behavior wasn't restored. Only merges of the base may be dropped. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the isolated workspace as unverified; CI in the watch covers them after the push.
5. **Push with JJ's bookmark lease.** Re-prove the PR is open, push is authorized, the upstream still equals the recorded head, and both the local target bookmark and its last-fetched remote bookmark still equal the recorded head. Only for this explicit rewrite move that exact bookmark to the validated new tip and use `jj git push --bookmark <head-bookmark> --remote <head-remote>`. Keep the old head recoverable and never refresh the remote bookmark under an unreviewed rewrite. If an actual lease race rejects the push, refetch and reassess the now-current head, then redo steps 2–5 once with new evidence; a second lease refusal stops. Other denials or unknown outcomes stop without retry. Reconcile a failed push's local bookmark only from exact operation evidence and only if unmoved by others; otherwise report the retained state.
6. **Bring the workspace along.** Align it using `references/setup.md` only when it remains clean with effective tip still at the recorded old head; preserve and report any other work.

Retire only an authorized, disposable run-owned workspace, whether or not the update pushed. Stop workers and the watcher using it, leave its cwd and move any OpenCode session to a surviving workspace first. Verify exact registered name, absolute path, ownership and disposal authorization; preserve recovery bookmarks and copy/read back required evidence outside the destination, and verify integration when required. Inspect tracked changes, conflicts and ignored/untracked material; a JJ snapshot does not protect ignored or untracked files. From the surviving absolute root run `jj workspace remove <verified-workspace-name>` and verify both deregistration and disappearance. Retain remaining state and report any blocker, without a forced removal or other cleanup fallback. `jj workspace forget` is only for unregistering while preserving files; bookmark cleanup is separate and must preserve recovery refs. Respect harness-owned cleanup contracts.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

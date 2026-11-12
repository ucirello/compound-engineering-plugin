# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. Git conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh refs. Pass the local remote whose URL is the PR's base repository (the repository in the PR's URL); in a fork checkout that is often not `origin`:

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "<verified absolute target workspace root>" --remote "<base-remote>" --base "<baseRefName>" --pr "<N>"
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

**Rework.** When the user asks for the rework, write the described goal, scope, PR link and verification to a new plan under the verified workspace's `.tmp/rocketclaw/`, invoke `ce-work mode:return-to-caller <that absolute path>` on the PR head workspace, push under ordinary babysit authority, then start a fresh invocation. Return-to-caller prevents a second PR or watcher. Without push access, offer takeover instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A history rewrite outside authorized routine maintenance requires the user's explicit apply/update/rebase request in this invocation or a live mid-watch grant; an optional rewrite otherwise needs approval. Description-only requests are draft-only. Coordinator text, caller tokens and delegate results never broaden authority. Delegates retain rebase/force-push exclusions; the rewrite stays with babysit and a grant covers one rewrite. Later base movement follows ordinary currency. Factual stale-description refresh preserving user content and issue links, clean verified head alignment, and monitoring/rearming are already authorized maintenance: never bundle them into rewrite approval. Declining the rewrite does not block authorized monitoring. Honor opt-outs, watch mode, scope and human/final-merge decisions.

A check that reached Update on its own does not ask and does not rebase. A moved base alone needs no rewrite, and the ordinary watch handles a real conflict or a required update. Say in the report that a rebase is available on request, and name what it would cost when it applies: the author's local branch will need a reset when the branch is someone else's (offer takeover as the alternative), approvals the repository dismisses on push, and a squash-merge repository gaining little from a rewrite. Unattended runs never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Verify head repository, named JJ remote, bookmark, tracking and exact remote head SHA, not the possibly lagging PR mirror. Fetch that exact bookmark, recheck through `gh`, and retain a private recovery bookmark at the recorded head.
2. **Rebase in a temporary isolated workspace.** Use `ce-worktree`'s detect-isolation-first ownership/session lifecycle, verified base, single captured local YYYYMMDD plus meaningful task/PR slug, collision checks on registrations and destinations, and stable name/path identity across retries. From the source absolute root create with `jj workspace add --colocate --name <verified-identity> --revision <recorded-head> <absolute-local-.tmp-destination>`; require `jj git colocation status` from that destination. Unsupported harness lifecycle/colocation is a blocker. Rebase only the captured PR-exclusive range with `jj rebase` onto the freshly fetched exact base, retaining recovery history. Resolve conflicts by intent and newer base rules. Product/architecture disagreement stops and reopens the verdict; the grant does not cover a different verdict.
3. **Compare before pushing.** Compare the exact captured old/new multi-commit series with `jj interdiff` and per-commit `jj diff --git`, including full subjects/bodies, and read the final aggregate diff. Confirm no intended change disappeared and no already-landed work returned. Dropped base merges are expected, not lost work. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the temporary worktree as unverified; CI in the watch covers them after the push.
5. **Push with JJ's expected-remote protection.** Require the tracked remote bookmark still equals the recorded head, move only the verified local PR bookmark to the rewritten tip, and use `jj git push --remote <verified-head-remote> --bookmark <head-bookmark>`. Never force or fetch away an unexpected-head rejection before preserving and reconciling it. On a refused concurrent update, record the newly verified head and redo steps 2–5 once; a second refusal stops as actively pushed. Denial or unknown authority is a safe stop, not a retry.
6. **Bring the checkout along.** Move the user's checkout to the new head only when its tip still equals the recorded old head. Any other tip holds work that is not yours: stop and report.

Retire the disposable owned workspace whenever the update ends, whether or not it pushed, only through the verified `ce-worktree` lifecycle. Stop workers, leave the target and move the harness session first; verify exact registration/path/ownership/authorization, integration and recovery refs; copy and read back evidence outside the target. Inspect tracked/conflicted/ignored/untracked data (a snapshot does not protect the latter). From a surviving absolute root use `jj workspace remove <verified-name>` and verify both deregistration and directory disappearance. Never forget plus delete, force-delete after a warning, or delete unrelated/ambiguous/referenced data. Preserve recovery/best/archive bookmarks; bookmark deletion is separate. Failed cleanup retains state and reports a residual.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

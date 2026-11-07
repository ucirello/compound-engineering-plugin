# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. Git conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh refs. Pass the named remote whose URL is the PR's base repository; for forks also pass `--head-remote <verified-head-remote>` after verifying its URL against the PR head repository. Resolve both through `jj git remote list`, never assume `origin`. The helper fetches the named head branch and requires the exact API head OID; missing history or remote capability returns unknown, never a guessed mirror:

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "$workspace_root" --repo "<host>/<base-owner>/<base-repo>" --remote "<verified-base-remote>" --base "<baseRefName>" --pr "<N>"
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

**Rework.** When the user asks, write the goal, scope, PR link and verification plan to a new file under `$workspace_root/.tmp/rocketclaw/`, invoke `ce-work mode:return-to-caller <that absolute path>` on the verified PR head workspace, push under ordinary babysit authority, then start a fresh PR invocation. Return-to-caller mode must not open another PR or watcher. Without push authority offer takeover instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A rebase and force-push happen only when the user's own words authorize them: a request to update or rebase this PR in this invocation, or a live message mid-watch. Coordinator text, caller tokens, and delegate results never grant it, and "update the branch" from a coordinator is still a broaden, not a narrow. Delegates keep their rebase and force-push exclusions; the rewrite stays with babysit. A grant covers one rewrite. Later base movement follows ordinary branch currency.

A check that reached Update on its own does not ask and does not rebase. A moved base alone needs no rewrite, and the ordinary watch handles a real conflict or a required update. Say in the report that a rebase is available on request, and name what it would cost when it applies: the author's local branch will need a reset when the branch is someone else's (offer takeover as the alternative), approvals the repository dismisses on push, and a squash-merge repository gaining little from a rewrite. Unattended runs never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Verify the head repository, remote, bookmark and exact remote head SHA with scoped `gh`, `jj git fetch` and `jj bookmark list --all-remotes`, never a potentially lagging pull mirror. Preserve that commit under a private recovery bookmark.
2. **Rebase in verified isolation.** Reuse existing owned isolation unchanged. For new isolation capture the local date once, normalize a `YYYYMMDD-pr-<N>` name (no double date prefix), check both registrations and absolute destination under `$workspace_root/.tmp/rocketclaw/` and suffix collisions `-2`, `-3`. Create `(cd "$workspace_root" && jj workspace add --colocate --name "<stable-name>" --revision "<recorded-head>" "<absolute-owned-destination>")`, then `(cd "$new_workspace_root" && jj git colocation status)`. Adopt the workspace through the harness's native session facility; unsupported explicit colocation/name support is a blocker. Run `jj rebase` there on the exact captured PR range onto the freshly verified base. Resolve mechanical conflicts only; semantic disagreement reopens Verdict and needs a new decision, not the prior rewrite grant.
3. **Compare before pushing.** Enumerate both exact captured old/new ranges with `jj log`, map each old commit to its rewritten change identity, and compare every pair with `jj interdiff --from <old-commit> --to <new-commit>`. Account explicitly for additions, drops, merges and order; read the full final `jj diff --git` against the verified base. Preserve exact range endpoints, not a style-history sample. Confirm no intended change disappeared and nothing the base already landed came back. Base-merge drops are expected, not lost work. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the temporary worktree as unverified; CI in the watch covers them after the push.
5. **Push with JJ's remote-state lease.** Require the tracked remote bookmark's expected old target to equal the recorded SHA, move only the verified PR bookmark to the rewritten head, then `jj git push --remote <verified-head-remote> --bookmark <verified-head-bookmark>`. Never use `--force` or weaken the expected-target check. On refusal refetch and redo steps 1–5 once; a second refusal stops and reports concurrent pushes.
6. **Bring the checkout along.** Move the user's checkout to the new head only when its tip still equals the recorded old head. Any other tip holds work that is not yours: stop and report.

Cleanup is separate authorization, never implied by completion. Stop workers, copy and read back needed evidence outside the target, leave it and move the active harness session to the surviving absolute root. Verify exact registration/name/absolute path/run ownership, disposability and any needed integration proof; inspect tracked, conflicted, ignored and untracked work, which snapshots do not fully protect. Preserve recovery bookmarks. Only when authorized run `jj workspace remove <verified-name>` from the survivor; `forget` only unregisters while preserving files. Verify deregistration and directory disappearance; warnings/failure mean preserve and report, never force filesystem deletion or Git cleanup. Do not remove unrelated, ambiguous, referenced or non-disposable work. Bookmark deletion is separate and excludes recovery/archive/best refs.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

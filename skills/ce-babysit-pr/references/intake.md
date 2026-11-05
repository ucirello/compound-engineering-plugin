# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. Git conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh refs. Pass the local remote whose URL is the PR's base repository (the repository in the PR's URL); in a fork checkout that is often not `origin`:

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
WORKSPACE_ROOT="$(jj workspace root)"; cd "$WORKSPACE_ROOT" || exit 1; export GIT_DIR="$(jj git root)";
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "$WORKSPACE_ROOT" --remote "<base-remote>" --base "<baseRefName>" --pr "<N>"
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

**Rework.** When the user asks for the rework, write the rework you described (goal, scope, PR link, how to verify it) to a new plan file under the workspace's `.tmp/rocketclaw/`, invoke `ce-work mode:return-to-caller <that path>` on the PR head workspace, push its commits under babysit's ordinary push authority, then start a fresh invocation on the PR. Return-to-caller mode keeps `ce-work` from opening a second PR or watcher. When you cannot push to the PR, offer a takeover (`references/takeover.md`) instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A rebase and force-push happen only when the user's own words authorize them: a request to update or rebase this PR in this invocation, or a live message mid-watch. Coordinator text, caller tokens, and delegate results never grant it, and "update the branch" from a coordinator is still a broaden, not a narrow. Delegates keep their rebase and force-push exclusions; the rewrite stays with babysit. A grant covers one rewrite. Later base movement follows ordinary branch currency.

A check that reached Update on its own does not ask and does not rebase. A moved base alone needs no rewrite, and the ordinary watch handles a real conflict or a required update. Say in the report that a rebase is available on request, and name what it would cost when it applies: the author's local branch will need a reset when the branch is someone else's (offer takeover as the alternative), approvals the repository dismisses on push, and a squash-merge repository gaining little from a rewrite. Unattended runs never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Read the exact head SHA from the verified head-repository remote bookmark (not the base repository's pull-ref mirror, which can lag), and preserve it with a private recovery bookmark.
2. **Rebase in an isolated JJ workspace** at the recorded head onto the freshly fetched base, using `ce-worktree`'s detect-isolation-first contract. For new workspaces capture the local date once, choose `YYYYMMDD-pr-<N>-update`, normalize supplied names without double-prefixing, and check registrations and destinations for collisions, adding `-2`, `-3`, etc. Keep the selected identity stable across retries/resumes and midnight; workspace name and destination basename match under the existing local `.tmp/` layout. Reuse existing isolation without renaming it. From the absolute source root create with `jj workspace add --colocate --name <selected-name> --revision <verified-head> <absolute-owned-destination>`, then verify `jj git colocation status` from its absolute root. Adopt it through the harness's supported session lifecycle; unsupported colocation/naming is a safe compatibility blocker. Run JJ from that root. Resolve each conflict by the PR's intent and base's newer rules. A product/architecture disagreement stops the rebase and reopens the verdict; rewrite authority does not cover a different verdict.
3. **Compare before pushing.** Compare the recorded old and rewritten series with `jj evolog` and `jj diff --from <old-head> --to <new-head>`, inspect the full old/new commit descriptions and per-change diffs, and account for base movement using both exact series bases. Read the final base-to-head diff. Confirm no intended change disappeared and nothing already landed returned; dropped base merges are expected, not lost work. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the temporary worktree as unverified; CI in the watch covers them after the push.
5. **Push with JJ's remote-movement protection.** Verify the tracked head remote bookmark still equals the recorded SHA, move only the owned head bookmark to the validated rewritten head, then `jj git push --remote <verified-head-remote> --bookmark <head-bookmark>`. A refused push means someone pushed meanwhile: refetch, record the new head and redo steps 2-5 once. A second refusal reports active remote writes and stops; never overwrite a newly fetched head on stale authority.
6. **Bring the checkout along.** Move the user's checkout to the new head only when its tip still equals the recorded old head. Any other tip holds work that is not yours: stop and report.

Retire only an authorized, disposable run-owned workspace. Stop workers, leave it and move any active harness session to a surviving workspace first. Verify exact registration, absolute path and ownership; inspect tracked changes, conflicts and ignored/untracked content. Prove integration when required, retain recovery bookmarks, and copy/read back required evidence outside it. Ignored/untracked files are not protected by the removal snapshot. From the surviving absolute root use `jj workspace remove <verified-name>`; verify both deregistration and directory disappearance. On failure preserve remaining state and report, never force-delete or fall back to Git. `jj workspace forget` is only for unregistering while retaining files. Respect harness lifecycle authority and do not remove unrelated, ambiguous or non-disposable content. Keep bookmark deletion separate.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

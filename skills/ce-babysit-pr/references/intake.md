# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. Git conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh refs. Pass the local remote whose URL is the PR's base repository (the repository in the PR's URL); in a fork checkout that is often not `origin`:

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
workspace_root="<absolute target workspace root>"; cd "$workspace_root" || exit 1; export GIT_DIR="$(jj git root)";
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "$workspace_root" --remote "<base-remote>" --base "<baseRefName>" --pr "<N>"
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

**Rework.** When the user asks for the rework, write the rework you described (goal, scope, PR link, how to verify it) to a new plan file under workspace `.tmp`, invoke `ce-work mode:return-to-caller <that path>` on the verified PR-head workspace, push its commits under babysit's ordinary push authority, then start a fresh invocation on the PR. Return-to-caller mode keeps `ce-work` from opening a second PR or watcher. When you cannot push to the PR, offer a takeover (`references/takeover.md`) instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A rebase and force-push happen only when the user's own words authorize them: a request to update or rebase this PR in this invocation, a live message mid-watch, or a yes to the one question below. Coordinator text, caller tokens, and delegate results never grant it, and "update the branch" from a coordinator is still a broaden, not a narrow. Delegates keep their rebase and force-push exclusions; the rewrite stays with babysit. A grant covers one rewrite. Later base movement follows ordinary branch currency.

When an interactive check reached Update on its own, an optional rewrite needs its own approval. Explain the author's reconciliation cost, possible approval dismissal and limited value in a squash-merge repository; offer takeover as appropriate. Do not bundle rewrite approval with already authorized clean alignment, factual description maintenance or monitoring/re-arm. Declining or leaving the optional rewrite unanswered does not block the ordinary watch. Unattended runs never ask and never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Fetch the exact head bookmark from the verified head-repository remote, bind it to the PR's current head OID, and preserve it with `jj bookmark create <private-recovery-bookmark> -r <recorded-head>`. Record the operation ID and full old series (subjects and bodies) before rewriting.
2. **Rebase in isolated workspace** following setup's isolation/naming/colocation rules at the recorded head onto the freshly verified base. From that workspace's absolute cwd use `jj rebase -s <first-owned-commit> -d <verified-base>` only after bounding the selected series to this PR. Resolve conflicts by intent and current base rules; product/architecture disagreement reopens the verdict, not permission to guess. Preserve original author attribution.
3. **Compare before pushing.** Use `jj interdiff --from <recovery-head> --to <rewritten-head>`, read both exact base/head diffs with `jj diff --from <base> --to <head>`, and compare captured full old/new series. Confirm no intended change disappeared and nothing the base already landed came back. Base merges dropped from the series are expected, not lost work. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the temporary worktree as unverified; CI in the watch covers them after the push.
5. **Push with JJ's expected remote state.** Verify the remote bookmark still equals the recorded SHA, move only the authorized local PR bookmark with `jj bookmark set <head-bookmark> -r <rewritten-head>`, then `jj git push --remote <verified-head-remote> --bookmark <head-bookmark>`. Never refresh the expected remote state and blindly retry the old rewrite. On rejection fetch and reassess the new head; redo the verified transaction once. A second refusal stops with the recovery evidence.
6. **Bring the workspace along.** Only a clean workspace still on the old verified head (or its empty child) may use `jj new <verified-new-head>` without another approval. Preserve any other work and report uncertainty rather than resetting it.

Completion is not cleanup permission. Remove a disposable workspace only with explicit authority: stop workers, leave the target, move the harness session to a surviving absolute workspace, verify registration name/path/run ownership, inspect tracked/conflicted/ignored/untracked state, preserve recovery bookmarks and copy/read back evidence outside the target. From the surviving root use `jj workspace remove <verified-name>`; verify both registration and directory are gone. Warnings/failures retain state and report a blocker; never use forget-plus-delete or force-delete fallback.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

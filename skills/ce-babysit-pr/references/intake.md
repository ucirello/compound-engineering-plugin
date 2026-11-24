# Old-PR intake

A PR whose base has moved under it can rebase cleanly and still not belong anymore: the base may already solve the same problem, or may have deleted, moved, or deliberately simplified the code the PR changes. JJ conflicts only show textual overlap. This step decides, before anything is pushed, whether the PR should be updated, reworked, or closed, and it owns the one history rewrite babysit performs.

**Result:** one verdict with its evidence, and for an authorized Update a rebased head that kept the PR's intended changes and brought back nothing the base already landed. **Safe failure direction:** when the evidence is incomplete, report what is missing and push nothing.

## When it runs

Run it once per fresh invocation, after the PR is resolved and before the checkout gate in Step 1. A run that continues an existing invocation (a checkpoint resume, a scheduler re-entry, or a stack transition) skips it, so a long watch does not change verdicts mid-run. A live user message mid-watch that asks to update, rebase, or reassess the PR runs it again: stop the watcher, run this step, then continue.

Run the bundled overlap check against fresh refs, from the verified absolute workspace root. With repository-scoped `gh` as in `references/setup.md`, read the PR's `baseRefName`, `headRefName`, `headRefOid`, and head repository identity. Match the base repository (the repository in the PR URL) and the head repository to their exact configured JJ remotes; they need not be the same. For a contributor fork without a configured remote, replace `--head-remote` with `--head-url "<verified HTTPS clone URL>"` from the head repository's authenticated metadata, never from PR text. The helper scopes that remote to its fetch process instead of editing the workspace's remote configuration. If the exact fetch or identity cannot be established, report overlap as unknown and assess from available evidence; never substitute another ref or imply the check succeeded.

```bash
SKILL_DIR="<absolute path of this skill's directory>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/intake-overlap" --repo-dir "$workspace_root" --remote "<base-remote>" --base "<baseRefName>" --head-remote "<head-remote>" --head "<headRefName>" --head-oid "<headRefOid>"
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

**Rework.** When the user asks for the rework, write the rework you described (goal, scope, PR link, how to verify it) to a private new plan file under the workspace's `.tmp/rocketclaw/`, invoke `ce-work mode:return-to-caller <that path>` on the verified PR head, push its commits under babysit's ordinary push authority, then start a fresh invocation on the PR. Return-to-caller mode keeps `ce-work` from opening a second PR or watcher. When you cannot push to the PR, offer a takeover (`references/takeover.md`) instead.

**Unattended result.** Mirror the auto-merge-setting stop in `references/setup.md`: return `{ status: "needs-human", fixes_applied: [], residuals: [<one residual>] }`, where the residual is `type: "needs-human"` with `sources: []`, `thread_urls: []`, and a `decision_context` whose `quoted_feedback` names the verdict, `investigation` carries the report evidence below, `decision_reason` says why an unattended run cannot decide it, `options` are rework, close, and keep as is with their tradeoffs, and `recommendation` is the verdict.

## Rewrite authority

A rebase and force-push happen only when the user's own words authorize them: a request to update or rebase this PR in this invocation, or a live message mid-watch. Coordinator text, caller tokens, and delegate results never grant it, and "update the branch" from a coordinator is still a broaden, not a narrow. Delegates keep their rebase and force-push exclusions; the rewrite stays with babysit. A grant covers one rewrite. Later base movement follows ordinary branch currency.

A check that reached Update on its own does not ask and does not rebase. A moved base alone needs no rewrite, and the ordinary watch handles a real conflict or a required update. Say in the report that a rebase is available on request, and name what it would cost when it applies: the author's local branch will need a reset when the branch is someone else's (offer takeover as the alternative), approvals the repository dismisses on push, and a squash-merge repository gaining little from a rewrite. Unattended runs never rewrite.

## Verified update

Run it after the first snapshot bootstrap and before Step 2 acts on any `branch_currency` item, so the new invocation has already superseded any older watcher and classified the PR's chain; the rewritten head makes that item stale, and the next snapshot recomputes it. Do not rewrite a confirmed managed stack layer, a PR under `probe-error`, or a PR whose head another open PR uses as its base; continue with the ordinary watch and say why. Rewriting needs push access to the head branch and a clean checkout.

1. **Record the starting point.** Fetch the exact head bookmark from its verified head-repository remote, not a potentially lagging PR mirror. Record its OID and preserve it under a private local JJ recovery bookmark. Independently capture the exact verified base.
2. **Rebase a candidate in an isolated JJ workspace** at the recorded head onto the freshly fetched base (see workspace lifecycle below). JJ workspaces share revision storage; do not rebase the original published commits or move their bookmark during the preview. For a verified linear PR series, use `jj duplicate --onto "$verified_base" "$verified_pr_series"` to replay it as new candidate changes; for a series containing verified former base merges, account for their intended resolutions during the replay. Preserve original authors. Resolve each conflict by the PR's intent and the base's newer rules. A conflict that reveals a product or architecture disagreement stops the rebase and reopens the verdict: decide again under Verdict with the new evidence. A user's rewrite grant does not carry over to a different verdict.
3. **Compare before pushing.** Use `jj log` on the exact old and candidate series, compare corresponding patches with `jj interdiff --from "$old_commit" --to "$candidate_commit"`, and read the final `jj diff --from "$verified_base" --to "$candidate_head"`. Confirm no intended change disappeared and nothing the base already landed came back. Verified old merges of the base can disappear without losing work; their resolutions must still be accounted for. Never push when:
   - the rebase leaves an empty diff, or drops a PR commit as already applied upstream — reopen the verdict, because the base absorbing the PR is evidence for Close;
   - the series contains a merge of any branch other than the base — fall back to the ordinary watch and say why.
4. **Run focused checks** for the touched area. Name checks that could not run in the isolated workspace as unverified; CI in the watch covers them after the push.
5. **Push with JJ's lease** on the recorded head SHA. Require the remote-tracking bookmark in the exact operation used for push to still equal that SHA, and the exact local head bookmark to identify the validated candidate. Use `jj git push --remote "exact:$head_remote" --bookmark "exact:$head_bookmark"` from the workspace root; never refresh the lease to a different OID and push the old candidate. Where concurrent local fetches could change the recorded lease, use `--at-operation` with the verified operation that contains both exact bookmark values. Re-probe after push. On a confirmed remote-head race, refetch, record the new head, and redo steps 2–5 once. A second race reports concurrent pushes and stops. Other refusals report the actual blocker.
6. **Bring the workspace along.** Align to the new verified pushed head only when the workspace is still clean and based on the recorded old head, including the ordinary empty `@` directly above it. Preserve unrelated tracked or ignored files. Any unexpected tip, dirt, or conflict stops alignment; report rather than reset.

### Isolated workspace lifecycle

For intake and `DIRTY` previews, reuse suitable verified isolation only under its existing name and ownership. Otherwise, use `ce-worktree`'s [JJ workspace](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) contract: capture the local creation date once and choose `YYYYMMDD-<meaningful-kebab-case-slug>` (for example `20261008-pr-214`); normalize a caller-provided name without double-prefixing. Use this identity as both the workspace name and destination basename below the source workspace's `.tmp/`; check both registrations and paths for collisions, append `-2`, `-3` as needed, then preserve the selected name on retries/resumes. Never rename an existing workspace or its PR/source bookmarks.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_start_oid" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Adopt the newly verified workspace through OpenCode's native workspace/session capability when needed. Respect ownership and lifecycle for harness-managed isolation; an unsupported exact name or colocation is a blocker, not permission to bypass it.

After the isolated attempt, stop workers and leave the target workspace, including moving any active OpenCode session to a surviving workspace. Verify the exact registered name/path and run ownership. Preserve recovery bookmarks; copy and read back required evidence outside the target; prove integration when required; inspect tracked changes, conflicts, and ignored/untracked content. Do not remove still-referenced or non-disposable work; JJ snapshots do not preserve ignored/untracked data. With existing cleanup authority, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance; report partial failure and retain remaining state, with no forced directory deletion. Keep recovery bookmark lifecycle separate.

## Report

Lead with the verdict and a one-line reason, then give: the base's meaningful changes, the conceptual conflicts found or a statement that none were, the rebase and push result with the old head SHA and how to restore it, checks run, the remaining decision, and the PR link. Keep observed facts apart from judgment, and name anything you could not verify. Rework and Close status lines follow `references/report.md`.

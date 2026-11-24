# Shipping (LFG steps 9–11)

The shipping steps are the last stretch of the run: commit, push, PR, CI, and close-out. LFG's SKILL.md defines the shipping precondition (`jj git remote list`) and the two invocation strings. This file defines everything else: which handoff runs, what LFG passes into it, what it does with the result, and how the run closes out.

Run JJ and repository-scoped `gh` from the target workspace's absolute root. For `gh`, first resolve `GIT_DIR=$(jj git root)` successfully and export it in that shell. Pass the verified PR URL or explicit head repository and bookmark when looking up a PR; do not infer the branch from JJ's working-copy commit. An empty `@` above a pushed head is normal: also inspect `@-` and resolve its bookmarks and remote before deciding no PR exists.

## Step 9 — a project-defined process may replace the default handoff

The goal is the remaining work committed, pushed, and in an open PR whose URL you hold.

The project's active instructions may name a process for that handoff: a named skill or command, a stacking tool, or documented steps. Commit or PR-title conventions do not count, because the default already honors them, and a skill directory alone is not a directive. When such a process is named, run it non-interactively with the same plan path and context below instead of the default. It is done only when the work is pushed and you hold the URL of an open PR containing it, either one the process opened or a PR that already exists for the branch. If it cannot run headlessly or respect the JJ-only policy, is unavailable, or ends short of that state, stop as **blocked** naming the process. Do not fall through to the default or to step 10.

## Step 9 — what LFG passes into the default

Pass the recorded plan path from step 1 into the `ce-commit-push-pr` invocation, along with any proceeded-and-flagged `settled_decision_conflicts` entries from step 2, so the PR body can include its settled-decisions provenance line and its note that work proceeded under a flagged conflict. On a one-pass statement there is no plan and no brief: pass the statement as PR-description context instead. On the defect route there is no plan and no brief: pass the debug return's `root_cause` and `issue_of_record` as PR-description context instead, per `references/debug-return.md`, so the PR body carries the diagnosis and links or closes the ticket. Also pass step 6's `## Unapplied review findings` section, when one exists, as PR-description context to be rendered as a dedicated section verbatim. That section is the record of unapplied findings; a run that opened a PR without it has lost them. Check the plan's execution profile for whether it ships as one PR or several. When it ships as several, ask for a stack and name its layers: one per PR group, bottom to top in merge order, each with its units and, when its `Waits on:` line names a deployment that must be live first, that deploy dependency as PR-description context. `ce-commit-push-pr` picks the stack's babysit posture from land intent in this request, so the merge grant is decided here. When the user granted merging, include land intent so it hands off `posture:stack-land`. When any layer carries a deploy dependency, leave land intent out so it hands off `posture:stack-ready`, because no skill observes deployments; the close-out then lists each layer whose deployment the user must confirm before it merges. The stack handoff in step 10 then applies.

This commits remaining run-owned changes, pushes the verified publishing bookmark, and opens a pull request, non-interactively because of the `mode:pipeline` token. If it prints a `New concepts:` trailer after the PR URL, record the concept name(s) for step 11. If an open PR already exists for the verified head, use that PR and still commit and push run-owned work. After the push, when the existing body lacks the required handoff record above, explicitly pass `ce-commit-push-pr mode:pipeline` the verified PR URL and the instruction to **apply** that narrow factual update using the verified results and context. Preserve unrelated user-authored text and existing issue links, and verify the required record is present. This is authorized handoff maintenance, not a standalone description-only request or an optional rewrite; do not request another preview approval.

Leave optional rewrites of existing PRs out of LFG. Outside already-authorized maintenance or an explicit request to apply a description update, an optional rewrite needs approval; a description-only request stays draft-only. Declining a rewrite never blocks otherwise authorized alignment or monitoring, and a rewrite is never part of the alignment or monitoring decision.

**When no remote is configured or the defect route holds publication, do NOT invoke `ce-commit-push-pr` or a project-defined shipping process.** Commit only the remaining run-owned changes (the work source's files, review fixes, and captured learning), following the [LFG commit-message and owned-path selection instructions](review-followup.md#commit-message-standards-for-lfg-owned-commits), and skip push, PR creation/edits, and monitoring. Preserve and report unrelated pre-run work, including the defect route's `pre_fix_scope`; do not select a whole path that also includes unrelated edits.

## Step 10 — stack handoff from step 9

If step 9's `ce-commit-push-pr` completed a stack-mode submit and handed off `ce-babysit-pr` on the **bottom open non-draft** PR with `posture:stack-ready` or `posture:stack-land`:

- Do **not** start a second bare `mode:pipeline` babysit on the current-branch URL. A second run can replace the stack-aware one with a run that watches only the current PR, or watch the wrong layer of the stack.
- Prefer the structured result already returned from that handoff when it reflects a completed pipeline stop.
- If step 9 only confirmed babysit **started** (or no structured result is available), wait for the existing authorized handoff where possible; otherwise resume/re-arm that same authorized `ce-babysit-pr mode:pipeline <bottom-pr-url> posture:<same>` and wait for its pipeline completion. Never start a competing watch or treat "started" as DONE.
- Record the bottom PR URL and posture for step 11's user-facing resume line.
- Collect `{ status, fixes_applied, residuals }` and proceed to step 11.

## Step 10 — the default babysit

Otherwise invoke `ce-babysit-pr mode:pipeline <pr-url>` on the current open PR. It runs the bounded pipeline loop: it watches CI, repairs real (convergent) failures via `ce-debug mode:pipeline` without ever weakening, skipping, or mocking an assertion, resolves any review comments that arrived via `ce-resolve-pr-feedback mode:pipeline`, and stops when CI is decided or its budget (default 3 fix rounds) is hit. This replaces LFG's former hand-rolled CI loop; do not reimplement CI-watching here.

Invoke it when an open PR exists, step 9 did not already hand off babysitting, and the bounded pipeline watch is authorized. Respect any standing opt-out that covers this watch. `auto_babysit: false` suppresses the automatic open-ended handoff; it is not consent to begin a watch, and does not cancel a bounded run separately authorized by the user or workflow. Apply the same authorization before handing off stack babysitting. If monitoring was opted out of, report that it did not run and do not claim CI was decided. A run whose CI looks likely-clean is not a reason to skip authorized babysitting or poll checks yourself. A passing check while advisory checks (e.g. Bugbot) are still pending or comments are unhandled never substitutes for the invocation.

For either handoff, verify the exact pushed PR head repository, bookmark, remote, and commit before aligning a clean workspace or starting/re-arming monitoring. An empty `@` directly above that head is already aligned. Alignment and monitoring within existing authorization need no extra approval. Dirty or conflicted state, unrelated tracked or ignored work at risk, ambiguous targets, denied permissions, or unknown push authority take the safe stop path; never reset, discard, guess, or bypass a denial. During authorized babysitting, stale description facts from this run may be refreshed directly without another prompt or routing through standalone description update; preserve unrelated text and issue links. Respect watch-mode boundaries and do not treat monitoring as a merge grant.

Collect its structured result (`{ status, fixes_applied, residuals }`).

Merging is the user's unless they granted it for this run. When they did, pass the grant in the form `ce-babysit-pr` accepts: `posture:stack-land` on a managed stack, decided in step 9. A single-PR grant has no pipeline carrier today, so on that path do not merge yourself; say in the close-out that the grant could not be carried and the merge is still theirs.

## Step 10 — common result gate

This check applies to whichever handoff produced the result. If an authorized watch ran but its receipt does not establish the required CI decision, stop at step 10 and report why, including a budget limit if applicable. Keep the `needs-human` residuals the handoff returned unchanged, with every field they carry. On the defect route, add the `residuals` that `ce-debug`'s `fixed` return carried, also unchanged, even when a watch was skipped. Render the complete set under `## Needs your decision`, including each residual's quoted feedback, investigation, decision reason, options and tradeoffs, recommendation if any, and every open-thread link. A non-empty set hands decisions to the user; stop without DONE. A generic count or a PR link does not count as passing the set on. Unfixable CI belongs in the babysitter's run-report comment, never a PR-body section.

## Step 11 — close out

Everything below happens before LFG outputs `<promise>DONE</promise>`. Write the close-out, the `## Needs your decision` framing, and any progress you narrate to the user through the `ce-noslop` skill; the residual entries themselves are rendered verbatim.

### Rendering the user-runnable invocations

For the two handoffs below, default to `/ce-explain <name>` / `/ce-babysit-pr <pr-url>`. Use `$ce-explain <name>` / `$ce-babysit-pr <pr-url>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### New concepts

If step 9 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run <rendered ce-explain invocation> to go deeper.`

### The open PR

If an open PR exists and the bounded watch ran, add one line pointing the user to the interactive watch-to-merge (pipeline mode does not imply the PR merged): `PR is moving — run <rendered ce-babysit-pr invocation> to watch it through review to merge.` If monitoring was opted out of, report the open PR and that CI was not decided by this run instead.

When step 9/10 used a stack handoff, render that invocation for the **bottom open non-draft** PR URL with the same `posture:stack-ready` or `posture:stack-land` token — never a bare current-branch URL that would supersede stack scope.

### The optional next-work offer

On the defect route there is no plan: make no next-work offer. A one-pass statement has no plan either: make no next-work offer. Otherwise inspect the plan recorded in step 1 for the semantic role `work-relationships`. Load `references/next-work-handoff.md` when that role exists, or when an older unmarked Product Contract appears to name the area this plan owns plus future separately planned areas and their relationships. That reference defines the cautious legacy semantic fallback, how to choose the candidate, and how the opt-in offer is worded. Do not match an exact visible heading, treat ordinary non-goals as future work, or invoke `ce-handoff` before the user explicitly accepts the offer. If neither semantic signal exists, do not load the reference and make no next-work offer.

Then output the DONE promise.

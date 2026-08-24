# Shipping tail (LFG steps 8–10)

LFG's body owns the shipping precondition and the two invocation strings. This file owns everything that decides *which* handoff runs, what LFG threads into it, what it does with the result, and how the run closes out.

## Step 8 — a project-defined process may own the handoff

The goal is the remaining work recorded as described Jujutsu changes, pushed through a bookmark, and in an open PR whose URL you hold.

If the project's active instructions name a process that owns that handoff — a named skill or command, a stacking tool, or documented steps, but not change-description or PR-title conventions, which the default already honors, and a skill directory alone is not a directive — run it non-interactively with the same plan path and context below instead of the default. Pass LFG's exact mandated change-description sentence and all of its interpretation constraints unchanged to the process at every description-composition, editing, validation, or recommendation site. It is done only when the Jujutsu changes are described, the intended bookmark is pushed, and you hold the URL of an open PR containing them. If it cannot run headlessly, is unavailable, or ends short of that state, stop as **blocked** naming the process — do not fall through to the default or to step 9.

## Step 8 — what LFG threads into the default

Thread the recorded plan path from step 1 into the `ce-commit-push-pr` invocation, along with any proceeded-and-flagged `settled_decision_conflicts` entries from step 2, so the PR body's settled-decisions provenance line and its proceed-under-flag clause can fire. Pass LFG's exact mandated change-description sentence and all of its interpretation constraints unchanged as a constraint on every description-composition, editing, validation, or recommendation site.

This records any remaining changes, pushes the intended bookmark, and opens a pull request non-interactively under that policy. Once the PR URL is known, back-fill it into any residual tickets filed in step 6 so each ticket links to the PR carrying the finding; a failed ticket update does not block completion. If a PR already exists for the pushed bookmark, use `gh pr view <bookmark> --json number,url,state`, skip PR creation, and still describe and push any remaining change. In a non-colocated repository, point `gh` at the backing Git repository reported by `jj git root`.

**Per the shipping precondition, when no remote is configured, do not invoke `ce-commit-push-pr` or a project-defined shipping process** because those routes require a push. Apply LFG's full change-description policy to describe the non-empty working-copy change accurately, then use `jj commit` to start a new change; skip bookmark push and PR creation.

## Step 9 — stack handoff from step 8

If step 8's `ce-commit-push-pr` completed a stack-mode submit and handed off `ce-babysit-pr` on the **bottom open non-draft** PR with `posture:stack-ready` or `posture:stack-land`:

- Do **not** start a second bare `mode:pipeline` babysit on another bookmark's URL (that can supersede the stack-aware run as target-only or watch the wrong layer).
- Prefer the structured result already returned from that handoff when it reflects a completed pipeline stop.
- If step 8 only confirmed babysit **started** (or no structured result is available), re-invoke `ce-babysit-pr mode:pipeline <bottom-pr-url> posture:<same>` and wait for its pipeline completion — never treat "started" as DONE.
- Record the bottom PR URL and posture for step 10's user-facing resume line.
- Collect `{ status, fixes_applied, residuals }` and proceed to step 10.

## Step 9 — the default babysit

Otherwise invoke `ce-babysit-pr mode:pipeline <pr-url>` on the current open PR. It runs the bounded pipeline loop: watches CI, repairs real (convergent) failures via `ce-debug mode:pipeline` — never weakening, skipping, or mocking an assertion — resolves any review comments that arrived via `ce-resolve-pr-feedback mode:pipeline`, and stops when CI is decided or its budget (default 3 fix rounds) is hit. This replaces LFG's former hand-rolled CI loop; do not reimplement CI-watching here. Invoke it unconditionally whenever an open PR exists **and** step 8 did not already hand off stack babysit — a run whose CI looks likely-clean is not a reason to skip babysit and poll `gh pr checks` yourself. Green CI at one instant is not this step's goal: babysit also resolves review comments across the PR's life, so a passing check while advisory checks (e.g. Bugbot) are still pending or comments are unhandled is not "done" and never substitutes for the invocation.

Collect its structured result (`{ status, fixes_applied, residuals }`).

## Step 9 — common result gate

Whichever handoff produced the result, preserve its canonical typed `needs-human` residual set unchanged. Before DONE, render the complete set under `## Needs your decision`, including each residual's quoted feedback, investigation, decision reason, options and tradeoffs, recommendation if any, and every open-thread link. A non-empty set is a decision handoff, never successful completion; a generic count or PR link is not propagation. Unfixable CI still belongs in the babysitter's run-report comment, never a PR-body section.

## Step 10 — close out

Everything below happens before LFG outputs `<promise>DONE</promise>`.

### Rendering the user-runnable invocations

For the two handoffs below, default to `/ce-explain <name>` / `/ce-babysit-pr <pr-url>`. Use `$ce-explain <name>` / `$ce-babysit-pr <pr-url>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### New concepts

If step 8 reported new concepts, name each concept and pair it with the rendered `ce-explain` invocation. Keep the line operational and unbranded.

### The open PR

If an open PR exists, tell the user that pipeline mode stopped at CI-decided rather than merged and provide the rendered interactive watch-to-merge invocation. Do not require fixed wording.

When step 8/9 used a stack handoff, render that invocation for the **bottom open non-draft** PR URL with the same `posture:stack-ready` or `posture:stack-land` token — never another bookmark's URL that would supersede stack scope.

### The optional next-work offer

Inspect the canonical plan from step 1 for the semantic role `work-relationships`. Load `references/next-work-handoff.md` when that role exists, or when an older unmarked Product Contract appears to name the area this plan owns plus future separately planned areas and their relationships; that reference owns the cautious legacy semantic fallback, candidate selection, and the opt-in offer contract. Do not match an exact visible heading, treat ordinary non-goals as future work, or invoke `ce-handoff` before the user explicitly accepts the offer. If neither semantic signal exists, do not load the reference and make no next-work offer.

Then output the DONE promise.

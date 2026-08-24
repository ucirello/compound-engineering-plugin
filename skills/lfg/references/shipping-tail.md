# Shipping tail (LFG steps 8–10)

LFG's body owns the shipping precondition. This file owns everything that decides *which* handoff runs, how the JJ delivery stack is described and published, what LFG threads into a delegated process, what it does with the result, and how the run closes out.

## Step 8 — a project-defined process may own the handoff

The goal is the remaining work represented by described JJ changes, published through one explicit bookmark, and in an open PR whose URL you hold.

If the project's active instructions name a process that owns that handoff and supports JJ changes and bookmarks — a named skill or command, a stacking tool, or documented steps, but not message or PR-title conventions, and a skill directory alone is not a directive — run it non-interactively with the same plan path and context below instead of the default. This includes `ce-commit-push-pr` when its listed contract explicitly supports JJ semantics. It is done only when the bookmark is published and you hold the URL of an open PR containing it. If it cannot run headlessly, is unavailable, uses mutating Git branch/index operations, or ends short of that state, stop as **blocked** naming the process — do not silently mix repository models or fall through to the default.

## Step 8 — native JJ handoff

Use the recorded plan path from step 1 and any proceeded-and-flagged `settled_decision_conflicts` entries from step 2 when composing the PR body, preserving its settled-decisions provenance and proceed-under-flag clause.

Inspect `jj status`, `jj diff`, and the `trunk()..@` stack. Resolve all file and bookmark conflicts before publication; JJ records conflicts without interrupting operations, but GitHub cannot receive conflicted revisions. Separate remaining unrelated edits rather than publishing them. For each remaining delivery change that lacks an adequate description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax or example. Preserve each change's semantic purpose and any required provenance or trailers.

Select or create one explicit local shipping bookmark for the top non-empty described change in the complete delivery stack. Use `jj bookmark create <shipping-bookmark> -r <stack-head>` when absent and `jj bookmark move <shipping-bookmark> --to <stack-head>` after a forward rewrite; a backward or sideways move is allowed only when the reviewed stack rewrite requires it. JJ has no active bookmark, so never infer one from the working copy. Select the writable remote from the project's JJ configuration and active conventions; prefer the configured `git.push` remote, otherwise use the sole remote, and stop as blocked rather than guessing among multiple writable candidates. Fetch that remote before publishing. If the fetch makes the bookmark conflicted or reveals a remote update, reconcile the targets and rebase the delivery stack as local policy requires, then rerun required verification before publishing. Push only the shipping bookmark with `jj git push --bookmark <shipping-bookmark> --remote <remote>`; rely on JJ's remote-state safety checks and never bypass them.

Query GitHub for an existing open PR by the shipping bookmark. Create one with `gh pr create --head <shipping-bookmark>` only when none exists, following the repository's PR title/body conventions and including the plan and settled-decision context above. For non-colocated workspaces, run each `gh` operation with `GIT_DIR` set to `jj git root`. Once the PR URL is known, post any retained residual run-report section from step 6 and back-fill the URL into filed residual tickets; these ticket updates are best-effort and never block DONE. If a delegated process prints a `New concepts:` trailer after the PR URL, record the concept names for step 10.

**Per the shipping precondition, when no remote is configured, do not invoke a publishing process.** Preserve the delivery as described JJ changes locally, applying the same message rule above, and skip bookmark publication and PR creation entirely.

## Step 9 — stack handoff from step 8

If step 8's project-defined process completed a stack-mode submit and handed off `ce-babysit-pr` on the **bottom open non-draft** PR with `posture:stack-ready` or `posture:stack-land`:

- Do **not** start a second bare `mode:pipeline` babysit on the shipping-bookmark URL (that can supersede the stack-aware run as target-only or watch the wrong layer).
- Prefer the structured result already returned from that handoff when it reflects a completed pipeline stop.
- If step 8 only confirmed babysit **started** (or no structured result is available), re-invoke `ce-babysit-pr mode:pipeline <bottom-pr-url> posture:<same>` and wait for its pipeline completion — never treat "started" as DONE.
- Record the bottom PR URL and posture for step 10's user-facing resume line.
- Collect `{ status, fixes_applied, residuals }` and proceed to step 10.

## Step 9 — the default babysit

Otherwise invoke `ce-babysit-pr mode:pipeline <pr-url>` on the shipping bookmark's open PR. It runs the bounded pipeline loop: watches CI, repairs real convergent failures via `ce-debug mode:pipeline` without weakening, skipping, or mocking an assertion, resolves review comments via `ce-resolve-pr-feedback mode:pipeline`, and stops when CI is decided or its budget is hit. Do not reimplement CI-watching here. Invoke it whenever an open PR exists and step 8 did not already hand off stack babysit; a passing check while advisory checks or comments remain pending does not substitute for the invocation.

Collect its structured result (`{ status, fixes_applied, residuals }`).

## Step 9 — common result gate

Whichever handoff produced the result, preserve its canonical typed `needs-human` residual set unchanged. Before DONE, render the complete set under `## Needs your decision`, including each residual's quoted feedback, investigation, decision reason, options and tradeoffs, recommendation if any, and every open-thread link. A non-empty set is a decision handoff, never successful completion; a generic count or PR link is not propagation. Unfixable CI still belongs in the babysitter's run-report comment, never a PR-body section.

## Step 10 — close out

Everything below happens before LFG outputs `<promise>DONE</promise>`.

### Rendering the user-runnable invocations

For the two handoffs below, default to `/ce-explain <name>` / `/ce-babysit-pr <pr-url>`. Use `$ce-explain <name>` / `$ce-babysit-pr <pr-url>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### New concepts

If step 8 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run <rendered ce-explain invocation> to go deeper.`

### The open PR

If an open PR exists, add one line pointing the user to the interactive watch-to-merge (pipeline mode stopped at "CI decided," not "merged"): `PR is moving — run <rendered ce-babysit-pr invocation> to watch it through review to merge.`

When step 8/9 used a stack handoff, render that invocation for the **bottom open non-draft** PR URL with the same `posture:stack-ready` or `posture:stack-land` token — never a bare shipping-bookmark URL that would supersede stack scope.

### The optional next-work offer

Inspect the canonical plan from step 1 for the semantic role `work-relationships`. Load `references/next-work-handoff.md` when that role exists, or when an older unmarked Product Contract appears to name the area this plan owns plus future separately planned areas and their relationships; that reference owns the cautious legacy semantic fallback, candidate selection, and the opt-in offer contract. Do not match an exact visible heading, treat ordinary non-goals as future work, or invoke `ce-handoff` before the user explicitly accepts the offer. If neither semantic signal exists, do not load the reference and make no next-work offer.

Then output the DONE promise.

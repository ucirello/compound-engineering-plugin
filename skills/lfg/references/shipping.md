# Shipping (LFG steps 9–11)

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

The shipping steps are the last stretch of the run: commit, push, PR, CI, and close-out. LFG's SKILL.md defines the shipping precondition (the `jj git remote list` check) and the two invocation strings. This file defines everything else: which handoff runs, what LFG passes into it, what it does with the result, and how the run closes out. Every JJ command uses the absolute target workspace cwd. Every repository `gh` invocation, including the PR lookup below, uses that cwd and `GIT_DIR=$(jj git root)`.

## Step 9 — a project-defined process may replace the default handoff

The goal is the remaining work committed, pushed, and in an open PR whose URL you hold.

The project's active instructions may name a process for that handoff: a named skill or command, a stacking tool, or documented steps. Commit or PR-title conventions do not count, because the default already honors them, and a skill directory alone is not a directive. When such a process is named, run it non-interactively with the same plan path and context below instead of the default. It is done only when the work is pushed and you hold the URL of an open PR containing it, either one the process opened or a PR that already exists for the branch. If it cannot run headlessly, is unavailable, or ends short of that state, stop as **blocked** naming the process. Do not fall through to the default or to step 10.

## Step 9 — what LFG passes into the default

Pass the recorded plan path from step 1 into the `ce-commit-push-pr` invocation, along with any proceeded-and-flagged `settled_decision_conflicts` entries from step 2, so the PR body can include its settled-decisions provenance line and its note that work proceeded under a flagged conflict. On the defect route there is no plan and no brief: pass the debug return's `root_cause` and `issue_of_record` as PR-description context instead, per `references/debug-return.md`, so the PR body carries the diagnosis and links or closes the ticket. Also pass step 6's `## Unapplied review findings` section, when one exists, as PR-description context to be rendered as a dedicated section verbatim. That section is the record of unapplied findings; a run that opened a PR without it has lost them. Check the plan's execution profile for whether it ships as one PR or several. When it ships as several, ask for a stack and name its layers: one per PR group, bottom to top in merge order, each with its units and, when its `Waits on:` line names a deployment that must be live first, that deploy dependency as PR-description context. `ce-commit-push-pr` picks the stack's babysit posture from land intent in this request, so the merge grant is decided here. When the user granted merging, include land intent so it hands off `posture:stack-land`. When any layer carries a deploy dependency, leave land intent out so it hands off `posture:stack-ready`, because no skill observes deployments; the close-out then lists each layer whose deployment the user must confirm before it merges. The stack handoff in step 10 then applies.

This commits any remaining changes, pushes the branch, and opens a pull request, non-interactively because of the `mode:pipeline` token. If it prints a `New concepts:` trailer after the PR URL, record the concept name(s) for step 11. If a PR already exists for the branch (check with `gh pr view --json number,url,state 2>/dev/null`), skip PR creation but still commit and push any uncommitted changes. Pipeline mode leaves an existing PR body alone by default, so the description context above would be lost there; after the push, invoke `ce-commit-push-pr mode:pipeline` again in its description-update mode on that PR with the same context, so the record reaches the reviewer without a confirmation prompt.

**Per the shipping precondition, when no remote is configured, do NOT invoke `ce-commit-push-pr` or a project-defined shipping process.** Instead capture only the files/hunks this run changed in a JJ change (the work source's files, review fixes, and captured learning), and skip push and PR creation entirely. A file already dirty before the run, or listed in the defect route's `pre_fix_scope`, stays outside that change and is named in the report; never capture all files indiscriminately. Apply the full commit-message standards in `references/review-followup.md`: read https://go.dev/wiki/CommitMessage in full and inspect several recent subjects and bodies from task-verified history before composing. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Use `jj describe -m "<message composed from the standards above>"`; repository-local syntax always wins.

### Authorized maintenance is not a new approval gate

Pass the existing run authority to shipping and babysitting: routine factual PR-description refresh applies without preview or yes/no, preserving unrelated text and issue links. Description-only mode remains draft-only. Clean alignment to the exact verified pushed PR head and authorized monitoring/re-arm need no new approval; an empty `@` above that head is already aligned, not evidence of no work (inspect `@-`, bookmarks, remotes, and eligible PRs too). Verify repository, bookmark, remote, commit, and authority, preserve dirty/conflicted/ignored/untracked content, and stop safely when uncertain or denied; never reset. Optional rewrites outside authorized maintenance or explicit apply still need approval, but declining them never blocks authorized monitoring. Do not bundle rewrite approval with alignment or monitoring. Preserve merge, scope-expansion, human-decision, and opt-out boundaries.

## Step 10 — stack handoff from step 9

If step 9's `ce-commit-push-pr` completed a stack-mode submit and handed off `ce-babysit-pr` on the **bottom open non-draft** PR with `posture:stack-ready` or `posture:stack-land`:

- Do **not** start a second bare `mode:pipeline` babysit on the current-branch URL. A second run can replace the stack-aware one with a run that watches only the current PR, or watch the wrong layer of the stack.
- Prefer the structured result already returned from that handoff when it reflects a completed pipeline stop.
- If step 9 only confirmed babysit **started** (or no structured result is available), re-invoke `ce-babysit-pr mode:pipeline <bottom-pr-url> posture:<same>` and wait for its pipeline completion — never treat "started" as DONE.
- Record the bottom PR URL and posture for step 11's user-facing resume line.
- Collect `{ status, fixes_applied, residuals }` and proceed to step 11.

## Step 10 — the default babysit

Otherwise invoke `ce-babysit-pr mode:pipeline <pr-url>` on the current open PR. It runs the bounded pipeline loop: it watches CI, repairs real (convergent) failures via `ce-debug mode:pipeline` without ever weakening, skipping, or mocking an assertion, resolves any review comments that arrived via `ce-resolve-pr-feedback mode:pipeline`, and stops when CI is decided or its budget (default 3 fix rounds) is hit. This replaces LFG's former hand-rolled CI loop; do not reimplement CI-watching here.

Invoke it unconditionally whenever an open PR exists **and** step 9 did not already hand off stack babysit. That includes a run under a standing `auto_babysit: false`: that setting opts out of the open-ended watch handed off after a PR is opened, not of this bounded loop that produces the pipeline's "CI decided" result. A run whose CI looks likely-clean is not a reason to skip babysit and poll `gh pr checks` yourself. Green CI at one instant is not this step's goal: babysit also resolves review comments across the PR's life, so a passing check while advisory checks (e.g. Bugbot) are still pending or comments are unhandled is not "done" and never substitutes for the invocation.

Collect its structured result (`{ status, fixes_applied, residuals }`).

Merging is the user's unless they granted it for this run. When they did, pass the grant in the form `ce-babysit-pr` accepts: `posture:stack-land` on a managed stack, decided in step 9. A single-PR grant has no pipeline carrier today, so on that path do not merge yourself; say in the close-out that the grant could not be carried and the merge is still theirs.

## Step 10 — common result gate

This check applies to whichever handoff produced the result. Keep the `needs-human` residuals it returned unchanged, with every field they carry. Before DONE, render the complete set under `## Needs your decision`, including each residual's quoted feedback, investigation, decision reason, options and tradeoffs, recommendation if any, and every open-thread link. A non-empty set means the run hands decisions to the user; it is never successful completion. A generic count or a PR link does not count as passing the set on. Unfixable CI still belongs in the babysitter's run-report comment, never a PR-body section.

## Step 11 — close out

Everything below happens before LFG outputs `<promise>DONE</promise>`. Write the close-out, the `## Needs your decision` framing, and any progress you narrate to the user through the `ce-noslop` skill; the residual entries themselves are rendered verbatim.

### Rendering the user-runnable invocations

For the two handoffs below, default to `/ce-explain <name>` / `/ce-babysit-pr <pr-url>`. Use `$ce-explain <name>` / `$ce-babysit-pr <pr-url>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### New concepts

If step 9 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run <rendered ce-explain invocation> to go deeper.`

### The open PR

If an open PR exists, add one line pointing the user to the interactive watch-to-merge (pipeline mode stopped at "CI decided," not "merged"): `PR is moving — run <rendered ce-babysit-pr invocation> to watch it through review to merge.`

When step 9/10 used a stack handoff, render that invocation for the **bottom open non-draft** PR URL with the same `posture:stack-ready` or `posture:stack-land` token — never a bare current-branch URL that would supersede stack scope.

### The optional next-work offer

On the defect route there is no plan: make no next-work offer. Otherwise inspect the plan recorded in step 1 for the semantic role `work-relationships`. Load `references/next-work-handoff.md` when that role exists, or when an older unmarked Product Contract appears to name the area this plan owns plus future separately planned areas and their relationships. That reference defines the cautious legacy semantic fallback, how to choose the candidate, and how the opt-in offer is worded. Do not match an exact visible heading, treat ordinary non-goals as future work, or invoke `ce-handoff` before the user explicitly accepts the offer. If neither semantic signal exists, do not load the reference and make no next-work offer.

Then output the DONE promise.

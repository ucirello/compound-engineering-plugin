---
name: ce-debug
description: "Diagnosis loop for bugs and failing behavior. Use when asked to debug or fix failing or slow behavior."
argument-hint: "[issue reference, error message, test path, or description of broken behavior]"
---

# Debug and Fix

Find the root cause of a failure, then — when the user chooses to — fix it with test-first discipline.

**Done when:** the causal chain from trigger to symptom is stated with no gaps and file:line evidence, and either a verified fix has been handed off (PR, commit, or the user's chosen stop) or a diagnosis-only summary has been delivered. **Escalate rather than persist:** 2-3 hypotheses exhausted without confirmation, or 3 failed fix attempts, means diagnose *why* instead of trying again — that is the smart escalation `references/investigate.md` describes. One hypothesis, one change at a time; changing several to see what helps is shotgun debugging.

`<bug_description>` is whatever this skill was invoked with — a failure description, a `mode:` token, or an issue reference (`#123`, `org/repo#123`, an issue URL) — from the user or from a calling skill (`ce-babysit-pr` / `lfg` in `mode:pipeline` pass the failing jobs and log tails; `lfg`'s defect route passes `mode:return-to-caller` and the user's own reference). Blank if nothing was provided.


## Mode

Default is **interactive**: investigate, run the Phase 2 fix-choice gate, then the Phase 4 handoff.

**`mode:pipeline`** (set by an orchestrator such as `ce-babysit-pr` or `lfg`): run fully non-interactively and never call the blocking-question tool. Strip the token from `<bug_description>`, then **read `references/pipeline-mode.md` and follow it** — it overrides every "ask the user" point with a conservative default, replaces the Phase 2 fix-gate with "fix convergent bugs, defer divergent ones", and replaces the Phase 4 handoff with a structured return whose `status` is exactly one of `fixed-and-pushed | fixed-not-pushed | diagnosed-no-fix | flaky-infra | needs-human`. The caller branches on those exact spellings, so never rename, abbreviate, or add to them.

**`mode:return-to-caller`** (set by `lfg` on its defect route): run non-interactively, but the caller owns everything after the fix. Strip the token, then **read `references/return-to-caller.md` and follow it** — it keeps Phases 0-3 and the convergent-or-defer fix boundary, applies the Phase 3 branch rule so the fix lands on a feature branch, commits the fix-owned files without pushing, skips the post-fix polish and review steps, and returns a structured result whose `status` is exactly one of `fixed | diagnosed-no-fix | needs-human | blocked`. The same spelling rule applies.

## Blocking questions

Wherever this skill asks the user something, use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to numbered options on the host's chat surface only when no such tool is in the list or a real question call errors. Never silently skip the question, and never end a phase without a response.

## Secrets in evidence

Debugging surfaces raw output constantly — command results, captured payloads, log excerpts — so check for secrets before running a command. Keep credentials in env vars rather than on the command line. Redact sensitive output before writing any file or surfacing excerpts; use `<REDACTED>` and keep temporary captures, including fallbacks, under the workspace's `.tmp/` (local `.tmp/` outside JJ). Do not write raw secrets. If sanitizing removes what the diagnosis needs, say so and follow the mode's ask/defer rule rather than un-redacting.

## Artifact Root

Resolve `<root>` only when you first compose a `<root>/` path — a run that composes none skips this entirely.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `$workspace_root/.rocketclaw/config.yaml` only, where `workspace_root` is the absolute JJ workspace root discovered with `jj workspace root`. Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither its root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Execution Flow

Five phases in order: **0 Triage -> 1 Investigate -> 2 Root Cause -> 3 Fix -> 4 Handoff.** Beyond Phase 0's trivial-bug fast-path there is no skipping and no complexity tiers. A hard bug spends longer in each phase; it does not enter fewer.

Give each file you read its own tool call, so its output comes back on its own, never several files in one command or one script. A read counts only when the whole file came back. Some hosts cut the middle out of a long tool output and leave a truncation marker in its place, so when a read comes back shortened, read the missing lines in smaller ranges before you act on that file.

**Read `references/investigate.md` now and follow it for Phases 0-2** — issue fetching, reproduction, environment sanity and the isolated clean comparison, backward tracing, the tracker/PR-history search, hypothesis grounding, and the escalation table. Run repository operations from the target workspace's verified absolute root. Only the gates below are stated here.

**The issue of record.** If the user handed you a ticket or issue, that is where this bug already lives, whichever system it is in; a Sentry issue counts as much as a Linear ticket. Carry its identifier and URL through to Phase 4. State its title, as the record gives it, before Phase 1 starts; if the fetch could not get one, say that rather than composing a title. If the input is only a stack trace, test path, or description, this run has **no issue of record**. That is an ordinary state, not a gap to fill: ship the fix without one, never open a ticket to manufacture a record, and never ask the user whether to. Phase 1's tracker search reads prior work and **never establishes a new home for the bug**. An existing ticket for this bug is one to *link* in Phase 4, never one to create.

**The trivial-bug fast-path** (cause readable from the input, one-line fix, no deep tracing) still runs Phase 2's fix-choice gate before editing: it saves investigation ceremony, not the user's choice over whether to apply a fix.

**Choosing the regression test.** The regression test for a *confirmed defect* belongs wherever existing coverage already owns that behavior: start from the tests that exist rather than from a new file. Before recommending a test in Phase 2, inspect the existing tests and follow the project's testing rules; `references/fix.md` holds the test homes and the naming rule for Phase 3. Wherever you name where the regression test should live, say in one line what that seam catches and what it misses. A test that fails because the change deliberately reverses the behavior it asserts does not have a wrong expectation — that is the divergent case below, deferred rather than updated.

### Phase 2 gate: present, then ask

**Causal chain gate:** do not proceed to Phase 3 until you can explain the full chain — trigger through every step to the observed symptom — with no gaps. "Somehow X leads to Y" is a gap. Only the user can authorize proceeding on a best-available hypothesis when investigation is stuck.

**Repair selection:** after confirming the cause and before recommending a fix, read `references/bakeoff.md` to decide whether the repair needs competing approaches.

Once the root cause is confirmed, write the findings as a user-visible block: the causal chain with file:line references; the proposed fix and the files it changes; which tests to use, add, modify, or strengthen, and whether existing tests should have caught this; and any related ticket or PR and how it shapes the recommendation — if an open PR already fixes this, lead with that link instead of a fresh fix. When the deciding fact was not visible at first look and took a deep dig to surface, because the existing logs, metrics, and errors did not show it, also propose the cheap always-on signal that would have shown it immediately: a log field, a metric, or an assertion. This is a proposal only; adding the signal is not part of the minimal fix.

**Same-turn presentation before the gate:** do not open the fix-choice question until that findings block has been written in full — in this turn or the immediately preceding assistant message. The blocking question tool renders only its own stem on modal harnesses, so a question fired on "root cause confirmed" alone leaves the user choosing with none of the causal chain in front of them. Naming the options is not presenting the findings, and a promise to explain after the choice is too late.

When the request has not already authorized the next action, ask (per **Blocking questions**) which path to take. An explicit fix request is Phase 3. An explicit diagnosis-only request skips to Phase 4. `mode:pipeline` and `mode:return-to-caller` never ask. The test recommendations are part of the diagnosis either way. Offer only the options the findings support, and recommend one:

1. **Fix it now** — proceed to Phase 3
2. **Diagnosis only — I'll take it from here** — skip the fix, write Phase 4's summary, end the skill
3. **Rethink the design** (`ce-brainstorm`) — only when the bug cannot be fixed within the current design: the root cause is a wrong responsibility or interface rather than wrong logic, the requirements themselves are wrong, or every candidate fix is a workaround around an assumption that no longer holds. Size alone is not a design problem. Recommend it over a fix when no fix within the current design corrects the mechanism that produced the bug, only this occurrence of it.

When the findings leave nothing for this run to fix (the behavior is correct, the bug is already fixed, or an open PR already does the work), offer the next step they support in place of a fix, such as replying on the issue of record or finishing that PR. Replying on the issue, closing it, or changing an existing PR waits for the user's choice.

**`mode:pipeline` and `mode:return-to-caller`:** do not ask. Proceed to Phase 3 and apply a **convergent** fix; a **divergent** fix — one that would reverse a deliberate contract/behavior/product decision, including a "failing" test that asserts intended behavior — is deferred, not applied, per `references/pipeline-mode.md` or `references/return-to-caller.md`. Never route to `ce-brainstorm` here; a design problem becomes a `needs-human` residual.

### Phase 3: Fix

If the user chose "Diagnosis only," skip to Phase 4's summary. If they chose "Rethink the design," control has transferred to `ce-brainstorm` and this skill ends.

**Read `references/fix.md` before editing any file** — the test-first sequence, the failed-fix rule, the check of other places the fix affects, and the post-mortem trigger. Two rules decide whether the fix may start at all, so they stay here:

- **Branch.** From the absolute JJ workspace root, resolve the actual default bookmark from repository conventions and the verified remote's default. Inspect the current revision and its parents without snapshotting first: the workspace may sit on an empty `@` above the branch or PR head. If `@` itself is the existing branch/PR head, do not rewrite it. Start a separate working-copy change with `jj new "$verified_history_head"` only after proving the current working copy can be left without moving a source bookmark, losing edits, or capturing unrelated work; otherwise stop or defer. Run `jj status` once it is safe to snapshot. Confirm overlapping user edits interactively; in non-interactive modes follow the mode's own scope and stop rules. On the default bookmark, or with no safely identified feature bookmark, choose a collision-free feature name from the bug and create it before editing with `jj bookmark create --revision "$verified_history_head" -- "$feature_bookmark"`. Report its name. Do not anchor it to a change carrying user WIP. Advance only the authorized feature/PR bookmark to the resulting fix commit. Pipeline mode instead uses the caller's verified PR bookmark.
- **Record the pre-fix scope:** save the exact pre-edit tree's commit ID and separately the verified branch/history head, default bookmark, relevant commit range, conflicts, and existing changed or untracked files. Use the tree ID for fix-only comparison, not a moving `@` or a guessed default. Keep a list of **fix-owned files** as you work. Phase 4 cannot reconstruct this record afterwards.

### Phase 4: Handoff

**`mode:pipeline` — skip this entire interactive handoff.** No polish or review steps, no residual questions, no preview, no learning-capture offer. Commit and push the convergent fix per `references/pipeline-mode.md`, then emit that reference's **structured return**. Divergent / needs-human items are deferred there (open thread or the caller's run-report comment — never a PR-body section). **`mode:return-to-caller` — skip it too:** commit the fix-owned files on the feature branch, push nothing, and emit the structured return `references/return-to-caller.md` defines. In both modes the return is the last thing this skill writes. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the return; do not announce a handoff to it. The rest of this section is the interactive path only.

**Structured summary** — write it before the routing below. When the findings block is already on screen, do not repeat it: give the root cause in a line and spend the summary on what changed since, how the fix was verified, and its limits. A diagnosis-only summary stands on its own.

```
## Debug Summary
**Problem**: [What was broken]
**Root Cause**: [Full causal chain, with file:line references — or one line pointing back to the findings block when it is already on screen]
**Recommended Tests**: [Diagnosis only: tests to add or modify to prevent recurrence, with file, assertion guidance, and one line on what that seam catches and misses. Omit when Phase 3 ran]
**Fix**: [What was changed, including every other site of the same mistake, and how it was verified — or "diagnosis only" if Phase 3 was skipped]
**Prevention**: [Test coverage added; structural fix or operation guard if applicable, or the structural fix left as follow-up; the always-on signal the findings block proposed, when it proposed one]
**Confidence**: [High/Medium/Low]
```

**If Phase 3 was skipped**, stop after the summary — the user already said they were taking it from here. Do not prompt.

**If Phase 3 ran, read `references/post-fix-handoff.md` now and follow it before routing below.** It defines the quality steps after a fix: the contextual-override checks, the rule for when review may be skipped, the scoping that keeps `ce-simplify-code` and `ce-code-review` off unrelated branch work, what to do with leftover findings, the `## Post-Fix Quality` block, and the criteria for offering to capture a learning. None of that appears in this body. The routing below names *which* action runs, never the scope rules that make it safe, so it cannot be improvised from. Skipping the read ships an unreviewed fix, lets review reach into unrelated branch work, and strands accepted findings in the session.

#### Routing

**Land the fix without carrying along anything the user did not offer up** — not into a commit, not into a push, not into a PR. Do not ask whether to open a PR; permission is not the gate. Two questions decide the handoff. Answer them from the pre-fix scope Phase 3 recorded, not from how the branch came to exist. **Fire the action itself** via the platform's skill-invocation primitive — never merely tell the user to type a command.

**Settle learning capture before anything commits.** Apply the reference's learning-capture criteria. Only when they call for it, offer capture; if the user accepts, invoke the `ce-compound` skill and add only the artifacts it actually wrote or updated to the fix-owned files, so they ship in the same commit as the fix. If it writes nothing, no artifact joins the commit.

**1. What may go into the commit — the fix-owned files and nothing else.** This is a constraint on whichever skill commits in question 2, never an action of its own. It holds on every route, remote or not. Do not commit here.

- If no fix-owned file carried pre-existing edits, those files are the commit scope. Pass them to whichever skill commits.
- If a fix-owned file already carried the user's edits, no commit can separate them: `ce-commit` groups at file level and never splits a file. Ask (per **Blocking questions**) *before* anything commits whether to commit that file including their edits, leave the fix uncommitted, or stop. Only the first answer continues. The other two end the handoff, so question 2 never runs and nothing commits; say what was left and why. Every option loses something the agent cannot choose on the user's behalf, which is why this question survives. Phase 3's confirmation covered *editing* the file, never committing the user's edits with the fix.

**2. Who commits, and whether it ships.** Exactly one of these runs.

- **Ships** when all three hold: the pre-fix tree was clean, nothing on the branch is work the user has not already offered, and the verified remote is **PR-capable**: somewhere `gh` can actually open a PR. For repository-scoped `gh`, from the verified workspace root resolve `GIT_DIR="$(jj git root)"` successfully and export it in that same subshell before calling `gh`. Two facts make it less obvious than it looks.
  - `ce-commit-push-pr` pushes the **whole branch**, and its PR spans every commit on it, not just your fix. So the question is about the branch, not your diff. It also pushes *before* creating the PR, so a remote `gh` cannot open a PR against leaves the branch published with no PR.
  - Already pushed is not already **offered**. Commits in an open PR are under review, so they are offered, and this run updates that PR rather than opening a second one. Commits pushed for backup or to trigger CI are not offered, and a first PR would publish them. Compare against the remote rather than a local ref: a local branch, including the default branch Phase 3 may have branched off, can itself be ahead of what was pushed.

  If you cannot establish all three, take the local route instead; that is the safe direction, and the preview is not a substitute for it. Otherwise preview what will be committed, on what bookmark, and whether a PR opens or updates, then **invoke `ce-commit-push-pr`** with the verified bookmark and question 1's file scope. Do not commit first. The preview is a statement, not a question. Surface the resulting PR URL.
- **Stays local** when any of those three fails. Invoke the `ce-commit` skill under question 1's scope and push nothing. Say in one line what stayed local and why, and that you will push and open the PR on request. Do not ask first; a local commit is reversible.
- **Not in a JJ workspace**: nothing commits. Stop after the summary and the quality block.

**Contextual override** ("don't open PRs from skills", "commit only", "stop after the fix") — follow what the user said, and **Stop here** without committing when that is what they asked for. When an override stops the handoff, say which instruction stopped it and that you will commit, push, or open the PR on request. A vague tonal cue is not an override.

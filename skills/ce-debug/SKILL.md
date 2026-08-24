---
name: ce-debug
description: "Diagnosis loop for bugs and failing behavior. Use when asked to debug or fix failing behavior."
argument-hint: "[issue reference, error message, test path, or description of broken behavior]"
---

# Debug and Fix

Find the root cause of a failure, then — when the user chooses to — fix it with test-first discipline.

**Done when:** the causal chain from trigger to symptom is stated with no gaps and file:line evidence, and either a verified fix has been handed off as a described Jujutsu change, a PR, or the user's chosen stop, or a diagnosis-only summary has been delivered. **Escalate rather than persist:** 2-3 hypotheses exhausted without confirmation, or 3 failed fix attempts, means diagnose *why* instead of trying again — that is the smart escalation `references/investigate.md` describes. One hypothesis, one change at a time; changing several to see what helps is shotgun debugging.

`<bug_description>` is whatever this skill was invoked with — a failure description, a `mode:` token, or an issue reference (`#123`, `org/repo#123`, an issue URL) — from the user or from a calling skill (`ce-babysit-pr` / `lfg` in `mode:pipeline` pass the failing jobs and log tails). Blank if nothing was provided.


## Mode

Default is **interactive**: investigate, run the Phase 2 fix-choice gate, then the Phase 4 handoff.

**`mode:pipeline`** (set by an orchestrator such as `ce-babysit-pr` or `lfg`): run fully non-interactively and never call the blocking-question tool. Strip the token from `<bug_description>`, then **read `references/pipeline-mode.md` and follow it** — it overrides every "ask the user" point with a conservative default, replaces the Phase 2 fix-gate with "fix convergent bugs, defer divergent ones", and replaces the Phase 4 handoff with a structured return whose `status` is exactly one of `fixed-and-pushed | fixed-not-pushed | diagnosed-no-fix | flaky-infra | needs-human`. The caller branches on those exact spellings, so never rename, abbreviate, or add to them.

## Blocking questions

Wherever this skill asks the user something, use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to numbered options on the host's chat surface only when no such tool is in the list or a real question call errors. Never silently skip the question, and never end a phase without a response.

## Workspace Paths

Resolve `<workspace-root>` with `jj workspace root`. Outside a Jujutsu workspace, use the current working directory as the local root. Put every temporary file or directory under `<workspace-root>/.tmp/rocketclaw`; never use an OS-global temporary location. Create a unique child when concurrent runs could collide, and remove only paths created by this run.

Resolve `<root>` only when you first compose a durable artifact path; a run that composes none skips this entirely.

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only. Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value; never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.

## Execution Flow

Five phases in order: **0 Triage -> 1 Investigate -> 2 Root Cause -> 3 Fix -> 4 Handoff.** Beyond Phase 0's trivial-bug fast-path there is no skipping and no complexity tiers — a hard bug spends longer in each phase, it does not enter fewer.

**Read `references/investigate.md` now and follow it for Phases 0-2** — issue fetching, reproduction, environment sanity and the isolated-workspace experiment, backward tracing, the tracker/PR-history search, hypothesis grounding, and the escalation table. Only the gates below are stated here.

**The issue of record.** Whatever the user handed you is where this bug already lives, whichever system that is — a Sentry issue counts as much as a Linear ticket. Carry its identifier and URL through to Phase 4. Input that is only a stack trace, test path, or description means this run has **no issue of record**. That is an ordinary state, not a gap to fill: ship the fix without one, never open a ticket to manufacture a record, and never ask the user whether to. Phase 1's tracker search reads prior work and **never establishes a new home for the bug** — an existing ticket for this bug is one to *link* in Phase 4, never one to create.

**The trivial-bug fast-path** (cause readable from the input, one-line fix, no deep tracing) still runs Phase 2's fix-choice gate before editing: it saves investigation ceremony, not the user's choice over whether to apply a fix.

**Choosing the regression test.** The regression test for a *confirmed defect* belongs wherever existing coverage already owns that behavior: start from the tests that exist rather than from a new file. Read `references/fix.md` for the homes and the naming rule before writing Phase 2's recommendation, not only before Phase 3's edits. A test that fails because the change deliberately reverses the behavior it asserts does not have a wrong expectation — that is the divergent case below, deferred rather than updated.

### Phase 2 gate: present, then ask

**Causal chain gate:** do not proceed to Phase 3 until you can explain the full chain — trigger through every step to the observed symptom — with no gaps. "Somehow X leads to Y" is a gap. Only the user can authorize proceeding on a best-available hypothesis when investigation is stuck.

Once the root cause is confirmed, write the findings as a user-visible block: the causal chain with file:line references; the proposed fix and the files it changes; which tests to use, add, modify, or strengthen, and whether existing tests should have caught this; and any related ticket or PR and how it shapes the recommendation — if an open PR already fixes this, lead with that link instead of a fresh fix.

**Same-turn presentation before the gate:** do not open the fix-choice question until that findings block has been written in full — in this turn or the immediately preceding assistant message. The blocking question tool renders only its own stem on modal harnesses, so a question fired on "root cause confirmed" alone leaves the user choosing with none of the causal chain in front of them. Naming the options is not presenting the findings, and a promise to explain after the choice is too late.

Then ask (per **Blocking questions**) which path to take. Do not assume the user wants action now; the test recommendations are part of the diagnosis either way.

1. **Fix it now** — proceed to Phase 3
2. **Diagnosis only — I'll take it from here** — skip the fix, write Phase 4's summary, end the skill
3. **Rethink the design** (`ce-brainstorm`) — only when the bug cannot be fixed within the current design: the root cause is a wrong responsibility or interface rather than wrong logic, the requirements themselves are wrong, or every candidate fix is a workaround around an assumption that no longer holds. Size alone is not a design problem.

**`mode:pipeline`:** do not ask. Proceed to Phase 3 and apply a **convergent** fix; a **divergent** fix — one that would reverse a deliberate contract/behavior/product decision, including a "failing" test that asserts intended behavior — is deferred, not applied, per `references/pipeline-mode.md`. Never route to `ce-brainstorm` here; a design problem becomes a `needs-human` residual.

### Phase 3: Fix

If the user chose "Diagnosis only," skip to Phase 4's summary. If they chose "Rethink the design," control has transferred to `ce-brainstorm` and this skill ends.

**Read `references/fix.md` before editing any file** — the test-first sequence, the failed-fix rule, and the defense-in-depth and post-mortem triggers. Two rules decide whether the fix may start at all, so they stay here:

- **Working-copy change.** Check `jj status`. If the working-copy revision already contains user changes in files that need modification, confirm before editing. Jujutsu has no current bookmark: when `@` is the trunk revision, start a new empty change with `jj new 'trunk()'` and report its change ID. Do not create or move a bookmark until publication requires one.
- **Record the pre-fix scope:** the change ID and commit ID of `@`, the output of `jj status`, and every pre-existing changed file. Then keep a list of **fix-owned files** (the tests and implementation changed for this bug) as you work. Phase 4 answers both of its questions from this record and cannot reconstruct it afterwards.

### Phase 4: Handoff

**`mode:pipeline` — skip this entire interactive handoff.** No polish/review tail, no residual questions, no preview, no learning-capture offer. Describe and publish the convergent change per `references/pipeline-mode.md`, then emit that reference's **structured return** as the final output. Divergent / needs-human items are deferred there (open thread or the caller's run-report comment — never a PR-body section). The rest of this section is the interactive path only.

**Structured summary** — always write this first:

```
## Debug Summary
**Problem**: [What was broken]
**Root Cause**: [Full causal chain, with file:line references]
**Recommended Tests**: [Tests to add/modify to prevent recurrence, with specific file and assertion guidance]
**Fix**: [What was changed — or "diagnosis only" if Phase 3 was skipped]
**Prevention**: [Test coverage added; defense-in-depth if applicable]
**Confidence**: [High/Medium/Low]
```

**If Phase 3 was skipped**, stop after the summary — the user already said they were taking it from here. Do not prompt.

**If Phase 3 ran, read `references/post-fix-handoff.md` now and follow it before routing below.** It owns this phase's quality tail — the contextual-override checks, the skip-for-mechanical-fixes rule, the scoping that keeps `ce-simplify-code` and `ce-code-review` off unrelated revision content, residual handling, the `## Post-Fix Quality` block, and the learning-capture criteria — and none of that appears in this body. The routing below names *which* action fires, never the scope rules that make it safe, so it cannot be improvised from. Skipping the read ships an unreviewed fix, lets review reach into unrelated revision content, and strands accepted findings in the session.

#### Routing

**Land the fix without carrying along anything the user did not offer up** — not into the described change, a published bookmark, or a PR. Do not ask whether to open a PR; permission is not the gate. Two questions decide the handoff, answered from the pre-fix scope Phase 3 recorded rather than inferred from bookmark state. **Fire the action itself** via the platform's skill-invocation primitive — never merely tell the user to type a command.

**1. What may go into the change — the fix-owned content and nothing else.** This is a constraint on whichever skill describes the change in question 2, never an action of its own. It holds on every route, remote or not. Do not describe or split the change here.

- No fix-owned file carried pre-existing edits: those filesets are the change scope passed to whichever routing skill acts next.
- A fix-owned file already carried the user's edits: first determine whether `jj split` can isolate the fix-owned content without ambiguity. If it can, isolate only that content. If it cannot, ask (per **Blocking questions**) before describing or publishing anything: include the user's overlapping edits, leave the mixed change local and undescribed, or stop. Only the first answer continues; say what was left and why on either other answer. Phase 3's confirmation covered editing the file, never publishing the user's edits with the fix.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local active instructions and syntax observed at runtime always win. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose fixed syntax, examples, or templates. Preserve dynamic tracker tokens and other placeholders required by the active provider.

**2. Who describes the change, and whether it ships.** Exactly one of these runs.

- **Ships** — the pre-fix change was empty, the publication stack contains no work the user has not already offered, and a configured remote is **PR-capable**: `jj git push` can publish a bookmark there and `gh` can open or update its PR. Establish those however fits the workspace. A PR spans every revision between its base and published bookmark, so inspect that revset rather than only `jj diff`; already published revisions count as offered only when they belong to an open PR. If these conditions do not all hold, take the local route. Otherwise preview the fix-owned content, target bookmark, publication revset, and whether a PR opens or updates, then invoke `ce-commit-push-pr` under question 1's scope. Surface the resulting PR URL.
- **Stays local** — any of those conditions fails. Invoke `ce-commit` under question 1's scope and publish no bookmark. Say what stayed local and why, and that you will publish it and open the PR on request. A local Jujutsu operation can be recovered through the operation log, so do not ask first.
- **Not a Jujutsu workspace** — nothing is described or published. Stop after the summary and the quality block.

**Contextual override** ("don't open PRs from skills", "keep the change local", "stop after the fix") — follow what the user said, and **Stop here** without describing or publishing when that is what they asked for. A vague tonal cue is not an override.

**After a PR is open** — apply the reference's learning-capture criteria; if the user accepts, invoke `ce-compound`, include the learning document in the same published change stack, move the PR bookmark to its new tip, and publish it with `jj git push`.

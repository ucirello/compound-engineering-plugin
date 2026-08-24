---
name: ce-debug
description: "Diagnosis loop for bugs and failing behavior. Use when asked to debug or fix failing behavior."
argument-hint: "[issue reference, error message, test path, or description of broken behavior]"
---

# Debug and Fix

Find the root cause of a failure, then, when the user chooses to, fix it with test-first discipline.

**Done when:** the causal chain from trigger to symptom is stated with no gaps and file:line evidence, and either a verified fix has been handed off as a PR or described change, the user chose another stop, or a diagnosis-only summary has been delivered. **Escalate rather than persist:** after 2-3 hypotheses are exhausted without confirmation, or 3 fix attempts fail, diagnose *why* instead of trying again. One hypothesis and one change at a time.

`<bug_description>` is whatever this skill was invoked with — a failure description, a `mode:` token, or an issue reference (`#123`, `org/repo#123`, an issue URL) — from the user or from a calling skill (`ce-babysit-pr` / `lfg` in `mode:pipeline` pass the failing jobs and log tails). Blank if nothing was provided.

At every direct or delegated change-description site: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is non-operational: current `jj log` descriptions and the project's active instructions win; compatible Go guidance governs quality, clarity, and structure only and imposes no fixed prefix, type, scope, subject, body, layout, template, or example. Preserve semantic issue and failure facts, operational model/provider/harness facts, and human authorship data.

## Mode

Default is **interactive**: investigate, run the Phase 2 fix-choice gate, then the Phase 4 handoff.

**`mode:pipeline`** (set by an orchestrator such as `ce-babysit-pr` or `lfg`): run fully non-interactively and never call the blocking-question tool. Strip the token from `<bug_description>`, then **read `references/pipeline-mode.md` and follow it** — it overrides every "ask the user" point with a conservative default, replaces the Phase 2 fix-gate with "fix convergent bugs, defer divergent ones", and replaces the Phase 4 handoff with a structured return whose `status` is exactly one of `fixed-and-pushed | fixed-not-pushed | diagnosed-no-fix | flaky-infra | needs-human`. The caller branches on those exact spellings, so never rename, abbreviate, or add to them.

## Blocking questions

Wherever this skill asks the user something, use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded — a pending schema load is not a reason to fall back), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (needs the `pi-ask-user` extension). Fall back to numbered options on the host's chat surface only when no blocking tool exists or the call errors. Never silently skip the question, and never end a phase without a response.

## Paths

Resolve `<workspace-root>` with `jj workspace root`. If no Jujutsu workspace exists, use the current directory only for local scratch and do not compose durable artifact paths.

Resolve `<root>` only when you first compose a durable `<root>/` path. A run that composes none skips this entirely.

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only. Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value; never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.

Put every invocation-owned scratch file or directory under `<workspace-root>/.tmp/rocketclaw/ce-debug/`. If no Jujutsu workspace exists, use `./.tmp/rocketclaw/ce-debug/`. Never use host-wide temporary storage or global caches.

## Execution Flow

Five phases in order: **0 Triage -> 1 Investigate -> 2 Root Cause -> 3 Fix -> 4 Handoff.** Beyond Phase 0's trivial-bug fast-path there is no skipping and no complexity tiers — a hard bug spends longer in each phase, it does not enter fewer.

**Read `references/investigate.md` now and follow it for Phases 0-2** — issue fetching, reproduction, environment and working-copy isolation, backward tracing, Jujutsu and tracker/PR history, hypothesis grounding, and the escalation table. Only the gates below are stated here.

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

- **Working-copy change.** Check `jj status`. If a file that must change contains pre-existing user work, confirm before editing. Record the current operation ID, workspace name and root, `@` change ID and commit ID, bookmarks at `@`, and `@`'s changed files. If `@` is empty and mutable, it may hold the fix. If `@` is `trunk()`, immutable, or already represents completed work, create a dedicated child change with `jj new @`. A bookmark is a publication pointer, not a current branch; create or move one only when the fix is ready to publish.
- **Record the pre-fix scope:** whether `@` had changes, every pre-existing changed file, and the offered stack selected by the revset from its remote base through `@`. Then keep a list of **fix-owned files** as you work. Phase 4 answers its scope and publication questions from this record and cannot reconstruct it afterwards.

### Phase 4: Handoff

**`mode:pipeline` — skip this entire interactive handoff.** No polish/review tail, no residual questions, no preview, no learning-capture offer. Describe and push the convergent fix per `references/pipeline-mode.md`, then emit that reference's **structured return** as the final output. Divergent / needs-human items are deferred there (open thread or the caller's run-report comment — never a PR-body section). The rest of this section is the interactive path only.

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

**If Phase 3 ran, read `references/post-fix-handoff.md` now and follow it before routing below.** It owns this phase's quality tail — the contextual-override checks, the skip-for-mechanical-fixes rule, the scoping that keeps `ce-simplify-code` and `ce-code-review` off unrelated change-stack work, residual handling, the `## Post-Fix Quality` block, and the learning-capture criteria — and none of that appears in this body. The routing below names *which* action fires, never the scope rules that make it safe, so it cannot be improvised from. Skipping the read ships an unreviewed fix, lets review reach into unrelated changes, and strands accepted findings in the session.

#### Routing

**Land the fix without carrying along anything the user did not offer up** — not into a described change, bookmark push, or PR. Do not ask whether to open a PR; permission is not the gate. Two questions decide the handoff, answered from the pre-fix scope Phase 3 recorded rather than inferred from the current bookmark. **Fire the action itself** via the platform's skill-invocation primitive — never merely tell the user to type a command.

**1. What may go into the described change — the fix-owned files and nothing else.** This constrains whichever skill finalizes in question 2; it is not an action of its own. It holds on every route. Do not finalize here.

- No fix-owned file carried pre-existing edits: pass those files as the finalization scope.
- A fix-owned file already carried the user's edits: `ce-commit` groups at file level and cannot separate their hunks from the fix. Ask (per **Blocking questions**) *before* finalization whether to include that whole file, leave the fix in the working-copy change, or stop. Only inclusion continues. Phase 3's confirmation covered editing, not describing the user's work as part of this fix.

**2. Who finalizes, and whether it ships.** Exactly one of these runs.

- **Ships** — the pre-fix working-copy change had no edits, every revision in the publication bookmark's stack is offered work, and there is exactly one writable, PR-capable publication remote. Resolve that remote by reconciling the bookmark's tracked remote bookmarks with the provider repository that will own the PR; never default to `origin`. If those signals identify multiple remotes or disagree, stop without finalizing or publishing and report the ambiguity. Establish the stack with a revset against the fetched publication-remote bookmark, not by assuming a bookmark is current or that local and remote pointers match. Two facts make this less obvious than it looks.
  - `ce-commit-push-pr` publishes the **whole bookmark stack**, and the PR spans every revision from the remote base through the bookmark target, not just the fix. It pushes before creating the PR, so a remote that `gh` cannot use leaves the bookmark published with no PR.
  - Already pushed is not already **offered**. Revisions in an open PR are offered and this run updates that PR; revisions pushed only for backup or CI are not. Fetch `<publication-remote>`, compare the local bookmark with `<bookmark>@<publication-remote>`, and inspect the exact stack with a revset such as `<bookmark>@<publication-remote>..<bookmark>`.

  If no suitable publication remote exists or another ship condition fails, take the local route. Otherwise preview the fix-owned files, bookmark stack, publication remote, and whether the PR opens or updates, then invoke `ce-commit-push-pr` under question 1's scope; do not finalize first. Surface the resulting PR URL.
- **Stays local** — no suitable publication remote exists or a non-ambiguity ship condition fails. Invoke `ce-commit` under question 1's scope and push nothing. Say what stayed local and why. Jujutsu's operation log provides recovery, but it does not make publishing unoffered work safe.
- **Not a Jujutsu workspace** — nothing is finalized. Stop after the summary and quality block.

**Contextual override** ("don't open PRs from skills", "keep it local", "stop after the fix") — follow what the user said, and **Stop here** without finalizing when that is what they asked for. A vague tonal cue is not an override.

**After a PR is open** — apply the reference's learning-capture criteria; if the user accepts, invoke `ce-compound`, then include the learning document in a described change on the same bookmark and push so the open PR picks it up.

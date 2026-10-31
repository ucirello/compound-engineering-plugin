---
name: ce-compound
description: Document a solved problem as a durable repo learning. Use when verified work produced non-obvious reasoning absent from its final code, tests, or existing docs; avoid routine fixes whose artifacts already explain the lesson.
argument-hint: "[optional: brief context] [mode:non-interactive] [depth:lightweight|full]"
---

# /ce-compound

**Outcome:** one qualifying solved problem is written as a durable learning under `<root>/solutions/`, grounded against the current tree, discoverable by the next agent.

**Done:** a qualifying doc is written or updated, its frontmatter and claims validated, vocabulary capture recorded, and the mode's completion report emitted; when no learning qualifies, nothing is written and the report says why.

**One learning per run.** A session that produced several gets several sequential runs, never one batched run. Read `references/research.md`; it explains what batching breaks.


## Preconditions

Document only a problem that is solved and verified.

<!-- ce-durable-bar:start -->
A learning earns its place only when it holds durable project reasoning that is not readily recoverable from the final code, tests, types, comments, or existing documentation, and losing it would plausibly cause recurrence, material risk, or substantial rediscovery. Apply this counterfactual: if the learning document disappeared, would a future engineer reading the final implementation still be likely to repeat the mistake or redo substantial investigation? Completion, effort, and diff size do not establish eligibility.
<!-- ce-durable-bar:end -->

If the counterfactual fails, write nothing and report why. Judge this from the session rather than asking. An explicit invocation requests the judgment now but does not lower the bar.

An existing learning that became materially inaccurate or incomplete qualifies because leaving it would mislead. Update that learning instead of creating a duplicate.

`ce-compound` does not bootstrap `CONCEPTS.md`. It seeds the learning's own area as a side effect, never the whole repo. Send a standalone request to create or bootstrap that file to `ce-compound-refresh`, then exit.

## Mode Detection

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

Enter non-interactive mode when **either** holds: the arguments you were invoked with contain the `mode:non-interactive` token or its deprecated alias `mode:headless`, **or** the invocation makes non-interactive intent unmistakable, such as a caller or standing instruction asking to run `ce-compound` "headless", "non-interactively", "unattended", or "without prompts/questions". Both tokens together is not a conflict. Bare "automatically" or "auto-run" is **not** on its own a non-interactive signal: it speaks to *invoking* the skill, not to suppressing its prompts. An ambiguous or absent signal defaults to interactive. Tokens starting with `mode:` or `depth:` are flags, not context: strip them before treating the remainder as the brief context hint. Once detected, non-interactive mode applies for the entire run.

Depth is chosen only by an explicit token, only in non-interactive mode, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

**Non-interactive mode asks nothing.** It asks no blocking question of any kind, in any phase, because a caller reaching this path has no human to answer one. Every non-interactive exit, including one taken before any phase runs, ends on a terminal signal a caller parses: `Documentation complete`, or `Documentation skipped` with the reason when no doc was written. Interactive mode asks only where the step's own reference says to, which is the Discoverability Check consent and, when several stale docs are in play, which refresh to run.

## Artifact Root

Resolve `<root>` when you first compose a `<root>/solutions/` path, and pass a subagent the resolved path rather than the config.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` is the absolute enclosing JJ workspace root containing `.jj`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Write boundary

In a context-pressure handoff the fresh Full delegate becomes the orchestrator. After it finishes, the interactive parent may apply the expressly consented discoverability edit or settle the eligible pack destination, without re-running Full or editorially reworking the learning. Destination changes must preserve one learning rather than create duplicate artifacts. These are the only handoff exceptions to the ordinary mode-specific boundaries below.

**Only the orchestrator writes product files.** Phase 1 subagents write to per-run scratch only, and never touch `<root>/`, project instruction files, or any other tracked path.

The orchestrator writes the one learning under `<root>/solutions/`, plus two maintenance side effects that its own step describes: `CONCEPTS.md` during vocabulary capture, and — **only in interactive Full mode after consent** — a small discoverability line in a project instruction file. Two further writes exist **only in interactive Full mode when the user selects them at the assembly destination step**: a rule file inside a writable declared Compound Pack, and the `packs:` entry appended to `.rocketclaw/config.yaml`. Creating `CONCEPTS.md` when it is absent is expected rather than a violation. An instruction file is only ever edited, never created. Nothing else in the tree is written. Edits to *other* docs belong to `ce-compound-refresh`, which this skill recommends or invokes with a narrow scope but never stands in for.

## Choosing the path

**Read `references/modes.md` before step 1.** Default to **Full**. Under interactive context pressure, delegate Full using the handoff below rather than choosing Lightweight. Explicit non-interactive depth tokens retain their meaning.

### Context-pressure Full handoff

Read the source ID with shell `printf '%s\n' "$OPENCODE_SESSION_ID"`; never guess it. Pass that ID, the known title (or explicitly unknown), absolute JJ workspace root, existing learning doc path (or none), and one-sentence topic to ONE fresh native subagent loading `ce-compound mode:non-interactive depth:full`. Do not pass a predigested conversation. This explicit dispatch authorizes delegation subject to unconditional tool/permission prohibitions. Discover effective depth using supported configuration discovery; deep delegation requires `experimental.subagent_depth >=3`. Setup must merge that value into the existing `opencode.json(c)` discovered with `opencode debug paths` / `opencode debug paths config`, preserving sibling fields and higher integers; never modify host configuration during this run or create a competing file. Package-local configuration alone is insufficient.

The delegate is the Full orchestrator and may write the single learning and normal Full side effects; its research children remain scratch-only. Before reading source evidence it exports the supplied source through `opencode session export ID` or `opencode api get /api/session/ID/message`, saves under the supplied workspace's `.tmp/`, and reduces it to user/assistant text plus tool names and short results (no reasoning, secrets, or internal database access). The supplied source is primary evidence, not an excluded current session. Exclude only the delegate's own session.

Parent relays the delegate's report and doc path without a second Full run or re-edit. Offer consent-based interactive discoverability editing and, for eligible prescriptive captures, a writable Compound Pack destination; avoid duplicate learning artifacts. Lightweight fallback is permitted only after an actual unavailable-tool, permission, or depth failure, classified from its error. Model rejection and capacity failures are distinct; do not evade denial through shell/another harness. Report reduced coverage and advise rerunning in the same source session once delegation is available.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

## Full Mode

Run these in order. Each reference is a required read at the step that names it.

1. **Research** — read `references/research.md`.
2. **Session history** — read `references/session-history.md`, and start it *after* dispatching the Related Docs Finder so it overlaps your drafting rather than serializing. Session history is the final Phase 1 input, not a workflow stop. When it returns, including with "no relevant prior sessions", go straight to assembly without pausing or summarizing.
3. **Assembly and write** — wait for every Phase 1 input, then read `references/assembly.md`.
4. **Refresh check and discoverability** — read `references/refresh-and-discoverability.md`.
5. **Optional enhancement** — read `references/enhancement.md`. Interactive only.
6. **Report** — read `references/report.md` for the report shape your mode must emit and how the skill ends.

**Lightweight Mode** replaces steps 1-6 with a single pass; read `references/lightweight.md`, which defines its own completion output for both modes.

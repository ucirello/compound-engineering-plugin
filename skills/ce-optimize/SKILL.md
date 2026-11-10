---
name: ce-optimize
description: "Optimize a named target with a measured loop: attribute a workload's cost, or score variants and keep winners. Use when a working system's metric should move and the winning change is not already known. Use ce-debug when the job is diagnosis; use ce-work when the change is already known."
argument-hint: "[path to optimization spec YAML, or describe the optimization goal]"
---

# Optimize a measurable target

**Outcome:** confirmed improvements to the named target live on an `optimize/<spec-name>` branch, with a disk log. The user takes over at wrap-up.

**Intent:** the next action is the cheapest step that would change what gets implemented. Attribute the cost of a named workload before searching implementations. Search and keep a scored variant space without requiring a profile.

**Done when:** a stopping criterion was met, every declared required target is met or another stop was met first, the final state is written and verified on disk, and the user has been given the post-completion options. If the run instead stopped at a check it could not pass, say what blocked it.

Invoking this skill authorizes reading the repo, building the harness, native subagent delegation, and (after the Phase 1 approval gate) isolated experiments and keep/revert revisions on `optimize/<spec-name>`. Read `references/workspaces.md` before any repository/workspace operation; it governs every phase, including callers and cleanup. Ask when spend is uncapped, when a new dependency appears, when wrap-up would push or open a PR, or when only the user can choose among the post-completion options. Do not ask again to run the next experiment inside those limits.

**Delegation.** Use native OpenCode subagents and `opencode.models` to resolve configured choices, authoritative within host permissions. Delegation permission is separate from model-override permission. Inherit the current model when suitable; disclose missing required cross-model coverage. Queue capacity-limited work. Depth exhaustion, permission denial, missing tools, and model-argument rejection are distinct blockers; never evade them through shell or another harness. Explicitly migrate legacy external backend selections to permitted native subagents with equivalent isolation/receipts or report unsupported.

**Description composition, all phases.** Read the full https://go.dev/wiki/CommitMessage at runtime and recent full subjects/bodies from the actual verified history head: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"')`. Compare several examples; actual repository syntax wins over Go guidance. Do not impose conventional-message templates. Explain the measured hypothesis and evidence accurately and preserve valid issue references; no attribution or Signed-off-by trailers. Use `jj describe -r <verified-revision> -m '<repository-appropriate description>'` after composition for experiment, result, integration and report revisions.

Set `workspace_root` to the verified absolute target workspace root and replace the history-head placeholder with the inspected actual revision before executing the history read. Read this full composition section before composing in any phase.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Verbatim source guidance, subordinate to actual repository syntax and not a mandatory template:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

Verbatim source excerpts (guidance, not a repository template):

> The CL description is a public document that explains to the future what has been done and why.
>
> the verb after the colon is lowercase
>
> there is no trailing period
>
> there is **no** Markdown in the commit message.
>
> similarly, we **do not** use `Co-authored-by` and `Assisted-by` lines. Don’t add them.

The source example below is **Go source guidance only**; repository history controls actual syntax:

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

Independent calls and dispatches go in one response; serialize only real dependencies.

Report findings, user decisions, blockers, and results. During longer work, give occasional updates on what was learned and what remains. Routine preparation and phase or batch transitions need no announcement. Keep accounting in the log and final recap unless it affects a current decision.

Explain the target, evidence, and decision in ordinary task language. Workflow labels (such as 'harness') belong in artifacts unless the user asks about those mechanics. State unknown duration or cost as unknown; caps are limits, not forecasts.

A step is done only after it ran. Describing a measurement, dispatch, or checkpoint is not doing it. Do not end a turn while in-scope work remains merely described. Outstanding work may outlive the turn only with a verified checkpoint and either bounded automatic resumption or an explicit manual-resume handback, as `references/persistence.md` defines.

## Interaction Method

Use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability: do not search for another host's tool name. Fall back to numbered options on the host's chat surface only when no such tool is in the list or a real question call errors. Never skip the question silently.

## Execution Surface

Three capabilities decide how run state is referenced across turns, how the loop waits, and where experiments run. A **durable state root** is a writable location the harness names that persists across turns and context resets; it may retain a reference or receipt for the run, but new run state and scratch live under `$(jj workspace root)/.tmp/ce-optimize/<spec-name>/`, never OS-global temporary storage. Reuse an existing run's ledger at its recorded location without moving it automatically (`references/persistence.md`). A **wake after turn end** is a way to be re-invoked by an external event or timer without holding a tool call open; without one, the loop runs inside this session, and a wait it cannot hold ends the turn as a checkpoint with a resume invocation. A **detached worker** is a dispatch whose result arrives as a pushed ref, a store file, or a host-delivered message, not as edits in the local tree; `execution.backend: remote` needs one; without one that spec runs on `worktree`. Presence in the current tool list, or in context the harness gave you, is proof; a missing binary or environment variable proves nothing. Take a fallback without asking.

## Artifact Root

<!-- ce-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.opencode/config.yaml` only (`<repo-root>` = `jj root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Persistence Discipline

The experiment log on disk is the source of truth. Write order is measure, write, verify, then show the user. **Read `references/persistence.md` now** for checkpoints CP-0 through CP-5, the state root layout, and resume.

## The phases

Four phases run in order; each names the reference it cannot start without. A fresh run skips none: a harder optimization spends longer in a phase, not fewer phases.

**A resume is not a fresh run.** On a resume, re-enter Phase 0 only far enough to detect the run and to recover any `result.yaml` markers the log is missing. Then continue from the phase the log records and skip the work it proves finished. A checkpoint proves the work that produced it; a user decision counts only while the log records it. The Phase 1 approval record is bound to the spec digest and the caps it approved; present that gate again when it is absent or no longer matches.

**Phase 0: Setup.** The input is a goal or a spec YAML path, from the user or a calling skill. **Read `references/spec.md`**: it asks for the input when neither supplied one, then loads or builds the spec to save (CP-0). **Read `references/measurement.md`** for the rest of Phase 0 and Phase 1.

**Phase 1: Measurement scaffolding.** Build or validate the harness, write the baseline (CP-1), probe parallelism, check the worktree budget. Two gates stop the run:

- **Clean-tree gate.** Do not continue while any file in `scope.mutable` or `scope.immutable` has uncommitted changes. The reference defines the check and what to ask for.
- **User approval gate.** Present what Phase 1 assembled and offer proceed, fix issues, and adjust spec; the reference lists what to include. Disclose which spend is capped and which is uncapped. **Do not enter Phase 2 until the user explicitly approves.** Then record the approval and re-read the spec and baseline from disk.

**Phase 2: Hypothesis generation.** Analyze the current approach, rank the hypotheses, record the backlog (CP-2). Do not dispatch an implementation experiment while a cheaper locating measurement would change keep or skip. **Read `references/loop.md`** for this phase and Phase 3. One gate: **dependency pre-approval** of every new dependency across all hypotheses, as one bulk list.

**Phase 3: Optimization loop.** Follow the tick protocol in `references/loop.md`, including per-result persistence and batch checkpoints. Stop as soon as any one of eight criteria holds: every declared required target is met, max iterations, max active hours, the wall-clock backstop, a spend cap reached, plateau, a user interrupt, or no runnable hypothesis left. `references/loop.md` states each one exactly. Otherwise start the next tick.

**Phase 4: Wrap-up.** **Read `references/wrap-up.md`** for the summary and the post-completion options to present. CP-5 marks the log final. **Write it only after the user picks an option that does not return to Phase 3.** Two options do return: Continue, and approving a deferred dependency.

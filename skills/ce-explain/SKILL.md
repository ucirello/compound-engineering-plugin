---
name: ce-explain
description: "Create a durable, visual teaching artifact — plus an optional check-in (predict-then-reveal for diffs, corrected exercises) that makes it stick — for something worth learning: a concept, a diff, an idea, or a window of your own recent work. Use when the user wants to be taught, wants a deep explainer, wants to understand a substantial change, or wants a work recap built for retention. Not for ordinary Q&A, brief 'why?' follow-ups, operational diagnosis, status updates, or a concise trade-off answer that belongs inline in chat. For learning, not repo docs or verdicts."
argument-hint: "[a concept, a diff ref, an idea, or 'what happened this week?'] — or invoke bare to be asked"
---

# Explain It To Me

Teach the user one thing well: a concept, a change, an idea, or a window of their own recent work. Agent-driven development removed the learning that writing code by hand used to provide; this skill is the replacement — the human keeps learning while agents do the writing.

What to explain is the input this skill was invoked with, present in the current prompt or conversation (whether the user asked directly or a calling skill passed it).

**Note: The current year is 2026.** Use this when weighting external sources and dating artifacts.

## Setup

Run this once at the start of this invocation, before any subagent dispatch, and follow the directives it prints — except where one conflicts with this skill's own rules on asking the user questions, whether those rules are scoped to a non-interactive mode or apply in every mode, in which case this skill's rules win and no blocking question is asked. Run the fence exactly as written, as its own command: do not pipe or filter it (no `head`, `tail`, or `grep`), do not truncate its output, and do not bundle it into a batch with other commands. Its output opens with a `=== skill context` header and ends with `SKILL_CONTEXT_END`; if you received one of those lines without the other, the output was truncated — rerun the fence verbatim once. That recovery is the only rerun: otherwise do not rerun it within the same invocation; a later invocation of this or any other skill runs its own. If no Node runtime is available the skill proceeds unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
"$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
echo "no Node runtime; continue with the skill's normal behavior";
fi
```

## Who the explainer is for

**Default — the user personally.** Dense, technical, one voice, second person, free to assume the context they already carry.

**On request — rendered for another reader.** When the user asks for a version someone else will read ("write this for my team", "this is going into the design review", "a share-out"), adapt voice and orientation, never depth: drop second person; name the subject in third person when the evidence supplies a name (recap mode's change authors) or the user supplies one, and stay impersonal when neither does; add the minimum orientation a reader outside the user's head needs to follow it. Density, real code, and the honesty labels are unchanged. It stays the same document rendered for someone else — never softened into a status update, never a deck.

The artifact is display-only in both renderings: no embedded quizzes, forms, or widgets — the doing happens in the session, where answers can be checked.

## Interaction Method

When you must ask the user a question, use the platform's blocking question capability. Fall back to numbered options on the host's user-visible chat surface only when no blocking capability exists or its call errors. In the fallback, stop and wait for the user's reply. Never silently skip the question. Ask one question at a time.

## Model Tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the work-recap scout: search-and-quote work. Use the platform's cheapest capable model when the harness exposes a known override; otherwise inherit.
- **Ceiling tier** — the explainer composition, the check-in reasoning, and the corrections. These run in the main conversation on the orchestrator's model; nothing is dispatched for them.

**Degradation rule.** When the platform's subagent primitive cannot select per-agent models, dispatch scouts on the inherited model and keep their read budgets. When the platform has no subagent primitive at all, run the scout work inline with the same budgets. When a dispatch fails, treat a concurrency or active-agent-limit error as backpressure — retry after a slot frees; a launch that fails for a reason that survives correcting the invocation runs that scout's work inline with the same budgets, disclosed in one line.

## Artifact Root

This skill writes an explainer under `<root>/explainers/` only when it archives one to the workspace, and may read learnings under `<root>/solutions/`. Resolve `<root>` only when you actually compose such a path. A run-local or external-concept explainer writes to its run directory and never needs it, so do not resolve or create a root at the start of every run. Pass the resolved path to any subagent when you do resolve it, not the config.

<!-- artifact-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml`, where `<workspace-root>` is `jj workspace root`. A set value resolves as `<workspace-root>/<docs_root>`; unset -> `<root>` is `<workspace-root>/.context`.
- **Validate** a set value as workspace-relative: its real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or `.tmp/`. Otherwise stop with an error naming `docs_root` and the value; never fall back to `.context`.
- **Use** `<root>` as the sole durable artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read another artifact root.
<!-- artifact-root:end -->

## Execution Flow

### Phase 1: Classify the input

Read `references/intake.md` now and classify the request into one of the four input shapes — concept, diff, idea, or work-recap window, plus its audience. It owns the token table (`diff:`, `since:`, `output:`, `audience:`), the reads-as-a-flag guard that keeps ordinary prose containing a colon from being parsed as a token, window resolution, audience resolution, the concept-vs-diff tiebreak, and conflict handling. Most requests arrive as plain language with no token; classify those by meaning. Do not improvise classification.

**Bare invocation** (no input at all): ask one blocking question — "What should I explain?" — offering a shortcut option for a recap of recent work in this repo alongside free-text. Do not produce a default artifact unprompted.

**Operational-question gate.** Not every *concept by inference* wants the teaching flow this skill runs — many just want a direct answer. When such a request (no `diff:`/`since:` token, no wording that plainly asks to learn or build like "teach me how X works") reads as one better answered in chat — e.g. diagnosing or operating current behavior ("why is X doing Y", "is X configured right") — answer it directly. Then offer to teach it only when a real underlying concept sits behind the question that the user would plausibly want to learn — not as a reflexive add-on to every answer — phrased plainly, e.g. "Want me to actually walk you through how this works? I can build you a visual explainer to keep." Create the run directory and profile the repo only if they take it. A request that plainly wants to learn, or that carries a build signal, skips the gate and is taught in full.

### Phase 2: Ground

Match grounding to the input shape. Create the run directory first — every run gets one, before any artifact exists:

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)";
if [ -z "$WORKSPACE_ROOT" ]; then WORKSPACE_ROOT="$(pwd -P)"; fi;
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
RUN_DIR="$SCRATCH_ROOT/explain/$(date +%Y%m%d)-$(openssl rand -hex 3)";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR";
```

**Repo-touching inputs** (a concept with footprint in this workspace, a diff, a recap): use the project's active instructions and canonical vocabulary already in context and go directly to the diff, call-sites, current source, or changes. If the topic cannot be scoped from the input and existing context, allow one targeted workspace probe.

- **Diff mode:** resolve the change (the `diff:` revision or revset, or the most recent substantial change when the request points at one implicitly) and gather its evidence with `jj diff`, `jj show`, and `jj log` — the diff itself, the files it touches, and any plan or solution doc that motivated it. Gather silently: nothing learned here is narrated to the user until Phase 3's ordering rule is satisfied. **Empty selection** (the revision or revset resolves to no changes, including when work remains in `@` outside the requested selection): do not silently explain something else. Say what it resolved to, name the nearest real candidate (`@` or the preceding change), and use it only after the user agrees — or, when they cannot be asked, use it and state the substitution in the artifact's `Subject`. Apply the same rule when the named subject does not exist in this workspace at all ("the retry logic" where there is none): report that before explaining an adjacent thing.
- **Recap mode:** dispatch a generic subagent directly, seeded with `references/agents/work-recap-scout.md` (extraction tier), passing the resolved window, the workspace root, and `$RUN_DIR`. Do not pre-scan, count, or characterize the window in the main conversation; the scout owns that evidence pass, and an early all-revisions summary can seed it with a false bookmark or activity model. **When the harness exposes no subagent primitive**, the degradation rule above applies: run the scout inline against its own prompt's sources and budgets, and still write `recap-evidence.md`. The no-pre-scan rule then means what it protects rather than where it runs — do the scout's evidence pass first and form no view of the window until it is done. It returns an evidence summary with change IDs and `file:line` pointers. **Empty window** (no change activity and no document changes): say so, offer to widen the window, write no artifact, and end the run after the user responds.
- **External concepts** (no footprint in this workspace): skip workspace grounding entirely — do not force local context into the output. Research with whatever web tools are reachable. When none are, you may explain from model knowledge, but the artifact must label that content **Unverified — from model knowledge, not checked against current sources** in its metadata header.
- **Idea mode:** the idea is a fixed given. Explain its implications, mechanics, and trade-offs for the user's understanding. Never scope it (`ce-brainstorm`'s job), never generate and rank alternatives (`ce-ideate`'s job).

### Phase 3: Check-in gate — before anything is revealed

Judge whether the material warrants a check-in (a routine recap does not; a gnarly diff or a hard concept does), then offer it with the blocking question tool. **In diff mode, word the offer without describing the change's content or purpose** — an offer that summarizes the change pre-leaks the reveal before the prediction is taken. Put **Just the explainer (Recommended)** first and **Quiz me** second; the common path is the report, not the exercise loop. Record the user's exact Phase 3 choice as **Just the explainer** or **Quiz me** — do not collapse both choices into an "accepted" boolean. Only **Quiz me** enables the prediction and exercise mechanics. **Just the explainer** skips both while still composing and presenting the report. If the warrant test skips the offer, proceed without either mechanic. The user can always decline, and declining is never re-litigated. Read `references/check-in.md` for the warrant test, the prediction protocol, and exercise design.

**Diff mode with Quiz me selected — hard ordering rule.** No interpretive content — explanation, annotation, diagram, or surfaced opportunity — may be shown before the user's prediction turn ends. Show only the raw change reference (the diff or its stat summary), ask for the prediction ("What do you think this change does, and why was it made?"), and **end the turn there**. When no blocking tool exists, ask in chat and stop — never print the reveal in the same message as the prediction prompt. Compose the explainer only after the prediction lands; the reveal names the gaps between the prediction and what the change actually does.

### Phase 4: Compose the explainer

Read the rendering reference for the resolved format **now**, not earlier: `references/explainer-html.md` (default) or `references/explainer-markdown.md` (when intake resolved `output:md`). Compose per its contract — visible metadata header, show-n-tell form matched to the material, ~70ch measure, single self-contained file — and write the artifact to `$RUN_DIR/explainer.html` (or `$RUN_DIR/explainer.md` when intake resolved `output:md`) before anything else happens with it. Display it to the user (inline summary plus the file path; open locally per Phase 6 when chosen). The artifact exists at that stable path from this moment — a declined destination ask never loses it.

### Phase 5: Exercises (only when Quiz me was selected)

Run this phase only when the recorded exact Phase 3 choice was **Quiz me**. For concepts, ideas, and dense recaps, pose the exercises from `references/check-in.md` in chat, one at a time, using the blocking question tool where its option shape fits and free chat where the answer is narrative. Check each answer, correct it, and name the gap it exposed. Do not put exercises inside the artifact. When the choice was **Just the explainer**, skip this phase and continue to the destination ask.

### Phase 6: Destination ask and close

Detect destinations by capability — probe the agent's own toolset and session context, and never treat a missing binary, environment variable, or unloaded connector as proof a destination is unavailable when another interface could supply it. Local file and Leave it are ungated and always offered. For default HTML runs, offer one preferred publisher: Claude Artifact when running in Claude Code with its Artifact tool present; otherwise ht-ml.app. Do not show both by default, but honor an explicit user request for either. Publishing always requires the user's destination choice; ht-ml.app is public and must never be selected headlessly. Detect Thinkroom through a session skill, reachable MCP tool, or documented CLI that responds. Ask for the destination once with the blocking question capability. That choice governs the menu itself, not any separate consent the selected destination requires. If the visible set exceeds the question capability's option cap, render a numbered list in chat with "Pick a number or describe what you want." and wait instead. Per-option routing:

- **Claude Artifact** (HTML only; preferred in Claude Code when its Artifact tool is present) — create it from the canonical explainer per `references/destinations.md`, following the Artifact tool's current contract.
- **Publish publicly to ht-ml.app** (HTML only; preferred when Claude Artifact is not the selected adapter) — label it Recommended and state in the option description that the page is public and may be indexed, crawled, copied, or archived. When an explicit publish request bypasses the menu, state that full warning in chat and obtain explicit confirmation after the warning before the call; the pre-warning request does not count as confirmation. If confirmation cannot be obtained, do not publish; preserve the canonical HTML and report its local `$RUN_DIR/explainer.html` path. On a warned menu selection or post-warning confirmation, follow the ht-ml.app sub-flow in `references/destinations.md`, passing the complete canonical HTML to the resolved publisher. Do not assume a particular skill exists or add a ce-explain-specific publisher.
- **Local file** — copy the artifact out of `$RUN_DIR` to the path the user names, then where the platform exposes a browser-opening primitive (`open` on macOS, `xdg-open` on Linux, `start` on Windows) offer to open it; otherwise print the absolute path.
- **Send to Thinkroom** — offered only when a Thinkroom skill, MCP tool, or documented CLI capability is detected; send per `references/destinations.md` and surface the returned reference.
- **Leave it** — report the `$RUN_DIR` path and state that it remains in the workspace-local `.tmp` area until local cleanup removes it; nothing else is written.

**Audience mismatch.** When the artifact was composed in the personal default and the user selects a destination that puts it in front of other people, offer once to re-render it for that audience per the compose-time reference before sending. A private artifact does not trigger this offer because it stays private until the user shares it. Take their answer and proceed either way; never re-render unasked, and never block the send on it.

**This offer comes first**, before any publish warning or confirmation the destination requires — consent must attach to the artifact actually being published, and the adapted rendering differs materially (it names a person where the personal one says "you"). Ask one question at a time: settle the rendering, then run the destination's own consent gate. When the destination needs no confirmation, this is the only ask.

**Non-interactive degradation:** when no interaction is possible at this ask (no blocking tool and no reply), do not hang and do not discard — the artifact is already at `$RUN_DIR`; report that path and end, skipping the improvement-observation handoffs below (they are offers, and an offer cannot fire without a user).

**Improvement observations.** When composing the explainer surfaced things that could be better, route them by type once the destination is settled — offer, don't auto-fire. "Settled" means the artifact was sent, or the user declined, or the run stopped at a consent gate they didn't answer; in that last case the run ends there and these offers are skipped, like the non-interactive case above. Never raise them while any of the asks above is still open — the destination question, the audience re-render offer, or a publisher's consent gate.

**User-runnable invocation rendering.** Only the user-run handoff below uses printed invocation syntax. Use the active harness's documented user-invocation form for `ce-polish`. Render only the invocation as inline code and output one form only.

- **New-capability ideas** — offer first; on acceptance invoke the `ce-ideate` skill via the platform's skill-invocation primitive, passing the observations as seed context. Do not merely tell the user to run it.
- **Code-clarity findings** — offer first; on acceptance invoke the `ce-simplify-code` skill via the platform's skill-invocation primitive, passing the observations and the files they concern. Do not merely tell the user to run it.
- **UI/UX polish opportunities** — present the observations in chat and tell the user to invoke `ce-polish` themselves using the rendering rule above; `ce-polish` is user-invoked only (`disable-model-invocation`), so never attempt to invoke it via the skill primitive. The in-session observations carry into their run.
- **A repo doc the evidence contradicts** — grounding reads plans and solution docs, so a recap or diff routinely surfaces one that is now stale, superseded, or contradicted by what shipped. Offer first; on acceptance invoke the `ce-compound-refresh` skill via the platform's skill-invocation primitive, naming the doc and the evidence that supersedes it. Do not edit the doc from this run — this skill teaches, it does not maintain repo memory.

## Boundaries

- **Not a verdict.** "Should we adopt X?" is `ce-pov`. This skill teaches what X is and how it works.
- **Not repo memory.** Documenting a solved problem for future work is `ce-compound`. This skill teaches the human, not the repo.
- **Not ideation or scoping.** An idea input is explained as given — implications and trade-offs — never expanded into options or a requirements dialogue.
- **The check-in is never headless.** It exists to exercise the human; automating the answers deletes the product.

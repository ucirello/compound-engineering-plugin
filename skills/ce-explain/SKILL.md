---
name: ce-explain
description: "Create a durable, visual teaching artifact — plus an optional check-in (predict-then-reveal for diffs, corrected exercises) that makes it stick — for something worth learning: a concept, a Jujutsu change, an idea, or a window of your own recent work. Use when the user wants to be taught, wants a deep explainer, wants to understand a substantial change, or wants a work recap built for retention. Not for ordinary Q&A, brief 'why?' follow-ups, operational diagnosis, status updates, or a concise trade-off answer that belongs inline in chat. For learning, not repo docs or verdicts."
argument-hint: "[a concept, a diff ref, an idea, or 'what happened this week?'] — or invoke bare to be asked"
---

# RocketClaw Explain It To Me

Teach the user one thing well: a concept, a change, an idea, or a window of their own recent work. Assistant-driven development removed the learning that writing code by hand used to provide; this skill is the replacement — the human keeps learning while assistants do the writing.

What to explain is the input this skill was invoked with, present in the current prompt or conversation (whether the user asked directly or a calling skill passed it).

**Note: The current year is 2026.** Use this when weighting external sources and dating artifacts.

## Who the explainer is for

The user personally — dense, technical, one voice, no audience adaptation. Meeting prep preps the user; it never produces the deck. The artifact is display-only: no embedded quizzes, forms, or widgets — the doing happens in the session, where answers can be checked.

## Interaction Method

When you must ask the user a question, use the runtime's blocking question capability. Fall back to numbered options in chat only when no blocking capability exists or the call errors. In the fallback, stop and wait for the user's reply. Never silently skip the question. Ask one question at a time.

Dispatch the work-recap scout through the runtime's generic subagent capability when available. Otherwise run the same bounded evidence pass inline.

## Execution Flow

### Phase 1: Classify the input

Read `references/intake.md` now and classify the request into one of the four input shapes — concept, diff, idea, or work-recap window. It owns the token table (`diff:`, `since:`, `output:`), the explicit-token-beats-inference rule, the concept-vs-diff tiebreak, and conflict handling. Do not improvise classification.

**Bare invocation** (no input at all): ask one blocking question — "What should I explain?" — offering a shortcut option for a recap of recent work in this repo alongside free-text. Do not produce a default artifact unprompted.

**Operational-question gate.** Not every *concept by inference* wants the teaching flow this skill runs — many just want a direct answer. When such a request (no `diff:`/`since:` token, no wording that plainly asks to learn or build like "teach me how X works") reads as one better answered in chat — e.g. diagnosing or operating current behavior ("why is X doing Y", "is X configured right") — answer it directly. Then offer to teach it only when a real underlying concept sits behind the question that the user would plausibly want to learn — not as a reflexive add-on to every answer — phrased plainly, e.g. "Want me to actually walk you through how this works? I can build you a visual explainer to keep." Create the run directory and profile the repo only if they take it. A request that plainly wants to learn, or that carries a build signal, skips the gate and is taught in full.

### Phase 2: Ground

Match grounding to the input shape. Create the run directory first — every run gets one, before any artifact exists:

```bash
if WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" && [ -n "$WORKSPACE_ROOT" ]; then :; else WORKSPACE_ROOT="$(pwd -P)"; fi;
SCRATCH_PARENT="$WORKSPACE_ROOT/.tmp";
SCRATCH_ROOT="$SCRATCH_PARENT/rocketclaw";
if [ -L "$SCRATCH_PARENT" ] || { [ -e "$SCRATCH_PARENT" ] && [ ! -d "$SCRATCH_PARENT" ]; }; then echo "unsafe workspace scratch parent: $SCRATCH_PARENT" >&2; exit 1; fi;
install -d -m 700 "$SCRATCH_PARENT" || exit 1;
if [ -L "$SCRATCH_PARENT" ] || [ ! -O "$SCRATCH_PARENT" ]; then echo "workspace scratch parent is not owned by the current user: $SCRATCH_PARENT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_PARENT" || exit 1;
if [ -L "$SCRATCH_ROOT" ] || { [ -e "$SCRATCH_ROOT" ] && [ ! -d "$SCRATCH_ROOT" ]; }; then echo "unsafe RocketClaw scratch root: $SCRATCH_ROOT" >&2; exit 1; fi;
install -d -m 700 "$SCRATCH_ROOT" || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "RocketClaw scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_DIR="$SCRATCH_ROOT/ce-explain/$(date +%Y%m%d)-$(openssl rand -hex 3)";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
printf '%s\n' "$RUN_DIR";
```

**Repo-touching inputs** (a concept with footprint in this repo, a diff, a recap): use the project's active instructions already in context and go directly to the diff, call-sites, current source, or Jujutsu history. Read `CONCEPTS.md` when canonical vocabulary matters. If the topic cannot be scoped from the input and existing context, allow one targeted root or workspace probe.

- **Diff mode:** resolve the Jujutsu revision or revset (the `diff:` value, or the most recent substantial change when the request points at one implicitly) and gather its evidence with `jj diff`, `jj show`, and `jj log` — the diff itself, the files it touches, and any plan or solution doc that motivated it. For a PR, preserve the hosting provider as the source of PR metadata through any available interface, map its base and head to Jujutsu commit IDs or remote bookmarks, and inspect configured remotes with `jj git remote list`; use `jj git fetch --remote <remote>` only when required evidence is absent locally and network access is in scope. Gather silently: nothing learned here is narrated to the user until Phase 3's ordering rule is satisfied.
- **Recap mode:** dispatch a generic subagent directly, seeded with `references/agents/work-recap-scout.md`, passing the resolved window, the Jujutsu workspace root, and `$RUN_DIR`. Do not pre-scan, count, or characterize the window in the main conversation; the scout owns that evidence pass, and an early broad history summary can seed it with a false bookmark or activity picture. It returns an evidence summary with Jujutsu change/commit IDs and `file:line` pointers. **Empty window** (no Jujutsu activity, no doc changes): say so, offer to widen the window, write no artifact, and end the run after the user responds.
- **External concepts** (no footprint in this repo): skip repo grounding entirely — do not force repo context into the output. Research with whatever web tools are reachable. When none are, you may explain from existing knowledge, but the artifact must label that content **Unverified — not checked against current sources** in its metadata header.
- **Idea mode:** the idea is a fixed given. Explain its implications, mechanics, and trade-offs for the user's understanding. Never scope it (`ce-brainstorm`'s job), never generate and rank alternatives (`ce-ideate`'s job).

### Phase 3: Check-in gate — before anything is revealed

Judge whether the material warrants a check-in (a routine recap does not; a gnarly diff or a hard concept does), then offer it with the blocking question tool. Put **Just the explainer (Recommended)** first and **Quiz me** second; the common path is the report, not the exercise loop. Record the user's exact Phase 3 choice as **Just the explainer** or **Quiz me** — do not collapse both choices into an "accepted" boolean. Only **Quiz me** enables the prediction and exercise mechanics. **Just the explainer** skips both while still composing and presenting the report. If the warrant test skips the offer, proceed without either mechanic. The user can always decline, and declining is never re-litigated. Read `references/check-in.md` for the warrant test, the prediction protocol, and exercise design.

**Diff mode with Quiz me selected — hard ordering rule.** No interpretive content — explanation, annotation, diagram, or surfaced opportunity — may be shown before the user's prediction turn ends. Show only the raw change reference (the diff or its stat summary), ask for the prediction ("What do you think this change does, and why was it made?"), and **end the turn there**. When no blocking tool exists, ask in chat and stop — never print the reveal in the same message as the prediction prompt. Compose the explainer only after the prediction lands; the reveal names the gaps between the prediction and what the change actually does.

### Phase 4: Compose the explainer

Read the rendering reference for the resolved format **now**, not earlier: `references/explainer-html.md` (default) or `references/explainer-markdown.md` (when intake resolved `output:md`). Compose per its contract — visible metadata header, show-n-tell form matched to the material, ~70ch measure, single self-contained file — and write the artifact to `$RUN_DIR/explainer.html` (or `$RUN_DIR/explainer.md` when intake resolved `output:md`) before anything else happens with it. Display it to the user (inline summary plus the file path; open locally per Phase 6 when chosen). The artifact exists at that stable path from this moment — a declined destination ask never loses it.

### Phase 5: Exercises (only when Quiz me was selected)

Run this phase only when the recorded exact Phase 3 choice was **Quiz me**. For concepts, ideas, and dense recaps, pose the exercises from `references/check-in.md` in chat, one at a time, using the blocking question tool where its option shape fits and free chat where the answer is narrative. Check each answer, correct it, and name the gap it exposed. Do not put exercises inside the artifact. When the choice was **Just the explainer**, skip this phase and continue to the destination ask.

### Phase 6: Destination ask and close

Detect destinations by capability — probe the available toolset and session context, never a closed list, and never treat a missing binary, environment variable, or unloaded connector as proof a destination is unavailable when another interface could supply it. Local file and Leave it are ungated and always offered. For default HTML runs, offer one preferred publisher: an artifact surface when an artifact-publishing capability is present; otherwise ht-ml.app. Do not show both by default, but honor an explicit user request for either. Publishing always requires the user's destination choice; ht-ml.app is public and must never be selected headlessly. Offer only what is detected; absence hides an option silently. Ask once with the blocking question capability, counting visible options against its supported limit first; when the visible set exceeds the limit, render a numbered list in chat with "Pick a number or describe what you want." and wait instead. Per-option routing:

- **Artifact surface** (HTML only; preferred when an artifact-publishing capability is present) — publish from the canonical explainer per `references/destinations.md`, following the detected capability's current contract.
- **Publish publicly to ht-ml.app** (HTML only; preferred when an artifact surface is not the selected adapter) — label it Recommended and state in the option description that the page is public and may be indexed, crawled, copied, or archived. When an explicit publish request bypasses the menu, state that full warning in chat and obtain explicit confirmation after the warning before the call; the pre-warning request does not count as confirmation. If confirmation cannot be obtained, do not publish; preserve the canonical HTML and report its local `$RUN_DIR/explainer.html` path. On a warned menu selection or post-warning confirmation, read and follow the ht-ml.app sub-flow in `references/destinations.md`, passing the complete canonical HTML to the resolved publisher. Do not assume a particular skill exists or add a ce-explain-specific publisher.
- **Local file** — copy the artifact out of `$RUN_DIR` to the path the user names, then where the platform exposes a browser-opening primitive (`open` on macOS, `xdg-open` on Linux, `start` on Windows) offer to open it; otherwise print the absolute path.
- **Publish to Proof** (markdown output only) — publish per `references/destinations.md` and surface the returned share URL; on failure retry once, then report and move on.
- **Send to Thinkroom** (offered only when a Thinkroom skill or CLI capability is detected) — send per `references/destinations.md`.
- **Leave it** — report the `$RUN_DIR` path and state that it is workspace-local scratch; nothing else is written.

**Non-interactive degradation:** when no interaction is possible at this ask (no blocking tool and no reply), do not hang and do not discard — the artifact is already at `$RUN_DIR`; report that path and end, skipping the improvement-observation handoffs below (they are offers, and an offer cannot fire without a user).

**Improvement observations.** When composing the explainer surfaced things that could be better, route them by type after the destination ask — offer, don't auto-fire:

**User-runnable invocation rendering.** Only the user-run handoff below uses printed invocation syntax. Render the `ce-polish` route using the active runtime's documented local invocation syntax; local syntax wins, and no prefix or command form is fixed here. Render only the invocation as inline code and output one form only.

- **New-capability ideas** — offer first; on acceptance invoke the `ce-ideate` skill via the platform's skill-invocation primitive, passing the observations as seed context. Do not merely tell the user to run it.
- **Code-clarity findings** — offer first; on acceptance invoke the `ce-simplify-code` skill via the platform's skill-invocation primitive, passing the observations and the files they concern. Do not merely tell the user to run it.
- **UI/UX polish opportunities** — present the observations in chat and tell the user to invoke `ce-polish` themselves using the rendering rule above; `ce-polish` is user-invoked only, so never attempt to invoke it via the skill primitive. The in-session observations carry into their run.

## Boundaries

- **Not a verdict.** "Should we adopt X?" is `ce-pov`. ce-explain teaches what X is and how it works.
- **Not repo memory.** Documenting a solved problem for future work is `ce-compound`. ce-explain teaches the human, not the repo.
- **Not ideation or scoping.** An idea input is explained as given — implications and trade-offs — never expanded into options or a requirements dialogue.
- **The check-in is never headless.** It exists to exercise the human; automating the answers deletes the product.

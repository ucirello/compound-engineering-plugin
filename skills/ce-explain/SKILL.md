---
name: ce-explain
description: "Create a durable visual teaching artifact for something worth learning. Use when the user wants to be taught, wants a deep explainer, wants to understand a substantial change, or wants a work recap built for retention. Not for ordinary Q&A, operational diagnosis, or a concise trade-off that belongs in chat. For learning, not repo docs or verdicts."
argument-hint: "[a concept, a jj revset, an idea, or 'what happened this week?'] — or invoke bare to be asked"
---

# Explain It To Me

Teach the user one thing well: a concept, a change, an idea, or a window of their own recent work. Agent-driven development removed the learning that writing code by hand used to provide; this skill is the replacement. What to explain is the input this skill was invoked with, present in the current prompt or conversation, whether the user asked directly or a calling skill passed it.

**Done:** a durable artifact exists at `$RUN_DIR`, the user has seen it, the destination they chose has been honored (or declined), and any check-in they accepted has been run and corrected. A run that correctly ends without an artifact — the operational-question gate answered it in chat, an empty window, or a bare invocation the user did not answer — is equally done.

**Note: The current year is 2026.** Use this when weighting external sources and dating artifacts.

## Setup

Run this once at the start of this invocation, before any subagent dispatch, and follow the directives it prints, except where one conflicts with this skill's own question rules. Run the fence exactly as written, as its own command: do not pipe, filter, truncate, or bundle its output. Its output opens with a `=== skill context` header and ends with `SKILL_CONTEXT_END`; if only one appears, rerun the fence verbatim once. Otherwise do not rerun it in this invocation. If no Node runtime is available, proceed unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
"$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
echo "no Node runtime; continue with the skill's normal behavior";
fi
```

**Read `references/orchestration.md` before the first blocking question, subagent dispatch, or run-directory creation** — it owns the per-harness ask tool, model tiers and their degradation rule, grounding by input shape, and menu sizing.

## Artifact Root

An explainer lands under `<root>/explainers/` only when archived to the workspace, and learnings may be read under `<root>/solutions/`. Resolve `<root>` only when you compose such a path; a workspace-scratch-only or external-concept run never composes one. Pass the resolved path to any subagent, not the config.

<!-- rocketclaw-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- rocketclaw-docs-root:end -->

## Execution Flow

### Phase 1: Classify the input

Read `references/intake.md` now and classify the request into one of the four input shapes — concept, diff, idea, or work-recap window — plus its audience. It owns the token table, reads-as-a-flag guard, window and audience resolution, concept-vs-diff tiebreak, conflict handling, and operational-question gate that answers a diagnostic question in chat instead of teaching it. Most requests arrive as plain language with no token; classify those by meaning rather than improvising.

**Bare invocation** (no input at all): ask one blocking question, "What should I explain?", offering a shortcut option for a recap of recent work in this workspace alongside free-text. Do not produce a default artifact unprompted.

### Phase 2: Ground

Create the run directory first: every artifact-producing run gets one before any artifact exists. It holds the explainer and recap evidence, so run this block as written rather than improvising a `mkdir`; the checks refuse a scratch root you do not own or one reached through a symlink.

```bash
if WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)"; then SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp"; else SCRATCH_ROOT=".tmp"; fi;
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_DIR="$SCRATCH_ROOT/ce-explain/$(date +%Y%m%d)-$(openssl rand -hex 3)";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR";
```

Then match grounding to the input shape per `references/orchestration.md`, which also owns the empty-window and unreachable-web paths. Two rules govern what reaches the user while gathering:

- **Diff mode.** Gather silently: nothing learned here is narrated until Phase 3's ordering rule is satisfied. If the revset resolves to no revisions, do not silently explain something else. Say what it resolved to, name the nearest real candidate (the working-copy change or previous revision), and use it only after the user agrees; when they cannot be asked, use it and state the substitution in the artifact's `Subject`. Apply the same rule when the named subject does not exist in this workspace.
- **Recap mode.** Do not pre-scan, count, or characterize the window in the main conversation: an early all-revisions summary can seed the run with a false line-of-work or activity model. Dispatch a generic subagent at the extraction tier, seeded with `references/agents/work-recap-scout.md` and passed the resolved window, workspace root, and `$RUN_DIR`. If the window contains no Jujutsu activity or doc changes, say so, offer to widen it, write no artifact, and end after the user responds. When no subagent primitive exists, apply the degradation rule: run the scout inline against its prompt's sources and budgets, still write `recap-evidence.md`, and form no view of the window until that evidence pass is done.

### Phase 3: Check-in gate — before anything is revealed

Read `references/check-in.md` now for the warrant test, offer wording, prediction protocol, and exercise design. Judge whether the material warrants a check-in, then offer it with the blocking question tool. **In diff mode, word the offer without describing the change's content or purpose**. Record the exact choice as **Just the explainer** or **Quiz me**. Only **Quiz me** enables prediction and exercises. If the warrant test skips the offer, proceed without either mechanic; declining is never re-litigated.

**Diff mode with Quiz me selected — hard ordering rule.** Show no interpretive content before the user's prediction turn ends. Show only the raw change reference (the diff or stat summary), ask what they think the change does and why it was made, and end the turn. When no blocking tool exists, ask in chat and stop. Compose only after the prediction lands; the reveal names gaps between the prediction and evidence.

### Phase 4: Compose the explainer

Read the rendering reference for the resolved format now, not earlier: `references/explainer-html.md` by default or `references/explainer-markdown.md` for `output:md`. Each owns artifact invariants and voice for the resolved audience. Write `$RUN_DIR/explainer.html` (or `explainer.md`) before anything else happens with it, then display an inline summary and path. A declined destination ask never loses it.

### Phase 5: Exercises (only when Quiz me was selected)

Run this phase only for the exact **Quiz me** choice. Pose the exercises from `references/check-in.md` in chat one at a time, use the blocking question tool where its option shape fits, check each answer, correct it, and name the gap. Do not put exercises inside the artifact. **Just the explainer** skips this phase.

### Phase 6: Destination ask and close

**Read `references/destinations.md` before rendering anything in this phase.** It owns the destination menu, per-option routing, each destination's sub-flow, the audience re-render offer and its ordering against publisher consent, and the closing improvement observations.

Ask for the destination once with the blocking question tool; that governs the menu, not any separate consent a chosen destination requires. Publishing is never headless or inferred. If the required sequence cannot complete, do not publish; preserve the canonical artifact and report its `$RUN_DIR` path. Offers fire only after acceptance, through the skill primitive, except `ce-polish`, which is user-run only.

**Non-interactive degradation:** when no interaction is possible at this ask, do not hang or discard the artifact. Report its `$RUN_DIR` path and end, skipping the reference's offers.

## Boundaries

- **Not a verdict.** "Should we adopt X?" is `ce-pov`. `ce-explain` teaches what X is and how it works.
- **Not repo memory.** Documenting a solved problem for future work is `ce-compound`. `ce-explain` teaches the human, not the repo.
- **Not ideation or scoping.** An idea input is explained as given — implications and trade-offs — never expanded into options or a requirements dialogue.
- **The check-in is never headless.** It exists to exercise the human; automating the answers deletes the product.

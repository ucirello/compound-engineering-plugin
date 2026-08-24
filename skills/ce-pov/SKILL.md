---
name: ce-pov
description: "Give a decisive, project-grounded point of view: a graded verdict on an external-adoption question, a holistic take on a document, or a position on a supplied approach set. Use for a solo POV. Use when asked to consult other models, reconcile their opinions, or `oracle`. Not for findings review (use ce-doc-review), neutral explainers, or generating options (use ce-ideate or ce-brainstorm)."
argument-hint: "[question, document, or approaches] [cross-check] — or bare"
---

# Form a Point of View

Produce a decisive, project-grounded point of view in the subject's own shape: a **graded verdict** on an external-adoption question, a **holistic take** on a document, or a **position** on a supplied approach set. The subject is whatever this skill was invoked with, in the prompt or the conversation. Stay read-only while forming and reconciling the POV. You are done when the POV is delivered with its required evidence and disclosure, or when an explicit blocker is returned. **The year is 2026**, for source recency.


## The moat

**Never issue a POV you did not earn against the project's own context.** Every subject must clear the **project floor** in `references/method.md`. An external-adoption verdict must also clear the full external floor. A document or approach-set POV must externally verify any external claim that is load-bearing to its bottom line. Nothing the conversation asserts substitutes for grounding.

## User-facing communication

Write for the person deciding what to do. Lead with the decision, question, or recommendation. Keep internal workflow vocabulary and mechanics out of chat unless asked, and put any consequence they need into ordinary language. Call the codebase "this project" or "the repository" unless the user supplied a recognizable name. Never promote a directory, workspace, working-copy change, bookmark, or path into the project name.

## Interaction Method

Ask through the host's blocking question tool, one question at a time: `AskUserQuestion` (Claude Code; run `ToolSearch` with `select:AskUserQuestion` if its schema is not loaded), `request_user_input` (Codex), `ask_question` (`agy`), `ask_user` (Pi). Fall back to numbered chat options only when none exists or the call errors. Never skip the question.

## Runtime Conventions

Use Jujutsu for every local version-control operation. Resolve the current workspace with `jj workspace root`; treat `@` as the working-copy commit; inspect state with `jj status`, content changes with `jj diff` (`--from`/`--to` for explicit comparison endpoints), revision history with `jj log` and revsets, line origins with `jj file annotate`, remotes with `jj git remote list`, branch-like pointers as bookmarks, and additional working copies as `jj workspace` workspaces. Jujutsu has no active bookmark, so never infer a current branch; inspect bookmarks and remote bookmarks explicitly. Prefer stable change IDs across rewrites and commit IDs only when the exact immutable revision matters. Use `jj describe` to edit an existing change description; use `jj commit` only when the intended operation is to describe the working-copy change and create a new change on top. Preserve GitHub, `gh`, and other provider-specific references; for `gh` in a non-colocated Jujutsu repository, set `GIT_DIR` from `jj git root`.

At every site in this skill and its references that composes, edits, validates, recommends, or emits a user-facing message, persisted decision, or Jujutsu change description, apply this exact sentence: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is not an operational instruction: inspect the project's active instructions and current `jj log` history; their runtime tone, vocabulary, and syntax take precedence. Preserve required decisions, paths, interaction semantics, and operational provider, model, or harness facts while adapting prose dynamically. Fixed stems, examples, and invocation tokens define required substance rather than mandatory message syntax. Do not impose a fixed prefix, heading, subject, body, layout, template, or example. Do not add product branding, generated-by text, or creator, model, provider, tool, agent, harness, runtime, workflow, or co-author attribution; operational references are facts, not attribution.

## Artifact Root

Resolve `<root>` the first time you compose a `<root>/` path; a read of `<root>/solutions/` counts as composing one. Pass the resolved path to scouts, never the config. A project outside a Jujutsu workspace has no `<root>`, so its prior-decision scan uses local ADRs and design docs instead.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

### Phase 0: Frame and Classify

**Read `references/intake.md` now, before any grounding.** It owns the output mode, the warm-invocation contract, orientation and framing, sizing, and the unbounded-field escape hatch. Settle the subject and the POV intent there (adopt / migrate / compare / is-this-our-problem / Document-take / Approach-set / explainer); an intent that routes out finishes at intake, and one that continues settles a reversibility tier. Read `references/boundaries.md` when this skill's fit is in doubt.

### Phase 1: Ground

**Read `references/grounding.md` now, before grounding by either path.** It owns the model tiers (the POV reasoning itself is never dispatched), the scratch fence, the scout payload and fleet, capability gating, and the provenance buckets that keep grounded facts apart from unconfirmed ones.

Send scouts directly to candidate-specific current evidence, never a generic repo profile. They search in their own context and return a dossier path plus a gist, which you read on demand. Where the load-bearing facts are already located, confirm them with bounded reads of the authoritative source instead of dispatching scouts; unscoped or noisy grounding still dispatches. A claim made in the conversation is a pointer to check, never self-verifying. The prior-decision scan (`<root>/solutions/`, ADRs, design docs) stays mandatory on either path.

### Phase 2: Verify Grounding

**Read `references/method.md` now**, before reasoning about the POV. It owns the Verify and POV steps, the skeptic stance, tiering, and the gate. Apply that gate over the grounded evidence. A failed floor forbids a confident result in any subject shape; that reference names the failure result each shape returns instead.

### Phase 3: Point of View

First form ce-pov's own independent POV under the active subject-shape contract in `references/method.md`, but do not emit it. Freeze that position. Keep it out of an independent peer's initial context; expose it only when the task is to critique that position, or in a later reconciliation round.

A summons is an affirmative request to consult or reconcile peers — a panel, a cross-check, `oracle` — anywhere in the invocation context. Declining one, or merely recounting one, is not a summons. On a summons, or when a cold POV may qualify for a proactive offer, read `references/cross-model-panel.md` before resolving participation or deciding whether to offer. Finish the panel branch before composing the result. A POV that follows a summons states which peers ran, or that none did and why. A POV with no summons carries no panel note.

Only then emit the subject shape's contract, as a **compact chat block, not a research report**. Lead with the grade, bottom line, or position, and never reprint dossiers or raw output.

### Phase 4: Follow-up

The chat POV is the deliverable; implementation is not. **Read `references/followup.md`** for the four-part handoff gate, the routing, and the continuations. Hand the POV on without another question only when that gate passes. Otherwise offer one continuation and wait. Reason that offer from the active subject shape's result — external adoption, Document take, or Approach-set position — never from a fixed menu, and never assume everything routes to a plan. Block only where that reference says the user must choose.

**Warm invocations stay a guest:** output the POV block, hand control back, and offer none of this unless asked.

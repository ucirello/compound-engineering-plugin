---
name: ce-strategy
description: "Create or update STRATEGY.md. Use when starting a product, adding a strategy doc to an existing workspace, changing direction or roadmap, or when ce-ideate, ce-brainstorm, or ce-plan need upstream product grounding."
argument-hint: "[optional: section to revisit, e.g. 'metrics' or 'approach']"
---

# Product Strategy

**The current year is 2026** - use it when dating the document.

`ce-strategy` writes and maintains its part of `STRATEGY.md` at the Jujutsu workspace root. Outside a Jujutsu workspace, use the physical current project directory. The document captures what the project is, who it serves, how it succeeds, and where the team is investing. It is shared with other tools and people; this skill owns only the sections `references/strategy-template.md` names. Downstream skills read it when it exists: `ce-ideate`, `ce-brainstorm`, and `ce-plan` for what work is on-strategy; `ce-product-pulse` for the product name and key metrics; `ce-dogfood` for the primary persona. Its frontmatter keys and this skill's section headings are the contract those skills parse - keep them for every section this skill authors; a meaning an existing section already carries is merged into it (`references/update-run.md`).

**Done:** `STRATEGY.md` exists at the resolved workspace root and the user has seen what will be written and had an edit pass. For a file in this skill's house format, every required section is filled from answers that survived pushback (or explicitly deferred to a linked legacy doc) and the file matches `references/strategy-template.md`. For a file in any other shape, done is the user-approved minimal edits applied, with the document's shape unchanged. A section the user could not sharpen in two rounds is written as given and named in chat as worth revisiting - a completed run, not a blocked one.

## Runtime conventions

Resolve `<workspace-root>` with `jj workspace root`. If that command fails because the current project is not a Jujutsu workspace, use the physical current project directory as a local-only fallback. Root `STRATEGY.md`, `README.md`, `CONCEPTS.md`, and sibling product documents there. Resolve the durable artifact root `<root>` from `<workspace-root>/.rocketclaw/config.yaml` as `references/grounding.md` specifies. If temporary or intermediate storage becomes necessary, use `<workspace-root>/.tmp/rocketclaw/ce-strategy/`; outside Jujutsu, use the physical current project directory's `.tmp/rocketclaw/ce-strategy/`. Never use OS-global or user-global temporary storage.

Use Jujutsu for local version-control operations: `jj status` for working-copy state, `jj diff` for content changes, `jj log` with explicit revsets for history, `jj file annotate` for line origins, bookmarks for named publication pointers, and `jj workspace` for additional working copies. Treat `@` as the working-copy change and do not infer an active bookmark. Use `jj git` for Git remote interoperability. Preserve forge and provider operations, including GitHub operations through `gh`; resolve remotes with `jj git remote list`, and in a non-colocated workspace point Git-dependent tools at the path from `jj git root`. Keep mutating repository operations in JJ even when a colocated `.git` directory or Git Bash makes Git commands available.

Whenever this skill composes, edits, validates, or recommends a commit message or Jujutsu change description, apply this requirement exactly once at that site. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and syntax observed at runtime win. Apply compatible Go guidance only to message quality, clarity, and structure. Preserve the required semantics with neutral placeholders until runtime resolves them; do not impose a fixed prefix, type, scope, subject, body, layout, message, template, or example.

## Boundaries

- **Anchor, not plan.** Strategy is what the product is and why. Features belong in `ce-brainstorm`, schedules and prioritization in the issue tracker, implementation plans in `ce-plan`; do not let them creep into the doc, and do not update the tracker or reconcile in-flight work.
- **The user answers; the workspace only grounds the question.** Evidence earns a sharper question, never fills in a section. Do not derive the strategy from the workspace.
- **Short is a feature.** Push back on expansion rather than adding sections.
- **Record which metrics matter and where they live**, not what they read today.
- **Keep output neutral.** Do not add product or workflow branding, visual badges, bylines, generated-by text, or creator, model, provider, tool, agent, harness, runtime, workflow, co-author, sign-off, or similar attribution. Preserve human and research-source attribution already present in user-owned content.
- **Meaning is the contract; the document's existing shape decides its format.** A file that has only this skill's shape - `references/update-run.md` states the test - is maintained in house format on every write: headings renamed, sections in the template's current order, missing required sections offered. A file in any other shape is read by meaning and edited in its own shape and idiom: no restructuring into the template, no uninvited frontmatter or headings. Either way, a section whose inline metadata records approval or forbids edits, or a doc the user does not own, is not edited at all - report the conflict, or write a separate file that links to it. A targeted update preserves every other section's content exactly, with placement following the shape test: a house-format-only file takes the template's order; a multi-writer file is never reordered. `references/update-run.md` owns the rest and is a required read before you edit an existing file.

## Asking and routing

Ask one question at a time through the host's blocking question tool already in the current tool list. Match by capability; never probe a user-facing tool to discover it. Fall back to numbered options on the visible chat surface only when no such tool is listed or a real question call errors. Never silently skip the question.

Any argument this skill was invoked with — present in the current prompt or conversation, from the user or a calling skill — is a focus hint: a section to revisit (`metrics`, `positioning`, `tracks`; older names such as `approach` or `who it's for` map to the current section) or a scope hint. With none, proceed open-ended and let the file state decide the path.

## Phase 0: Ground and route

Phase 0 produces a workspace model and a route, whatever the harness reads. `references/grounding.md` is a non-optional load: it carries the full source list, repository-evidence semantics, and the wording of the disagreement question and focus hint.

**The workspace model** is your working understanding of what this product is. Read `<workspace-root>/STRATEGY.md` if it exists. Take what the product is from its stated intent and structure - `README.md`, `CONCEPTS.md`, durable artifacts under `<root>`, sibling docs such as `PRODUCT.md`, and what the code is organized around - and bound that read to "what is this and who is it for" rather than profiling the whole workspace. Take what is getting attention now from recent Jujutsu changes or provider review records such as GitHub PRs, using `references/grounding.md` to preserve history and interop semantics. Attention informs only the Tracks question and staleness in an update run; where it disagrees with stated intent, that is a question for the user, never a conclusion. Show the model in chat before the first question: three to five lines on what you take the product to be, who it seems to serve, and where attention has gone, each with its source named, and invite correction. If the model did not supply the product's name, ask for it here - the template's frontmatter and title need it. A workspace with no substantive content is a normal path: say so in one line and run the interview ungrounded.

**The route** is announced in one line by file state: no file -> Phase 1, after the legacy-sibling offer in `references/grounding.md` when one applies; file exists -> Phase 2. State whether the strategy document was found and whether this run will create or update it without requiring fixed announcement wording.

## Phase 1: First-run interview

Read `references/interview.md` before the first question - a non-optional load. The opening questions, pushback rules, anti-pattern examples, quality bar, blocking-question tool per host, and the two-round cap live there; improvising from memory produces a passive transcription instead of a strategy doc.

Run the interview in this order (the document itself follows the template's order; Boundaries is asked after the stress test, where its content comes from):

1. Purpose
2. Positioning
3. Users
4. Key metrics
5. Tracks
6. Stress test
7. Boundaries (always written)
8. Milestones (optional)
9. Brand (optional)

When every section is captured, read `references/strategy-template.md`, fill it in, present the full draft in chat, offer one round of edits, then write `<workspace-root>/STRATEGY.md`.

## Phase 2: Update run

Read `references/update-run.md` first - a non-optional load, before the summary, the drift check, or any question. It decides how drift candidates are raised, which section is revisited, and what is preserved untouched. An update run summarizes the file's current state in 3-5 lines, and names any section the workspace model suggests is stale as a candidate rather than a verdict. It then revisits the section the focus hint named, or the one the user picks when asked. The user may pick any section; list the drift candidates first, as suggestions rather than as the only choices. Every other section's content is left untouched, and its place follows the shape test in `references/update-run.md`. Questions and pushback still come from `references/interview.md`, applied as if this were a first run.

## Phase 3: Downstream handoff

Note in one line where the file lives and that `ce-ideate`, `ce-brainstorm`, and `ce-plan` pick it up as grounding on their next run. If no downstream skill has run here yet, suggest `ce-ideate` or `ce-brainstorm` as a next step.

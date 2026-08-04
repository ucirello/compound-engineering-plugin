---
name: ce-compound-refresh
description: Refresh the repo's captured learnings against the current codebase. Use when auditing stale, overlapping, superseded, or drifted learnings; avoid general refactor, debugging, or code review unless the learnings store is explicit.
argument-hint: "[optional: scope hint — directory, filename, module, or keyword] [mode:non-interactive] "
---

# Compound Refresh

Audit the learnings under `<root>/solutions/` against the current codebase, apply the maintenance actions the evidence supports, and deliver a complete per-doc report plus a described JJ change. The report and the corrected document set are the deliverables; the store only compounds value if every doc in it can be trusted.

## Mode

If the arguments contain `mode:non-interactive` (or its deprecated alias `mode:headless`), strip those tokens (the remainder is a scope hint) and run **non-interactive**; otherwise run **interactive**.

**Interactive:** apply unambiguous actions directly; ask the user only on genuine judgment calls (see Decide).

**Non-interactive:** never pause for input, in any phase.

- Apply all safe actions: Keep, Update, Consolidate, auto-Delete (gate below), Replace (when evidence is sufficient). If a write succeeds, record it as **applied**; if it fails (e.g., permission denied), record it as **recommended** and continue — never stop to ask for permissions.
- When classification is genuinely ambiguous or Replace evidence is insufficient, mark the doc stale instead: add `status: stale`, `stale_reason: [what you found]`, `stale_date: YYYY-MM-DD` to its frontmatter. Err toward stale-marking over incorrect action. If even that write fails, record it as recommended.
- Relocations auto-apply only under the four-condition gate (see Classify); otherwise recommend. Splits are always recommend-only: fragment boundaries are a retrieval-value judgment with no ground truth.
- With no scope hint, process everything — no scope-narrowing questions. With a scope hint that matches nothing, report the miss and exit; do not widen to all docs.
- The report (see Report) is the primary deliverable.

## Blocking questions

Wherever this skill asks the user something, use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to numbered options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question. Ask one question at a time, prefer multiple choice, lead with the recommended option and a one-sentence rationale.

## CONCEPTS.md bootstrap requests

If invoked specifically to create or bootstrap `CONCEPTS.md` ("create a CONCEPTS.md", "build the concept map"), the intent is ambiguous between two jobs — disambiguate with a blocking question:

1. **Create CONCEPTS.md (build the concept map)** — skip the `<root>/solutions/` classification work. Read `references/concepts-vocabulary.md` and follow its **Seed goal** and **Scope of a seed** (repo-wide) rules: seed the project's core domain nouns from the declared domain model, write the preamble (see Vocabulary Capture), cluster per the organization rules, run the Discoverability Check, then record it via the Record Changes flow — do not leave the bootstrap undescribed.
2. **Run a refresh cycle** — proceed normally; `CONCEPTS.md` is seeded (if absent) and reconciled during Vocabulary Capture.

In non-interactive mode, default to the refresh cycle and note in the report that a standalone repo-wide bootstrap was not run.

## Artifact Root

This skill reviews and refreshes learnings under `<root>/solutions/`. Resolve `<root>` when you first compose a `<root>/solutions/` path (per the block below); pass the resolved `<root>/solutions/` path to any subagent, not the config. Resolve the workspace root with `jj workspace root`; if that fails, report that the workflow requires a JJ workspace and stop rather than falling back to another VCS.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; first non-empty value wins (`<workspace-root>` = `jj workspace root`). Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Scope

Find all `.md` files under `<root>/solutions/`, excluding `README.md` files and anything under `_archived/` (if `_archived/` exists, flag it in the report as legacy to clean up). READMEs are excluded as review *candidates* only: whenever an action deletes, renames, moves, consolidates, or replaces a doc a catalog README lists, update that README's rows mechanically as part of the action's cleanup. Keep temporary refresh artifacts under `<workspace-root>/.tmp/rocketclaw/ce-compound-refresh/`; never use an OS-global temporary location.

If a scope argument was provided, narrow with the first strategy that produces results: subdirectory name → frontmatter (`module`/`component`/`tags`) → filename → content keyword. No matches: ask the user to clarify (interactive) or report the miss and exit (non-interactive).

If the store is empty, report the resolved empty path and route the user to `ce-compound` after solving a problem. Match the surrounding response style instead of copying fixed output syntax.

For a broad sweep (9+ docs), triage before deep investigation: read all frontmatter, cluster by module/category, spot-check whether primary referenced files still exist, and start with the highest-impact cluster (interactive: confirm the starting area with the user; non-interactive: process all clusters in impact order). Review individual learning docs before the pattern docs that depend on them — stale learnings make a pattern look more valid than it is. If the user named a pattern doc, you may start there, but inspect its supporting learnings before changing it.

## Investigate

For each learning in scope, read it and cross-reference its claims against the current codebase. Dimensions that go stale independently: referenced paths/classes/modules; the recommended solution itself (does it still match how the code works?); code snippets; cross-referenced docs; overlap with other in-scope docs (note pairs covering the same problem/files/solution and which appears broader or more current); and domain vocabulary (note project-specific terms and whether `CONCEPTS.md` defines them accurately — collect the signal, don't edit yet). If the harness injects an auto-memory block, also scan it for same-domain notes: memory-sourced signals are supplementary — they corroborate codebase evidence or prompt deeper investigation, never alone justify Replace or Delete, and in non-interactive mode memory-only drift means stale-mark. Match depth to specificity: a doc citing exact paths and snippets needs more verification than a general principle.

After individual docs, evaluate the set: overlaps, supersession (an older narrow doc a newer doc subsumes), and outright contradictions between docs — contradictions actively mislead and outrank individual staleness. Note category-shape problems (a directory whose docs span unrelated themes, a near-empty category) as report-only observations — never restructure directories or create categories.

**Subagents.** Use them for context isolation, choosing the lightest approach that fits: main thread for small scopes, parallel investigation subagents for 3+ independent docs, batches for broad sweeps; docs that overlap or share a root issue are investigated together, not parallelized. When spawning any subagent, omit the `mode` parameter so the user's permission settings apply, and include in its prompt:

> Use dedicated file search and read tools (Glob, Grep, Read) for all investigation. Do NOT use shell commands (ls, find, cat, grep, test, bash) for file operations. This avoids permission prompts and is more reliable.
>
> Also scan any auto-memory block injected into your context. Check for notes related to the learning's problem domain. Report memory-sourced drift signals separately from codebase-sourced evidence, tagged with "(auto memory)" in the evidence section. If the block is not present, skip this check.

Two subagent roles: **investigation** subagents are read-only and return evidence + a recommended action; **replacement** subagents write successor docs (one per Replace or Split candidate, run one at a time, sequentially). The orchestrator merges results, resolves contradictions, and performs all deletions and metadata edits centrally.

## Classify

Assign each doc one outcome:

| Outcome | Meaning | Action |
|---------|---------|--------|
| **Keep** | Still accurate and useful | No edit — report it as reviewed. Do not write a review breadcrumb or `last_refreshed` on its own. |
| **Update** | Solution still correct; references drifted (paths, names, links, snippets, metadata, misfiling) | Fix in place |
| **Consolidate** | Docs overlap heavily, both correct | Merge unique content into the canonical doc, delete the subsumed one |
| **Replace** | Guidance is now misleading; a trustworthy successor can be written | Successor via subagent, then delete the old |
| **Delete** | No longer useful, applicable, or distinct | Delete the file — JJ history is the archive; there is no `_archived/` |

Judgment rules that are easy to get wrong:

- **Match docs to reality, not the reverse.** When code and doc disagree, the doc is what changes. Never ask whether a code change was "intentional" or amounts to a regression — code review is out of scope.
- **The Update/Replace boundary:** if you find yourself rewriting the solution section or changing what the doc recommends, that is Replace, not Update. A contradiction between the doc's recommendation and current code is a strong Replace signal, not minor drift.
- **Age alone is not staleness** — a two-year-old doc that still matches the code is a Keep; use age only as a prompt to inspect harder.
- **No churn:** never edit just for typos, wording, or cosmetics.
- **Replace needs real evidence** — from the investigation itself, the conversation, newer docs/PRs, or the user. If you cannot confidently document the current approach, stale-mark and recommend `ce-compound` for the user's next encounter with that area instead of guessing.
- **Consolidate vs separate — the retrieval-value test:** would a maintainer searching this topic in six months benefit from separate docs (genuinely different sub-problems, different audiences), or do they just create drift risk? Two docs saying the same thing will eventually say different things. Two accurate docs about *different sub-problems* of one feature (e.g., request volume vs response ordering) stay separate even when they cite the same file — shared code is not shared problem. If the subsumed doc adds nothing unique, it's a straight Delete. Deleting the subsumed doc after merging its unique content is part of the Consolidate action itself — it is a safe, unattended-appliable step and does not require the auto-delete gate below.
- **Unverifiable is not false.** A claim the workspace cannot corroborate — a schema or index fact, an operational practice, an environment behavior — is not thereby wrong; repositories rarely witness their own operations. Never delete, strip during a merge, or stale-mark content solely because no workspace artifact confirms it. Act only on contradiction (code demonstrably does otherwise); for unverifiable-but-plausible claims, keep them and note the verification gap in the report. **Split** (one doc holding several independent problems → focused successors) is the inverse and the bar is high: each fragment must have independent retrieval value; length alone is never a reason.
- **Relocation** (an Update variant): move a doc only when directory and frontmatter category disagree or content unambiguously belongs in a different **existing** category. A mismatch proves something is wrong, not which side — resolve the direction from content before moving, and never relocate on an arguable judgment call. Non-interactive auto-relocation requires all four: (1) frontmatter and directory disagree per the category mapping, (2) content clearly resolves the direction as directory-wrong, (3) the target category directory exists, (4) all inbound citations are workspace-local and mechanically rewritable. Otherwise recommend.

**Before any Delete**, two checks:

1. **Is the problem domain still active?** Missing files prove the *implementation* is gone, not the problem. If the app still deals with what the doc addresses (e.g., the auth-token file is gone but sessions are still handled), that is Replace, not Delete. A doc that never referenced workspace code (developer environment, onboarding, process) can never satisfy "implementation gone" and **never auto-deletes** — stale-mark (non-interactive) or ask (interactive) when its currency is in doubt.
2. **Inbound links.** Search the workspace's markdown (not source code) for the filename slug; read context around matches. **Decorative** citations (see-also pointers, principle already stated inline) permit Delete with mechanical cleanup in the same change. **Substantive** citations (the citing doc relies on the cited content) signal Replace — or Keep with narrowed scope. Mixed or unclear: stale-mark.

**Auto-delete (no confirmation needed, either mode) only when all three hold:** the implementation once lived in this repo and is gone (or the doc is fully superseded or plainly redundant); the problem domain is gone — or, for a superseded/redundant doc, the surviving canonical doc itself already states the subsumed doc's guidance (topical overlap is not coverage: verify the specific content exists there before deleting); inbound citations are absent or unambiguously decorative. Any condition fails → Replace, Update, Consolidate, stale-mark, or ask.

**Pattern docs** (`<root>/solutions/patterns/`) get the same five outcomes evaluated as *derived* guidance: does the generalized rule still hold given the refreshed learnings beneath it? A pattern with no supporting learnings is itself a stale signal. Base any pattern Replace on the refreshed learning set, not fresh invention.

## Decide (interactive mode only)

Apply unambiguous Keeps, Updates, and Consolidations directly — no confirmation. Ask (per Blocking questions) only when: the action is genuinely ambiguous; a Delete fails the auto-delete gate; the canonical doc in a Consolidate isn't clear-cut; you are about to Replace; or you are about to Split (it writes successors and deletes the original — confirm fragment boundaries like a Replace). Present the file path, 2-4 evidence bullets, and the recommended action; offer only plausible alternatives plus "skip for now". For broad sweeps, work in batches and confirm continuation between them rather than front-loading a full maintenance queue.

## Execute

Read `references/per-action-flows.md` and follow the section matching each doc's classification — it owns the step-by-step criteria, the relocation and split procedures, the replacement subagent contract (pass `references/schema.yaml`, `references/yaml-schema.md`, and `assets/resolution-template.md`; validate with the bundled frontmatter and doc-claims scripts), and citation cleanup. One flow per doc.

## Vocabulary Capture

After the per-doc actions execute, reconcile the domain terms flagged during investigation with `CONCEPTS.md`.

**First, read `references/concepts-vocabulary.md` — unconditionally.** Its qualifying criteria are non-obvious; a "nothing qualifies" judgment without reading it is a shortcut, not a result.

1. **Aggregate** qualifying terms across the learnings in scope; when one term surfaced with different shades of precision, union the shades into one entry.
2. **If `CONCEPTS.md` exists:** add missing terms, refine entries where the corpus surfaced new precision, then reconcile the in-scope core nouns — re-derive the area's core domain nouns per the reference's **Seed goal** and backfill any central-but-missing ones. Bounded to the area in scope; never a repo-wide sweep.
3. **If it doesn't exist** and at least one term qualified: bootstrap it — seed the in-scope area's core domain nouns per the Seed goal alongside the surfaced terms, holding the bar conservatively for borderline terms at creation. Start the file with a style-matched heading and preamble:

   Derive a concise, style-matched preamble carrying these semantics: shared project-specific domain vocabulary; seeded core terms; growth through `ce-compound`, `ce-compound-refresh`, and direct edits; glossary rather than specification or catch-all. Let the term set and repository style determine whether headings stay flat or cluster by domain relationship; do not impose a fixed count threshold or wording.
4. **Scrub violations** in existing entries per the reference's criteria (implementation specifics, config values that drift, status/owner/date metadata, duplicates, undefined project-specific siblings). The full sweep is appropriate here because refresh is an audit.
5. Do not expand beyond the area in scope (the explicit repo-wide bootstrap path is the exception), and do not retroactively inject `(see CONCEPTS.md)` pointers into learnings.

If nothing qualified, record that explicitly in the report's `CONCEPTS.md` line (e.g., "scanned, no qualifying terms") — the visible scan record is the audit signal that the reference was consulted. Apply vocabulary edits silently in every mode — no user prompt.

## Report

**Print the full report as markdown — it is the deliverable, not an internal summary.** After processing the scope:

Produce a style-matched summary containing counts for scanned, kept, updated, consolidated, replaced, deleted, skipped, and stale learnings, plus the applicable `CONCEPTS.md` scan, creation, seeding, addition, refinement, reconciliation, scrub, or repo-wide-map outcome. Do not copy a fixed heading, table, placeholder, or layout.

Then, for EVERY file processed: path, classification, evidence found (tag memory-sourced findings "(auto memory)"), and the action taken or recommended; for Consolidate, which doc was canonical, what was merged, what was deleted. Group Keeps under a reviewed-without-edits section.

In non-interactive mode the report is the sole deliverable — self-contained, never abbreviated — and actions split into two sections. **Applied:** writes that succeeded, with the same per-file detail. **Recommended:** writes that failed (with enough context for a human to apply them), plus everything that never runs unattended — relocations that failed the four-condition gate (doc, target, failing condition), splits (doc, proposed fragment boundaries), category-shape observations, and the discoverability recommendation if any. If no writes succeed, the report is a maintenance plan. If `_archived/` exists, list its files and recommend disposition (restore, delete, or consolidate).

## Record Changes

Skip if no files changed. Inspect `@` and its parents with `jj log -r '@ | parents(@)'`, bookmarks on `@` with `jj bookmark list -r @`, all working-copy paths with `jj status`, available remotes with `jj git remote list`, remote bookmarks with `jj bookmark list --all-remotes`, and recent change descriptions with `jj log`. Resolve one writable publication remote from the project's active instructions and provider ownership; if multiple plausible remotes remain, ask rather than choosing one. When the selected provider is GitHub, resolve base and head ownership separately and inspect existing review state with `gh`.

Repository-local runtime instructions and JJ syntax discovered during execution override this generic flow. If the workspace is not a JJ repository, report that durable recording is unavailable and stop this phase; do not fall back to another VCS.

Include this exact sentence verbatim at every site that composes, recommends, or validates a change description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Active project instructions and change-description syntax inferred at runtime from `jj log` always win. Preserve every semantic content requirement stated by the site while adapting syntax to runtime conventions. Apply compatible Go quality, clarity, and structure generally, regardless of repository language. Do not impose any fixed prefix, type, scope, subject, body, layout, template, example, bookmark namespace, or command sequence.

Non-interactive defaults: when `@` contains only refresh paths, describe `@`, create or move a specific bookmark when publication is appropriate, publish it through the resolved JJ remote, and open or update the provider review request; use `gh` for GitHub. When `@` also contains unrelated paths, do not rewrite or split the user's change automatically; leave the refresh paths in place and report a JJ-native recommendation for isolating and describing them. If JJ, remote, or provider operations fail, report the intended semantic operation, relevant change ID/bookmark/remote, and failure without emitting a fixed command sequence. Every description recommendation at this site must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Active project instructions and change-description syntax inferred at runtime from `jj log` always win. Preserve the refresh outcome summary while adapting syntax to runtime conventions. Apply compatible Go quality, clarity, and structure generally, regardless of repository language. Do not impose any fixed prefix, type, scope, subject, body, layout, template, example, bookmark namespace, or command sequence.

Interactive: ask (per Blocking questions) with the recommended option first, using change IDs, bookmarks, workspaces, and revsets as the native identities. When `@` contains only refresh paths, recommend describing the current change and, when publication is wanted, placing a specific bookmark, publishing through the resolved JJ remote, and opening or updating the provider review request. When unrelated paths are also present, recommend leaving the working copy untouched unless the user explicitly chooses a repository-approved JJ operation to isolate the refresh paths. Always offer leaving the work undescribed. Every option that composes or recommends a description must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Active project instructions and change-description syntax inferred at runtime from `jj log` always win. Preserve the refresh outcome summary while adapting syntax to runtime conventions. Apply compatible Go quality, clarity, and structure generally, regardless of repository language. Do not impose any fixed prefix, type, scope, subject, body, layout, template, example, bookmark namespace, or command sequence.

Compose a succinct description that summarizes the refresh outcomes at the level used by the repository, validate it against runtime conventions, then describe the change. This composition and validation site must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Active project instructions and change-description syntax inferred at runtime from `jj log` always win. Preserve the refresh outcome summary while adapting syntax to runtime conventions. Apply compatible Go quality, clarity, and structure generally, regardless of repository language. Do not impose any fixed prefix, type, scope, subject, body, layout, template, example, bookmark namespace, or command sequence.

## Discoverability Check

After the report, check that the project's instruction files would lead an agent to discover `<root>/solutions/` before working in a documented area. Runs every time — the store only compounds value when agents can find it.

1. Use the project's active runtime instructions already in context to identify the substantive workspace-local instruction source. Ignore compatibility shims that only include another source. If no workspace-local instruction source exists, skip this check.
2. Assess semantically (not by string match) whether a reader would learn: the store exists, enough structure to search it (categories, frontmatter fields like `module`, `tags`, `problem_type`), and when it's relevant. If the spirit is met, done.
3. If not, draft the smallest addition that communicates those three things, matching the file's style — prefer one line in an existing related section (a directory listing, architecture tree, conventions block) over a new headed section. Keep the tone informational, not imperative ("relevant when implementing or debugging in documented areas", not "always search before implementing" — imperatives cause redundant reads when a workflow already searches). Substitute the resolved concrete root for `<root>` in what you write — readers without this plugin cannot resolve the placeholder. Calibration example for a directory listing:

   Calibrate rather than copy fixed syntax: add one style-matched entry describing the store, its categories, and searchable metadata.

4. Interactive: show the proposed change and where it goes, explain why it matters (fresh sessions and plugin-less collaborators won't find the store otherwise), and get consent via a blocking question before editing. Non-interactive: emit a "Discoverability recommendation" line in the report instead of editing instruction files — non-interactive scope is doc maintenance, not project config.
5. If `CONCEPTS.md` exists at the workspace root, run the same check for it, preserving the semantics that it contains shared domain vocabulary relevant to codebase orientation while deriving wording and syntax from the target file. Skip entirely when it doesn't exist — never nag for an artifact the project hasn't adopted.
6. If this check edits a runtime-instruction file before publication, keep it in the current refresh change and update that change's description. If publication already occurred, create a follow-up JJ change only when repository-local workflow requires one, describe it, advance the relevant bookmark, and publish it through the resolved remote so the review request includes the edit. If the user chose to leave the work undescribed, leave these edits in the working-copy change. Every composed, recommended, or validated description at this site must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Active project instructions and change-description syntax inferred at runtime from `jj log` always win. Preserve the discoverability-edit summary while adapting syntax to runtime conventions. Apply compatible Go quality, clarity, and structure generally, regardless of repository language. Do not impose any fixed prefix, type, scope, subject, body, layout, template, example, bookmark namespace, or command sequence.

## Relationship to ce-compound

`ce-compound` captures a newly solved, verified problem; this skill maintains the store as the codebase evolves — each doc's accuracy and the set's design. Replace only with real evidence; otherwise stale-mark and point the user at `ce-compound`. Consolidate proactively: every capture adds a doc, and redundant docs drift silently.
